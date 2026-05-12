import random
import uuid
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.db import (
    get_or_create_user, update_user_stats, save_game_history,
    get_session, update_session, create_game_session, find_waiting_pvp_session
)

router = Router()

from aiogram.fsm.state import State, StatesGroup

class ClubGameStates(StatesGroup):
    waiting_for_guess = State()
    pvp_waiting_for_opponent = State()
    pvp_waiting_for_guess = State()
    pvp_waiting_for_join = State()


def get_club_keyboard(session_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🏳️ Сдаться",
        callback_data=f"club_giveup:{session_id}"
    ))
    return builder.as_markup()


def play_again_clubs_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚽ Ещё раз!", callback_data="clubs_play_again"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def play_again_clubs_pvp_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Новая дуэль!", callback_data="clubs_pvp_again"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def clubs_pvp_join_keyboard(room_code: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🟢 Принять вызов!",
        callback_data=f"clubs_join_pvp:{room_code}"
    ))
    return builder.as_markup()


def clubs_pvp_game_keyboard(room_code: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🏳️ Сдаться",
        callback_data=f"clubs_pvp_giveup:{room_code}"
    ))
    return builder.as_markup()


def format_players_text(club: dict, revealed_count: int) -> str:
    players = club["players"][:revealed_count]
    lines = []
    for i, p in enumerate(players, 1):
        lines.append(f"{i}. {p['nationality']} — {p['position']}")
    return "\n".join(lines)


def check_club_answer(answer: str, club: dict) -> bool:
    ans = answer.strip().lower()
    name = club["name"].lower()
    if ans == name:
        return True
    if len(ans) >= 4 and ans in name:
        return True
    for word in name.split():
        if len(word) >= 4 and ans == word:
            return True
    return False


def calculate_club_score(revealed: int) -> int:
    scores = {3: 100, 4: 85, 5: 70, 6: 55, 7: 40, 8: 30, 9: 20, 10: 15, 11: 10}
    return scores.get(revealed, 10)


# ── СОЛО ИГРА ────────────────────────────────────────

@router.message(F.text == "🏟️ Угадай клуб")
@router.callback_query(F.data == "clubs_play_again")
async def start_clubs_game(event, state: FSMContext):
    await state.clear()
    is_callback = isinstance(event, CallbackQuery)
    user_id = event.from_user.id
    message = event.message if is_callback else event

    from data.clubs_data import CLUBS
    club = random.choice(CLUBS)
    session_id = str(uuid.uuid4())[:8]

    await create_game_session(
        session_id=session_id,
        mode="solo",
        footballer_id=club["id"],
        player1_id=user_id
    )
    await update_session(session_id, clubs_shown=3)

    await state.set_state(ClubGameStates.waiting_for_guess)
    await state.update_data(session_id=session_id, club_id=club["id"], revealed=3)

    players_text = format_players_text(club, 3)
    text = (
        "🏟️ *Угадай клуб по национальностям!*\n\n"
        f"📋 Игроки (3 из 11):\n\n{players_text}\n\n"
        "Напиши название клуба! 👇"
    )

    if is_callback:
        await event.answer()
        await message.answer(text, parse_mode="Markdown", reply_markup=get_club_keyboard(session_id))
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=get_club_keyboard(session_id))


@router.message(ClubGameStates.waiting_for_guess)
async def handle_clubs_guess(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    club_id = data.get("club_id")
    revealed = data.get("revealed", 3)

    if not session_id or not club_id:
        await message.answer("Начни новую игру!", reply_markup=play_again_clubs_keyboard())
        await state.clear()
        return

    from data.clubs_data import get_club_by_id
    club = get_club_by_id(club_id)

    if check_club_answer(message.text, club):
        score = calculate_club_score(revealed)
        await update_session(session_id, status="finished")
        await update_user_stats(message.from_user.id, won=True, score=score)
        await state.clear()

        if revealed <= 3:
            reaction = "🤯 НЕВЕРОЯТНО! С первых 3 игроков!"
        elif revealed <= 5:
            reaction = "🔥 ОГОНЬ! Быстро угадал!"
        elif revealed <= 7:
            reaction = "💪 Красавчик!"
        else:
            reaction = "✅ Верно!"

        await message.answer(
            f"{reaction}\n\n"
            f"🏟️ *{club['name']}* {club['emoji']}\n"
            f"🏆 {club['league']}\n\n"
            f"💰 *+{score} очков!*\n"
            f"Угадал по {revealed} игрокам",
            parse_mode="Markdown",
            reply_markup=play_again_clubs_keyboard()
        )
    else:
        responses = ["❌ Не то!", "🤔 Нет...", "😅 Мимо!", "⚡ Неверно!"]
        await message.answer(random.choice(responses))

        if revealed >= 11:
            await update_session(session_id, status="finished")
            await update_user_stats(message.from_user.id, won=False, score=0)
            await state.clear()
            await message.answer(
                f"😔 Не угадал...\n\n"
                f"Это был *{club['name']}* {club['emoji']}\n"
                f"🏆 {club['league']}",
                parse_mode="Markdown",
                reply_markup=play_again_clubs_keyboard()
            )
        else:
            new_revealed = revealed + 1
            await state.update_data(revealed=new_revealed)
            players_text = format_players_text(club, new_revealed)
            await message.answer(
                f"📋 Игроки ({new_revealed} из 11):\n\n{players_text}\n\n"
                f"Кто это? Пиши! 👇",
                parse_mode="Markdown",
                reply_markup=get_club_keyboard(session_id)
            )


@router.callback_query(F.data.startswith("club_giveup:"))
async def handle_club_giveup(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    club_id = data.get("club_id")
    session_id = callback.data.split(":")[1]

    from data.clubs_data import get_club_by_id
    club = get_club_by_id(club_id)

    await update_session(session_id, status="finished")
    await update_user_stats(callback.from_user.id, won=False, score=0)
    await state.clear()

    await callback.message.edit_text(
        f"🏳️ Сдался!\n\n"
        f"Это был *{club['name']}* {club['emoji']}\n"
        f"🏆 {club['league']}",
        parse_mode="Markdown",
        reply_markup=play_again_clubs_keyboard()
    )
    await callback.answer()


# ── PvP ИГРА ─────────────────────────────────────────

@router.message(F.text == "👥 Дуэль: клубы")
@router.callback_query(F.data == "clubs_pvp_again")
async def start_clubs_pvp(event, state: FSMContext):
    await state.clear()
    is_callback = isinstance(event, CallbackQuery)
    user_id = event.from_user.id
    message = event.message if is_callback else event

    from data.clubs_data import CLUBS
    club = random.choice(CLUBS)
    room_code = str(uuid.uuid4())[:6].upper()

    await create_game_session(
        session_id=room_code,
        mode="pvp",
        footballer_id=club["id"],
        player1_id=user_id
    )

    await state.set_state(ClubGameStates.pvp_waiting_for_opponent)
    await state.update_data(room_code=room_code)

    if is_callback:
        await event.answer()

    await message.answer(
        f"🏟️ *Дуэль: Угадай клуб!*\n\n"
        f"Комната создана!\n"
        f"Код: `{room_code}`\n\n"
        f"Отправь другу: /clubs_join {room_code}\n\n"
        f"⏳ Жду соперника...",
        parse_mode="Markdown",
        reply_markup=clubs_pvp_join_keyboard(room_code)
    )


@router.message(Command("clubs_join"))
async def cmd_clubs_join(message: Message, state: FSMContext, bot: Bot):
    parts = message.text.split()
    if len(parts) < 2:
        await state.set_state(ClubGameStates.pvp_waiting_for_join)
        await message.answer("🔑 Введи код комнаты:")
        return
    await _do_clubs_join(message, state, bot, parts[1])


@router.message(ClubGameStates.pvp_waiting_for_join)
async def handle_clubs_join_code(message: Message, state: FSMContext, bot: Bot):
    await _do_clubs_join(message, state, bot, message.text.strip())


@router.callback_query(F.data.startswith("clubs_join_pvp:"))
async def cb_clubs_join_pvp(callback: CallbackQuery, state: FSMContext, bot: Bot):
    room_code = callback.data.split(":")[1]
    await callback.answer()

    class FakeMessage:
        def __init__(self, cb):
            self.from_user = cb.from_user
            self.text = ""
            self._cb = cb
        async def answer(self, text, **kwargs):
            await self._cb.message.answer(text, **kwargs)

    await _do_clubs_join(FakeMessage(callback), state, bot, room_code)


async def _do_clubs_join(message, state: FSMContext, bot: Bot, room_code: str):
    session = await find_waiting_pvp_session(room_code.upper())
    if not session:
        await message.answer("❌ Комната не найдена! Проверь код.")
        return
    if session["player1_id"] == message.from_user.id:
        await message.answer("😅 Нельзя играть против себя!")
        return

    room_code = room_code.upper()
    club_id = session["footballer_id"]

    from data.clubs_data import get_club_by_id
    club = get_club_by_id(club_id)

    await update_session(
        room_code,
        player2_id=message.from_user.id,
        status="active",
        current_turn=session["player1_id"],
        current_turn_tried=0,
        clubs_shown=3
    )

    await state.set_state(ClubGameStates.pvp_waiting_for_guess)
    await state.update_data(room_code=room_code, club_id=club_id, revealed=3)

    host_state = FSMContext(
        storage=state.storage,
        key=StorageKey(bot_id=bot.id, chat_id=session["player1_id"], user_id=session["player1_id"])
    )
    await host_state.set_state(ClubGameStates.pvp_waiting_for_guess)
    await host_state.update_data(room_code=room_code, club_id=club_id, revealed=3)

    players_text = format_players_text(club, 3)
    guest_name = message.from_user.first_name or "Соперник"

    await message.answer(
        "🔥 Ты вошёл в комнату!\n\n"
        "⏳ Сейчас ход хозяина... Жди!",
        parse_mode="Markdown",
        reply_markup=clubs_pvp_game_keyboard(room_code)
    )

    try:
        await bot.send_message(
            session["player1_id"],
            "🔥 *" + guest_name + "* принял вызов!\n\n"
            "👉 *ТВОЙ ХОД!*\n\n"
            "📋 Игроки (3 из 11):\n\n" + players_text + "\n\n"
            "Напиши название клуба! 🎯",
            parse_mode="Markdown",
            reply_markup=clubs_pvp_game_keyboard(room_code)
        )
    except Exception as e:
        print("Ошибка: " + str(e))


@router.message(ClubGameStates.pvp_waiting_for_guess)
async def handle_clubs_pvp_guess(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    room_code = data.get("room_code")
    club_id = data.get("club_id")
    revealed = data.get("revealed", 3)

    if not room_code:
        await message.answer("⚠️ Игра не найдена!")
        await state.clear()
        return

    session = await get_session(room_code)
    if not session or session["status"] != "active":
        await message.answer("⚠️ Игра уже завершена!")
        await state.clear()
        return

    if session["current_turn"] != message.from_user.id:
        await message.answer("⏳ Подожди, сейчас ход соперника!")
        return

    from data.clubs_data import get_club_by_id
    club = get_club_by_id(club_id)
    opponent_id = session["player2_id"] if message.from_user.id == session["player1_id"] else session["player1_id"]
    already_tried = session.get("current_turn_tried", 0)

    if check_club_answer(message.text, club):
        score = calculate_club_score(revealed)
        await update_session(room_code, status="finished", winner_id=message.from_user.id)
        await update_user_stats(message.from_user.id, won=True, score=score)
        await update_user_stats(opponent_id, won=False, score=0)

        await state.clear()
        opp_state = FSMContext(
            storage=state.storage,
            key=StorageKey(bot_id=bot.id, chat_id=opponent_id, user_id=opponent_id)
        )
        await opp_state.clear()

        winner_name = message.from_user.first_name or "Игрок"
        await message.answer(
            "🏆 *ТЫ ПОБЕДИЛ!*\n\n"
            "🏟️ Это был *" + club['name'] + "* " + club['emoji'] + "\n"
            "🏆 " + club['league'] + "\n\n"
            "💰 *+" + str(score) + " очков!*",
            parse_mode="Markdown",
            reply_markup=play_again_clubs_pvp_keyboard()
        )
        try:
            await bot.send_message(
                opponent_id,
                "😤 *" + winner_name + "* угадал раньше!\n\n"
                "🏟️ Это был *" + club['name'] + "* " + club['emoji'] + "\n"
                "🏆 " + club['league'],
                parse_mode="Markdown",
                reply_markup=play_again_clubs_pvp_keyboard()
            )
        except Exception:
            pass
        return

    await message.answer("❌ Не угадал! Ход переходит к сопернику...")

    if already_tried == 0:
        await update_session(room_code, current_turn=opponent_id, current_turn_tried=1)
        players_text = format_players_text(club, revealed)
        try:
            await bot.send_message(
                opponent_id,
                "👉 *ТВОЙ ХОД!*\n\n"
                "📋 Игроки (" + str(revealed) + " из 11):\n\n" + players_text + "\n\n"
                "Напиши название клуба! 🎯",
                parse_mode="Markdown",
                reply_markup=clubs_pvp_game_keyboard(room_code)
            )
        except Exception as e:
            print("Ошибка: " + str(e))
    else:
        if revealed >= 11:
            await update_session(room_code, status="finished")
            await state.clear()
            opp_state = FSMContext(
                storage=state.storage,
                key=StorageKey(bot_id=bot.id, chat_id=opponent_id, user_id=opponent_id)
            )
            await opp_state.clear()

            await message.answer(
                "🤝 Никто не угадал...\n\n"
                "🏟️ Это был *" + club['name'] + "* " + club['emoji'] + "\n"
                "🏆 " + club['league'],
                parse_mode="Markdown",
                reply_markup=play_again_clubs_pvp_keyboard()
            )
            try:
                await bot.send_message(
                    opponent_id,
                    "🤝 Никто не угадал...\n\n"
                    "🏟️ Это был *" + club['name'] + "* " + club['emoji'] + "\n"
                    "🏆 " + club['league'],
                    parse_mode="Markdown",
                    reply_markup=play_again_clubs_pvp_keyboard()
                )
            except Exception:
                pass
        else:
            new_revealed = revealed + 1
            await update_session(
                room_code,
                clubs_shown=new_revealed,
                current_turn=opponent_id,
                current_turn_tried=0
            )
            await state.update_data(revealed=new_revealed)
            opp_state = FSMContext(
                storage=state.storage,
                key=StorageKey(bot_id=bot.id, chat_id=opponent_id, user_id=opponent_id)
            )
            await opp_state.update_data(revealed=new_revealed)

            players_text = format_players_text(club, new_revealed)
            try:
                await bot.send_message(
                    opponent_id,
                    "👉 *ТВОЙ ХОД!*\n\n"
                    "📋 Игроки (" + str(new_revealed) + " из 11):\n\n" + players_text + "\n\n"
                    "Напиши название клуба! 🎯",
                    parse_mode="Markdown",
                    reply_markup=clubs_pvp_game_keyboard(room_code)
                )
            except Exception as e:
                print("Ошибка: " + str(e))


@router.callback_query(F.data.startswith("clubs_pvp_giveup:"))
async def handle_clubs_pvp_giveup(callback: CallbackQuery, state: FSMContext, bot: Bot):
    room_code = callback.data.split(":")[1]
    session = await get_session(room_code)
    if not session:
        await callback.answer("Игра уже завершена")
        return

    data = await state.get_data()
    club_id = data.get("club_id")
    from data.clubs_data import get_club_by_id
    club = get_club_by_id(club_id)

    opponent_id = (
        session["player2_id"]
        if callback.from_user.id == session["player1_id"]
        else session["player1_id"]
    )

    await update_session(room_code, status="finished", winner_id=opponent_id)
    await update_user_stats(callback.from_user.id, won=False, score=0)
    if opponent_id:
        await update_user_stats(opponent_id, won=True, score=10)

    await state.clear()
    if opponent_id:
        opp_state = FSMContext(
            storage=state.storage,
            key=StorageKey(bot_id=bot.id, chat_id=opponent_id, user_id=opponent_id)
        )
        await opp_state.clear()

    name = club["name"] if club else "?"
    emoji = club["emoji"] if club else ""

    await callback.message.edit_text(
        "🏳️ Ты сдался!\n\nЭто был *" + name + "* " + emoji,
        parse_mode="Markdown",
        reply_markup=play_again_clubs_pvp_keyboard()
    )

    giver_name = callback.from_user.first_name or "Соперник"
    try:
        await bot.send_message(
            opponent_id,
            "🏆 *" + giver_name + "* сдался! Ты победил!\n\nЭто был *" + name + "* " + emoji,
            parse_mode="Markdown",
            reply_markup=play_again_clubs_pvp_keyboard()
        )
    except Exception:
        pass

    await callback.answer()