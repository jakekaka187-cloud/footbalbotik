import asyncio
import random
import string
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from config import DRAFT_FORMATION, SLOT_POSITION, PVP_ROOM_EXPIRY_SECONDS
from data.draft_players import get_draft_pool_by_position, get_draft_player_by_id
from database import db


ROOM_CODE_ALPHABET = "".join(c for c in string.ascii_uppercase + string.digits if c not in "0O1IL")


class DraftError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message = message
        self.status = status


class PoolExhaustedError(DraftError):
    def __init__(self, position: str):
        super().__init__(f"Пул игроков на позицию {position} исчерпан", status=500)


_session_locks: dict[str, asyncio.Lock] = {}


def _get_lock(session_id: str) -> asyncio.Lock:
    lock = _session_locks.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _session_locks[session_id] = lock
    return lock


def _generate_code(length: int = 8) -> str:
    return "".join(random.choices(ROOM_CODE_ALPHABET, k=length))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slot_for_index(index: int) -> str:
    return DRAFT_FORMATION[index]


async def create_solo_session(user_id: int) -> dict:
    session_id = _generate_code()
    while await db.get_draft_session(session_id):
        session_id = _generate_code()
    await db.create_draft_session(session_id, mode="solo", creator_id=user_id, status="active")
    await db.create_draft_participant(session_id, user_id, seat=1)
    return {
        "session_id": session_id,
        "mode": "solo",
        "status": "active",
        "slots": DRAFT_FORMATION,
        "current_slot_index": 0,
    }


async def create_pvp_room(user_id: int) -> dict:
    session_id = _generate_code()
    while await db.get_draft_session(session_id):
        session_id = _generate_code()
    expires_at = (datetime.now(timezone.utc) + timedelta(seconds=PVP_ROOM_EXPIRY_SECONDS)).isoformat()
    await db.create_draft_session(session_id, mode="pvp", creator_id=user_id, status="waiting", expires_at=expires_at)
    await db.create_draft_participant(session_id, user_id, seat=1)
    return {
        "session_id": session_id,
        "mode": "pvp",
        "status": "waiting",
        "room_code": session_id,
        "expires_at": expires_at,
    }


async def join_pvp_room(room_code: str, user_id: int) -> dict:
    session = await db.find_joinable_pvp_session(room_code)
    if not session:
        existing = await db.get_draft_session(room_code)
        if existing and existing["status"] != "waiting":
            raise DraftError("Комната уже заполнена или игра завершена", status=409)
        raise DraftError("Комната не найдена", status=404)

    if session["expires_at"] and datetime.fromisoformat(session["expires_at"]) < datetime.now(timezone.utc):
        await db.update_draft_session(room_code, status="expired")
        raise DraftError("Время ожидания истекло", status=410)

    if session["creator_id"] == user_id:
        raise DraftError("Нельзя присоединиться к своей же комнате", status=409)

    await db.create_draft_participant(room_code, user_id, seat=2)
    await db.update_draft_session(room_code, status="active", opponent_id=user_id)
    return {"session_id": room_code, "mode": "pvp", "status": "active"}


# ─── Rematch ─────────────────────────────────────────────────────────────────
# In-memory only (same lifetime assumption as _session_locks) — fine for a
# short-lived "both players tapped play again" handshake, not meant to
# survive a process restart.

_rematch_votes: dict[str, set] = {}
_rematch_result: dict[str, str] = {}


async def _create_matched_session(p1_id: int, p2_id: int) -> str:
    session_id = _generate_code()
    while await db.get_draft_session(session_id):
        session_id = _generate_code()
    await db.create_draft_session(session_id, mode="pvp", creator_id=p1_id, status="active")
    await db.update_draft_session(session_id, opponent_id=p2_id)
    await db.create_draft_participant(session_id, p1_id, seat=1)
    await db.create_draft_participant(session_id, p2_id, seat=2)
    return session_id


async def request_rematch(session_id: str, user_id: int) -> dict:
    if session_id in _rematch_result:
        return {"status": "matched", "session_id": _rematch_result[session_id]}

    session = await db.get_draft_session(session_id)
    if not session or session["status"] != "finished":
        raise DraftError("Игра ещё не завершена", status=409)
    if session["mode"] != "pvp":
        raise DraftError("Реванш доступен только для игры с другом", status=400)

    participants = await db.get_draft_participants(session_id)
    if not any(p["participant_id"] == user_id for p in participants) or len(participants) != 2:
        raise DraftError("Нет доступа к этой сессии", status=403)

    votes = _rematch_votes.setdefault(session_id, set())
    votes.add(user_id)

    other = next(p["participant_id"] for p in participants if p["participant_id"] != user_id)
    if other in votes:
        new_session_id = await _create_matched_session(*[p["participant_id"] for p in participants])
        _rematch_result[session_id] = new_session_id
        return {"status": "matched", "session_id": new_session_id}

    return {"status": "waiting"}


async def _build_participant_view(session_id: str, participant: dict, reveal_self: bool) -> dict:
    view = {
        "telegram_id": participant["participant_id"],
        "current_slot_index": participant["current_slot_index"],
        "status": participant["status"],
    }
    if reveal_self:
        pending = None
        if participant["pending_player_id"] is not None and participant["status"] == "drafting":
            slot = _slot_for_index(participant["current_slot_index"])
            pending = {"slot": slot, "player": get_draft_player_by_id(participant["pending_player_id"])}
        roster_rows = await db.get_roster(session_id, participant["participant_id"])
        roster = [{"slot": r["slot"], "player": get_draft_player_by_id(r["player_id"])} for r in roster_rows]
        view["pending_candidate"] = pending
        view["roster"] = roster
    return view


async def get_session_state(session_id: str, requester_id: int) -> dict:
    session = await db.get_draft_session(session_id)
    if not session:
        raise DraftError("Сессия не найдена", status=404)

    participants = await db.get_draft_participants(session_id)
    is_participant = any(p["participant_id"] == requester_id for p in participants)
    if session["status"] in ("active", "finished") and not is_participant:
        raise DraftError("Нет доступа к этой сессии", status=403)

    me = next((p for p in participants if p["participant_id"] == requester_id), None)
    opponent = next((p for p in participants if p["participant_id"] != requester_id), None)

    result = {
        "session_id": session_id,
        "mode": session["mode"],
        "status": session["status"],
        "slots": DRAFT_FORMATION,
        "me": await _build_participant_view(session_id, me, reveal_self=True) if me else None,
        "opponent": None,
    }
    if session["mode"] == "pvp" and session["status"] == "waiting":
        from config import BOT_USERNAME, WEBAPP_SHORT_NAME
        result["invite_link"] = f"https://t.me/{BOT_USERNAME}/{WEBAPP_SHORT_NAME}?startapp={session_id}"
    if opponent:
        reveal_opponent = session["status"] == "finished"
        opp_view = await _build_participant_view(session_id, opponent, reveal_self=reveal_opponent)
        if not reveal_opponent:
            opp_view["first_name"] = None
        result["opponent"] = opp_view
    return result


async def _draw_candidate(session_id: str, position: str) -> dict:
    shown_ids = set(await db.get_shown_player_ids(session_id))
    pool = [p for p in get_draft_pool_by_position(position) if p["id"] not in shown_ids]
    if not pool:
        raise PoolExhaustedError(position)
    return random.choice(pool)


async def reveal_candidate(session_id: str, user_id: int) -> dict:
    session = await db.get_draft_session(session_id)
    if not session or session["status"] != "active":
        raise DraftError("Сессия неактивна", status=409)

    participant = await db.get_draft_participant(session_id, user_id)
    if not participant:
        raise DraftError("Вы не участник этой сессии", status=403)
    if participant["status"] == "done":
        raise DraftError("Вы уже собрали состав", status=409)

    slot = _slot_for_index(participant["current_slot_index"])

    async with _get_lock(session_id):
        # Idempotent re-fetch: don't burn a new player if one is already pending.
        if participant["pending_player_id"] is not None:
            pending_row = await db.get_pending_shown_row(session_id, user_id, slot)
            if pending_row:
                return {
                    "slot": slot,
                    "player": get_draft_player_by_id(participant["pending_player_id"]),
                    "draw_index": pending_row["draw_index"],
                }

        position = SLOT_POSITION[slot]
        candidate = await _draw_candidate(session_id, position)
        draw_index = await db.get_shown_count_for_slot(session_id, user_id, slot) + 1
        await db.record_shown_player(session_id, user_id, slot, draw_index, candidate["id"])
        await db.update_draft_participant(session_id, user_id, pending_player_id=candidate["id"])

    return {"slot": slot, "player": candidate, "draw_index": draw_index}


async def _finalize_if_done(session_id: str, user_id: int, current_slot_index: int) -> Optional[int]:
    """Marks the participant done once all slots are filled; returns team_rating if just finished."""
    if current_slot_index < len(DRAFT_FORMATION):
        return None

    roster_rows = await db.get_roster(session_id, user_id)
    team_rating = sum(get_draft_player_by_id(r["player_id"])["rating"] for r in roster_rows)
    await db.update_draft_participant(session_id, user_id, status="done", team_rating=team_rating,
                                       pending_player_id=None)
    await db.record_draft_completion(user_id, team_rating)

    session = await db.get_draft_session(session_id)
    if session["mode"] == "solo":
        await db.update_draft_session(session_id, status="finished", finished_at=_now_iso())
    else:
        participants = await db.get_draft_participants(session_id)
        if len(participants) == 2 and all(p["status"] == "done" for p in participants):
            await db.update_draft_session(session_id, status="finished", finished_at=_now_iso())
    return team_rating


async def decide_candidate(session_id: str, user_id: int, action: str) -> dict:
    if action not in ("take", "skip"):
        raise DraftError("Некорректное действие", status=400)

    session = await db.get_draft_session(session_id)
    if not session or session["status"] != "active":
        raise DraftError("Сессия неактивна", status=409)

    participant = await db.get_draft_participant(session_id, user_id)
    if not participant or participant["status"] == "done":
        raise DraftError("Нечего решать — состав уже собран", status=409)
    if participant["pending_player_id"] is None:
        raise DraftError("Сначала нужно показать кандидата (reveal)", status=409)

    slot = _slot_for_index(participant["current_slot_index"])

    async with _get_lock(session_id):
        pending_row = await db.get_pending_shown_row(session_id, user_id, slot)
        if not pending_row:
            raise DraftError("Нечего решать — состав уже собран", status=409)

        skipped_player = None
        alt_player = None
        if action == "take":
            await db.set_shown_decision(session_id, user_id, slot, pending_row["draw_index"], "taken")
            committed_player = get_draft_player_by_id(participant["pending_player_id"])

            # Draw (and burn from the pool) who the alternative would have been,
            # purely so the player can see what they passed up by not skipping.
            # Never committed to the roster — decision stays 'shown_alt'.
            try:
                position = SLOT_POSITION[slot]
                alt_candidate = await _draw_candidate(session_id, position)
                alt_draw_index = pending_row["draw_index"] + 1
                await db.record_shown_player(session_id, user_id, slot, alt_draw_index, alt_candidate["id"])
                await db.set_shown_decision(session_id, user_id, slot, alt_draw_index, "shown_alt")
                alt_player = alt_candidate
            except PoolExhaustedError:
                pass
        else:
            await db.set_shown_decision(session_id, user_id, slot, pending_row["draw_index"], "skipped")
            skipped_player = get_draft_player_by_id(participant["pending_player_id"])

            position = SLOT_POSITION[slot]
            candidate = await _draw_candidate(session_id, position)
            draw_index = pending_row["draw_index"] + 1
            await db.record_shown_player(session_id, user_id, slot, draw_index, candidate["id"])
            await db.set_shown_decision(session_id, user_id, slot, draw_index, "taken")
            committed_player = candidate

        next_slot_index = participant["current_slot_index"] + 1
        await db.update_draft_participant(session_id, user_id,
                                           current_slot_index=next_slot_index,
                                           pending_player_id=None)

    team_rating = await _finalize_if_done(session_id, user_id, next_slot_index)

    response = {
        "slot": slot,
        "committed_player": committed_player,
        "current_slot_index": next_slot_index,
        "status": "done" if team_rating is not None else "drafting",
        "team_rating": team_rating,
    }
    if skipped_player is not None:
        response["skipped_player"] = skipped_player
    if alt_player is not None:
        response["alt_player"] = alt_player
    return response


async def get_finished_result(session_id: str, requester_id: int) -> dict:
    session = await db.get_draft_session(session_id)
    if not session:
        raise DraftError("Сессия не найдена", status=404)
    if session["status"] != "finished":
        raise DraftError("Игра ещё не завершена", status=409)

    participants = await db.get_draft_participants(session_id)
    if not any(p["participant_id"] == requester_id for p in participants):
        raise DraftError("Нет доступа к этой сессии", status=403)

    result_participants = []
    for p in participants:
        roster_rows = await db.get_roster(session_id, p["participant_id"])
        roster = [{"slot": r["slot"], "player": get_draft_player_by_id(r["player_id"])} for r in roster_rows]
        result_participants.append({
            "telegram_id": p["participant_id"],
            "roster": roster,
            "team_rating": p["team_rating"],
            "team_ovr_avg": round(p["team_rating"] / len(DRAFT_FORMATION), 1) if p["team_rating"] else None,
        })

    _session_locks.pop(session_id, None)

    return {
        "session_id": session_id,
        "mode": session["mode"],
        "finished_at": session["finished_at"],
        "participants": result_participants,
    }
