import random
import uuid
from typing import Optional
from config import POINTS_TABLE, MAX_CLUBS_TOTAL
from data.footballers import get_footballer_by_id, get_all_ids
from database.db import (
    create_game_session, get_session, update_session,
    update_user_stats, save_game_history, find_waiting_pvp_session
)


def pick_random_footballer(exclude_id: Optional[int] = None) -> dict:
    ids = get_all_ids()
    if exclude_id and exclude_id in ids:
        ids.remove(exclude_id)
    footballer_id = random.choice(ids)
    return get_footballer_by_id(footballer_id)


def calculate_score(clubs_shown: int) -> int:
    return POINTS_TABLE.get(clubs_shown, 5)


def check_answer(user_answer: str, footballer: dict) -> bool:
    answer = user_answer.strip().lower()
    name = footballer["name"].lower()
    if answer == name:
        return True
    parts = name.split()
    if len(parts) >= 2 and answer == parts[-1]:
        return True
    if len(parts) >= 2 and answer == parts[0]:
        return True
    if len(answer) >= 4 and answer in name:
        return True
    return False


def get_club_display(footballer: dict, club_index: int) -> str:
    club = footballer["clubs"][club_index]
    return f"{club['emoji']} {club['name']} ({club['years']})"


def get_clubs_so_far(footballer: dict, clubs_shown: int) -> str:
    lines = []
    for i in range(min(clubs_shown, len(footballer["clubs"]))):
        club = footballer["clubs"][i]
        lines.append(f"{i + 1}. {club['emoji']} {club['name']} ({club['years']})")
    return "\n".join(lines)


def all_clubs_shown(footballer: dict, clubs_shown: int) -> bool:
    total = len(footballer["clubs"])
    limit = min(MAX_CLUBS_TOTAL, total)
    return clubs_shown >= limit


async def start_solo_game(user_id: int) -> dict:
    footballer = pick_random_footballer()
    session_id = str(uuid.uuid4())[:8]
    await create_game_session(
        session_id=session_id,
        mode="solo",
        footballer_id=footballer["id"],
        player1_id=user_id
    )
    return {"session_id": session_id, "footballer": footballer}


async def process_solo_guess(session_id: str, user_id: int, guess: str) -> dict:
    session = await get_session(session_id)
    if not session or session["status"] != "active":
        return {"error": "session_not_found"}

    footballer = get_footballer_by_id(session["footballer_id"])
    clubs_shown = session["clubs_shown"]

    if check_answer(guess, footballer):
        score = calculate_score(clubs_shown)
        await update_session(session_id, status="finished", winner_id=user_id)
        await update_user_stats(user_id, won=True, score=score)
        await save_game_history(user_id, footballer["id"], clubs_shown, score, "win")
        return {
            "correct": True,
            "score": score,
            "clubs_shown": clubs_shown,
            "game_over": True,
            "footballer": footballer,
        }

    next_clubs_shown = clubs_shown + 1
    await update_session(session_id, clubs_shown=next_clubs_shown)
    last_chance = all_clubs_shown(footballer, next_clubs_shown)

    return {
        "correct": False,
        "clubs_shown": next_clubs_shown,
        "game_over": False,
        "last_chance": last_chance,
        "footballer": footballer,
    }


async def skip_solo_club(session_id: str) -> dict:
    session = await get_session(session_id)
    if not session or session["status"] != "active":
        return {"error": "session_not_found"}

    footballer = get_footballer_by_id(session["footballer_id"])
    new_clubs_shown = session["clubs_shown"] + 1
    await update_session(session_id, clubs_shown=new_clubs_shown)
    last_chance = all_clubs_shown(footballer, new_clubs_shown)

    return {
        "clubs_shown": new_clubs_shown,
        "game_over": False,
        "last_chance": last_chance,
        "footballer": footballer,
    }


async def give_up_solo(session_id: str, user_id: int) -> dict:
    session = await get_session(session_id)
    if not session:
        return {"error": "not_found"}
    footballer = get_footballer_by_id(session["footballer_id"])
    await update_session(session_id, status="finished")
    await update_user_stats(user_id, won=False, score=0)
    await save_game_history(user_id, footballer["id"], session["clubs_shown"], 0, "gave_up")
    return {"footballer": footballer}


async def create_pvp_room(host_id: int) -> dict:
    footballer = pick_random_footballer()
    room_code = str(uuid.uuid4())[:6].upper()
    await create_game_session(
        session_id=room_code,
        mode="pvp",
        footballer_id=footballer["id"],
        player1_id=host_id
    )
    return {"room_code": room_code, "footballer": footballer}


async def join_pvp_room(room_code: str, guest_id: int) -> dict:
    session = await find_waiting_pvp_session(room_code.upper())
    if not session:
        return {"error": "room_not_found"}
    if session["player1_id"] == guest_id:
        return {"error": "cant_join_own_room"}
    await update_session(
        room_code.upper(),
        player2_id=guest_id,
        status="active",
        current_turn=session["player1_id"],
        current_turn_tried=0
    )
    footballer = get_footballer_by_id(session["footballer_id"])
    return {"session": session, "footballer": footballer, "host_id": session["player1_id"]}


async def process_pvp_guess(room_code: str, user_id: int, guess: str) -> dict:
    """
    Логика ходов:
    - current_turn_tried=0: первый игрок ещё не отвечал на текущий клуб
    - current_turn_tried=1: первый игрок ответил, ждём второго

    Схема:
    Клуб 1 показан -> хост отвечает (tried=0->1) -> гость отвечает (tried=1->0, открываем клуб 2)
    Клуб 2 показан -> хост отвечает -> гость отвечает -> открываем клуб 3
    И так далее пока не закончатся клубы.
    Игра заканчивается только когда ВТОРОЙ игрок ответил на ПОСЛЕДНИЙ клуб.
    """
    session = await get_session(room_code.upper())
    if not session or session["status"] != "active":
        return {"error": "session_not_found"}
    if session["current_turn"] != user_id:
        return {"error": "not_your_turn"}

    footballer = get_footballer_by_id(session["footballer_id"])
    clubs_shown = session["clubs_shown"]
    already_tried = session.get("current_turn_tried", 0)

    # Правильный ответ — победа
    if check_answer(guess, footballer):
        loser_id = session["player2_id"] if user_id == session["player1_id"] else session["player1_id"]
        await update_session(room_code.upper(), status="finished", winner_id=user_id)
        await update_user_stats(user_id, won=True, score=0)
        await update_user_stats(loser_id, won=False, score=0)
        return {
            "correct": True,
            "score": 0,
            "winner_id": user_id,
            "loser_id": loser_id,
            "footballer": footballer,
            "clubs_shown": clubs_shown,
        }

    # Неверный ответ
    next_turn = session["player2_id"] if user_id == session["player1_id"] else session["player1_id"]

    if already_tried == 0:
        # Первый игрок ответил неверно — передаём ход второму, клуб не меняем
        await update_session(
            room_code.upper(),
            current_turn=next_turn,
            current_turn_tried=1
        )
        return {
            "correct": False,
            "next_turn": next_turn,
            "clubs_shown": clubs_shown,
            "new_club": False,
            "game_over": False,
            "footballer": footballer,
        }
    else:
        # Второй игрок тоже ответил неверно
        # Проверяем — это был последний клуб?
        if all_clubs_shown(footballer, clubs_shown):
            # Оба ответили на последний клуб и не угадали — конец игры
            await update_session(room_code.upper(), status="finished")
            return {
                "correct": False,
                "next_turn": next_turn,
                "clubs_shown": clubs_shown,
                "new_club": False,
                "game_over": True,
                "footballer": footballer,
            }
        else:
            # Открываем следующий клуб, первым ходит тот кто начинал раунд
            # Чередуем: если хост начинал этот раунд, гость начинает следующий
            host_id = session["player1_id"]
            # Следующий раунд начинает тот кто ещё не отвечал первым
            # Просто передаём ход next_turn (второй игрок) и сбрасываем tried
            new_clubs_shown = clubs_shown + 1
            await update_session(
                room_code.upper(),
                clubs_shown=new_clubs_shown,
                current_turn=next_turn,
                current_turn_tried=0
            )
            return {
                "correct": False,
                "next_turn": next_turn,
                "clubs_shown": new_clubs_shown,
                "new_club": True,
                "game_over": False,
                "footballer": footballer,
            }