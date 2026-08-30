import aiosqlite
from typing import Optional
from config import DATABASE_URL, COMPETITION_MIN_DRAFTS
from models import User


DB_PATH = DATABASE_URL


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                games_lost INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                best_score INTEGER DEFAULT 0,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("DROP TABLE IF EXISTS game_sessions")
        await db.execute("DROP TABLE IF EXISTS game_history")

        # season_wins now counts completed drafts (solo or pvp), not PvP wins —
        # there is no win/loss concept in the draft game.
        await db.execute("""
            CREATE TABLE IF NOT EXISTS draft_sessions (
                session_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'waiting',
                creator_id INTEGER NOT NULL,
                opponent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                finished_at TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS draft_participants (
                session_id TEXT NOT NULL,
                participant_id INTEGER NOT NULL,
                seat INTEGER NOT NULL,
                current_slot_index INTEGER NOT NULL DEFAULT 0,
                pending_player_id INTEGER,
                status TEXT NOT NULL DEFAULT 'drafting',
                team_rating INTEGER,
                PRIMARY KEY (session_id, participant_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS draft_shown_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                participant_id INTEGER NOT NULL,
                slot TEXT NOT NULL,
                draw_index INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                decision TEXT,
                shown_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, participant_id, slot, draw_index)
            )
        """)

        # Add new columns if they don't exist yet (safe for existing DBs)
        for col_def in [
            "ALTER TABLE users ADD COLUMN season_score INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN season_wins INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0",
        ]:
            try:
                await db.execute(col_def)
            except Exception:
                pass
        await db.commit()


# ─── Users ───────────────────────────────────────────────────────────────────

async def get_or_create_user(telegram_id: int, username: Optional[str], first_name: str) -> User:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return User(**dict(row))
        try:
            await db.execute(
                "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
                (telegram_id, username, first_name)
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            # Lost a race with a concurrent get_or_create_user for the same user
            # (e.g. /start and the Mini App's /api/auth firing at once) — row exists now.
            pass
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return User(**dict(row))


async def get_user(telegram_id: int) -> Optional[User]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return User(**dict(row)) if row else None


async def record_draft_completion(telegram_id: int, team_rating: int):
    """Called once per participant when their 5-slot roster is finished (solo or pvp)."""
    user = await get_user(telegram_id)
    if not user:
        return
    best_score = max(user.best_score, team_rating)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET
                games_played = games_played + 1,
                total_score = total_score + ?,
                season_score = season_score + ?,
                season_wins = season_wins + 1,
                best_score = ?
            WHERE telegram_id = ?
        """, (team_rating, team_rating, best_score, telegram_id))
        await db.commit()


async def get_leaderboard(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT telegram_id, username, first_name, total_score, games_played, best_score
            FROM users
            ORDER BY total_score DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in await cursor.fetchall()]


async def apply_referral(new_user_id: int, referrer_id: int) -> bool:
    """
    Called once when a new user joins via ref link.
    Returns True if bonus was applied, False if referral already exists or self-referral.
    """
    if new_user_id == referrer_id:
        return False
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT referred_by FROM users WHERE telegram_id = ?", (new_user_id,)
        )
        row = await cursor.fetchone()
        if not row or row[0] is not None:
            return False
        await db.execute(
            "UPDATE users SET referred_by = ? WHERE telegram_id = ?",
            (referrer_id, new_user_id)
        )
        await db.execute("""
            UPDATE users SET
                total_score = total_score + 1500,
                season_score = season_score + 1500,
                referral_count = referral_count + 1
            WHERE telegram_id = ?
        """, (referrer_id,))
        await db.commit()
        return True


async def get_bot_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        total_users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        active_today = (await (await db.execute(
            "SELECT COUNT(DISTINCT participant_id) FROM draft_shown_players WHERE shown_at >= date('now')"
        )).fetchone())[0]
        active_week = (await (await db.execute(
            "SELECT COUNT(DISTINCT participant_id) FROM draft_shown_players WHERE shown_at >= date('now', '-7 days')"
        )).fetchone())[0]
        total_games = (await (await db.execute(
            "SELECT COUNT(*) FROM draft_participants WHERE status = 'done'"
        )).fetchone())[0]
        total_referrals = (await (await db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by IS NOT NULL"
        )).fetchone())[0]
        top = await (await db.execute(
            "SELECT first_name, username, season_score, season_wins FROM users ORDER BY season_score DESC LIMIT 3"
        )).fetchall()
        return {
            "total_users": total_users,
            "active_today": active_today,
            "active_week": active_week,
            "total_games": total_games,
            "total_referrals": total_referrals,
            "top3": [dict(r) for r in top],
        }


async def get_referral_stats(telegram_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT referral_count FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else {"referral_count": 0}


async def get_competition_leaderboard(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT telegram_id, username, first_name, season_score, season_wins
            FROM users
            WHERE season_wins >= ?
            ORDER BY season_score DESC
            LIMIT ?
        """, (COMPETITION_MIN_DRAFTS, limit))
        return [dict(row) for row in await cursor.fetchall()]


# ─── Draft sessions ────────────────────────────────────────────────────────────

async def create_draft_session(session_id: str, mode: str, creator_id: int,
                                status: str, expires_at: Optional[str] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO draft_sessions (session_id, mode, status, creator_id, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, mode, status, creator_id, expires_at))
        await db.commit()


async def get_draft_session(session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM draft_sessions WHERE session_id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def find_joinable_pvp_session(room_code: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM draft_sessions WHERE session_id = ? AND status = 'waiting' AND mode = 'pvp'",
            (room_code,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_draft_session(session_id: str, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [session_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE draft_sessions SET {set_clause} WHERE session_id = ?", values
        )
        await db.commit()


# ─── Draft participants ─────────────────────────────────────────────────────────

async def create_draft_participant(session_id: str, participant_id: int, seat: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO draft_participants (session_id, participant_id, seat)
            VALUES (?, ?, ?)
        """, (session_id, participant_id, seat))
        await db.commit()


async def get_draft_participant(session_id: str, participant_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM draft_participants WHERE session_id = ? AND participant_id = ?",
            (session_id, participant_id)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_draft_participants(session_id: str) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM draft_participants WHERE session_id = ? ORDER BY seat",
            (session_id,)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def update_draft_participant(session_id: str, participant_id: int, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [session_id, participant_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE draft_participants SET {set_clause} WHERE session_id = ? AND participant_id = ?",
            values
        )
        await db.commit()


# ─── Draft shown-player ledger ──────────────────────────────────────────────────

async def record_shown_player(session_id: str, participant_id: int, slot: str,
                               draw_index: int, player_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO draft_shown_players
                (session_id, participant_id, slot, draw_index, player_id, decision)
            VALUES (?, ?, ?, ?, ?, NULL)
        """, (session_id, participant_id, slot, draw_index, player_id))
        await db.commit()


async def set_shown_decision(session_id: str, participant_id: int, slot: str,
                              draw_index: int, decision: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE draft_shown_players SET decision = ?
            WHERE session_id = ? AND participant_id = ? AND slot = ? AND draw_index = ?
        """, (decision, session_id, participant_id, slot, draw_index))
        await db.commit()


async def get_shown_player_ids(session_id: str) -> list:
    """All player ids ever shown to anyone in this session — the exclusion set."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT player_id FROM draft_shown_players WHERE session_id = ?",
            (session_id,)
        )
        return [row[0] for row in await cursor.fetchall()]


async def get_shown_count_for_slot(session_id: str, participant_id: int, slot: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM draft_shown_players WHERE session_id = ? AND participant_id = ? AND slot = ?",
            (session_id, participant_id, slot)
        )
        row = await cursor.fetchone()
        return row[0] if row else 0


async def get_pending_shown_row(session_id: str, participant_id: int, slot: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM draft_shown_players
            WHERE session_id = ? AND participant_id = ? AND slot = ? AND decision IS NULL
            ORDER BY draw_index DESC LIMIT 1
        """, (session_id, participant_id, slot))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_roster(session_id: str, participant_id: int) -> list:
    """Rows of taken players, in the order they were drafted."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT slot, player_id FROM draft_shown_players
            WHERE session_id = ? AND participant_id = ? AND decision = 'taken'
            ORDER BY id
        """, (session_id, participant_id))
        return [dict(row) for row in await cursor.fetchall()]
