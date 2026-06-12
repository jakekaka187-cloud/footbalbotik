import aiosqlite
import json
from typing import Optional
from config import DATABASE_URL, COMPETITION_MIN_WINS
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                session_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                footballer_id INTEGER NOT NULL,
                clubs_shown INTEGER DEFAULT 0,
                player1_id INTEGER,
                player2_id INTEGER,
                current_turn INTEGER,
                status TEXT DEFAULT 'waiting',
                winner_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                footballer_id INTEGER NOT NULL,
                clubs_used INTEGER NOT NULL,
                score INTEGER NOT NULL,
                result TEXT NOT NULL,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Add new columns if they don't exist yet (safe for existing DBs)
        for col_def in [
            "ALTER TABLE users ADD COLUMN season_score INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN season_wins INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0",
            "ALTER TABLE game_history ADD COLUMN mode TEXT DEFAULT 'bot'",
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
        await db.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
            (telegram_id, username, first_name)
        )
        await db.commit()
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


async def update_user_stats(telegram_id: int, won: bool, score: int):
    user = await get_user(telegram_id)
    if not user:
        return
    new_streak = user.current_streak + 1 if won else 0
    best_streak = max(user.best_streak, new_streak)
    best_score = max(user.best_score, score)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET
                games_played = games_played + 1,
                games_won = games_won + ?,
                games_lost = games_lost + ?,
                total_score = total_score + ?,
                best_score = ?,
                current_streak = ?,
                best_streak = ?,
                season_score = season_score + ?,
                season_wins = season_wins + ?
            WHERE telegram_id = ?
        """, (
            1 if won else 0,
            0 if won else 1,
            score,
            best_score,
            new_streak,
            best_streak,
            score,
            1 if won else 0,
            telegram_id
        ))
        await db.commit()


async def get_leaderboard(limit: int = 10) -> list:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT telegram_id, username, first_name, total_score, games_won, best_streak
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
        # Check that new_user has no referrer yet
        cursor = await db.execute(
            "SELECT referred_by FROM users WHERE telegram_id = ?", (new_user_id,)
        )
        row = await cursor.fetchone()
        if not row or row[0] is not None:
            return False
        # Mark new user as referred
        await db.execute(
            "UPDATE users SET referred_by = ? WHERE telegram_id = ?",
            (referrer_id, new_user_id)
        )
        # Give referrer 1500 pts (season + total) and increment referral count
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
            "SELECT COUNT(DISTINCT user_id) FROM game_history WHERE played_at >= date('now')"
        )).fetchone())[0]
        active_week = (await (await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM game_history WHERE played_at >= date('now', '-7 days')"
        )).fetchone())[0]
        total_games = (await (await db.execute("SELECT COUNT(*) FROM game_history")).fetchone())[0]
        total_referrals = (await (await db.execute(
            "SELECT COUNT(*) FROM users WHERE referred_by IS NOT NULL"
        )).fetchone())[0]
        webapp_players = (await (await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM game_history WHERE mode LIKE 'webapp_%'"
        )).fetchone())[0]
        webapp_games = (await (await db.execute(
            "SELECT COUNT(*) FROM game_history WHERE mode LIKE 'webapp_%'"
        )).fetchone())[0]
        webapp_today = (await (await db.execute(
            "SELECT COUNT(DISTINCT user_id) FROM game_history WHERE mode LIKE 'webapp_%' AND played_at >= date('now')"
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
            "webapp_players": webapp_players,
            "webapp_games": webapp_games,
            "webapp_today": webapp_today,
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
        """, (COMPETITION_MIN_WINS, limit))
        return [dict(row) for row in await cursor.fetchall()]


# ─── Game Sessions ────────────────────────────────────────────────────────────

async def create_game_session(session_id: str, mode: str, footballer_id: int,
                               player1_id: int, player2_id: Optional[int] = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO game_sessions
                (session_id, mode, footballer_id, player1_id, player2_id, current_turn, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, mode, footballer_id, player1_id, player2_id,
            player1_id, "active" if mode == "solo" else "waiting"
        ))
        await db.commit()


async def get_session(session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM game_sessions WHERE session_id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_session(session_id: str, **kwargs):
    if not kwargs:
        return
    set_clause = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [session_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"UPDATE game_sessions SET {set_clause} WHERE session_id = ?", values
        )
        await db.commit()


async def find_waiting_pvp_session(session_id: str) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM game_sessions WHERE session_id = ? AND status = 'waiting' AND mode = 'pvp'",
            (session_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def save_game_history(user_id: int, footballer_id: int, clubs_used: int,
                             score: int, result: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO game_history (user_id, footballer_id, clubs_used, score, result)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, footballer_id, clubs_used, score, result))
        await db.commit()


async def save_webapp_play(user_id: int, game: str, score: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO game_history (user_id, footballer_id, clubs_used, score, result, mode)
            VALUES (?, 0, 0, ?, 'win', ?)
        """, (user_id, score, f"webapp_{game}"))
        await db.commit()