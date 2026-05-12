from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey

from services.game_service import (
    create_pvp_room, join_pvp_room, process_pvp_guess,
    get_clubs_so_far, get_club_display, all_clubs_shown
)
from database.db import get_session, update_session, get_user
from keyboards.keyboards import (
    pvp_join_keyboard, pvp_game_keyboard, play_again_pvp_keyboard, main_menu_keyboard
)
from utils.states import PvPGameStates
from utils.messages import (
    pvp_room_created_text, pvp_your_turn_text,
    pvp_opponent_turn_text, pvp_win_text, pvp_lose_text, pvp_draw_text,
    ERROR_SESSION_NOT_FOUND, ERROR_NOT_YOUR_TURN, ERROR_ROOM_NOT_FOUND, ERROR_CANT_JOIN_OWN
)

router = Router()


@router.message(F.text == "👥 Угадай карьеру с другом")
@router.callback_query(F.data == "play_again_pvp")
async def start_pvp(event, state: FSMContext, bot: Bot):
    await state.clear()
    is_callback = isinstance(event, CallbackQuery)

    from utils.check_subscription import check_subscription
    subscribed = await check_subscription(bot, event)
    if not subscribed:
        return
    user_id = event.from_user.id
    message = event.message if is_callback else event

    game = await create_pvp_room(user_id)
    room_code = game["room_code"]

    await state.set_state(PvPGameStates.waiting_for_opponent)
    await state.update_data(room_code=room_code)

    if is_callback:
        await event.answer()

    await message.answer(
        pvp_room_created_text(room_code),
        parse_mode="Markdown",
        reply_markup=pvp_join_keyboard(room_code)
    )


@router.message(Command("join"))
async def cmd_join(message: Message, state: FSMContext, bot: Bot):
    parts = message.text.split()
    if len(parts) < 2:
        await state.set_state(PvPGameStates.waiting_for_join_code)
        await message.answer("🔑 Введи код комнаты:")
        return
    await _do_join(message, state, bot, parts[1])


@router.message(PvPGameStates.waiting_for_join_code)
async def handle_join_code(message: Message, state: FSMContext, bot: Bot):
    await _do_join(message, state, bot, message.text.strip())


async def _do_join(message: Message, state: FSMContext, bot: Bot, room_code: str):
    result = await join_pvp_room(room_code, message.from_user.id)

    if "error" in result:
        if result["error"] == "room_not_found":
            await message.answer(ERROR_ROOM_NOT_FOUND)
        elif result["error"] == "cant_join_own_room":
            await message.answer(ERROR_CANT_JOIN_OWN)
        return

    host_id = result["host_id"]
    footballer = result["footballer"]
    room_code = room_code.upper()

    # FSM для гостя
    await state.set_state(PvPGameStates.waiting_for_guess)
    await state.update_data(room_code=room_code)

    # FSM для хоста
    host_state = FSMContext(
        storage=state.storage,
        key=StorageKey(bot_id=bot.id, chat_id=host_id, user_id=host_id)
    )
    await host_state.set_state(PvPGameStates.waiting_for_guess)
    await host_state.update_data(room_code=room_code)

    await update_session(room_code, clubs_shown=1)
    clubs_text = get_clubs_so_far(footballer, 1)
    guest_name = message.from_user.first_name or "Соперник"

    # Гостю — только уведомление, без клубов
    await message.answer(
        "🔥 Ты вошёл в комнату!\n\n"
        "Правила: по очереди называете футболиста.\n"
        "Каждый раунд сначала ходит хозяин, потом гость.\n"
        "Кто первый угадает — победил!\n\n"
        "⏳ Сейчас ход соперника... Жди!",
        parse_mode="Markdown",
        reply_markup=pvp_game_keyboard(room_code)
    )

    # Хосту — первый клуб
    try:
        await bot.send_message(
            host_id,
            "🔥 *" + guest_name + "* принял вызов! Начинаем!\n\n" +
            pvp_your_turn_text(clubs_text, 1),
            parse_mode="Markdown",
            reply_markup=pvp_game_keyboard(room_code)
        )
    except Exception as e:
        print("Ошибка отправки хосту: " + str(e))


@router.callback_query(F.data.startswith("join_pvp:"))
async def cb_join_pvp(callback: CallbackQuery, state: FSMContext, bot: Bot):
    room_code = callback.data.split(":")[1]
    await callback.answer()

    class FakeMessage:
        def __init__(self, cb):
            self.from_user = cb.from_user
            self.text = ""
            self._cb = cb
        async def answer(self, text, **kwargs):
            await self._cb.message.answer(text, **kwargs)

    fake = FakeMessage(callback)
    await _do_join(fake, state, bot, room_code)


@router.message(PvPGameStates.waiting_for_guess)
async def handle_pvp_guess(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    room_code = data.get("room_code")
    if not room_code:
        await message.answer(ERROR_SESSION_NOT_FOUND)
        await state.clear()
        return

    result = await process_pvp_guess(room_code, message.from_user.id, message.text)

    if "error" in result:
        if result["error"] == "not_your_turn":
            await message.answer(ERROR_NOT_YOUR_TURN)
        else:
            await message.answer(ERROR_SESSION_NOT_FOUND)
            await state.clear()
        return

    footballer = result["footballer"]

    # Победа
    if result["correct"]:
        winner_id = result["winner_id"]
        loser_id = result["loser_id"]
        score = result["score"]

        await state.clear()
        loser_state = FSMContext(
            storage=state.storage,
            key=StorageKey(bot_id=bot.id, chat_id=loser_id, user_id=loser_id)
        )
        await loser_state.clear()

        await message.answer(
            pvp_win_text(footballer, score),
            parse_mode="Markdown",
            reply_markup=play_again_pvp_keyboard()
        )
        winner_name = message.from_user.first_name or "Соперник"
        try:
            await bot.send_message(
                loser_id,
                pvp_lose_text(footballer, winner_name),
                parse_mode="Markdown",
                reply_markup=play_again_pvp_keyboard()
            )
        except Exception:
            pass
        return

    next_turn = result["next_turn"]
    clubs_shown = result["clubs_shown"]
    clubs_text = get_clubs_so_far(footballer, clubs_shown)

    # Конец игры — оба ответили на последний клуб и не угадали
    if result.get("game_over"):
        await state.clear()
        opp_state = FSMContext(
            storage=state.storage,
            key=StorageKey(bot_id=bot.id, chat_id=next_turn, user_id=next_turn)
        )
        await opp_state.clear()

        await message.answer(
            pvp_draw_text(footballer),
            parse_mode="Markdown",
            reply_markup=play_again_pvp_keyboard()
        )
        try:
            await bot.send_message(
                next_turn,
                pvp_draw_text(footballer),
                parse_mode="Markdown",
                reply_markup=play_again_pvp_keyboard()
            )
        except Exception:
            pass
        return

    # Не угадал — передаём ход
    await message.answer("❌ Не угадал! Ход переходит к сопернику...")

    try:
        await bot.send_message(
            next_turn,
            pvp_your_turn_text(clubs_text, clubs_shown),
            parse_mode="Markdown",
            reply_markup=pvp_game_keyboard(room_code)
        )
    except Exception as e:
        print("Ошибка передачи хода: " + str(e))


@router.callback_query(F.data.startswith("pvp_giveup:"))
async def handle_pvp_giveup(callback: CallbackQuery, state: FSMContext, bot: Bot):
    room_code = callback.data.split(":")[1]
    session = await get_session(room_code)
    if not session:
        await callback.answer("Игра уже завершена")
        return

    from data.footballers import get_footballer_by_id
    footballer = get_footballer_by_id(session["footballer_id"])
    name = footballer["name"]

    opponent_id = (
        session["player2_id"]
        if callback.from_user.id == session["player1_id"]
        else session["player1_id"]
    )

    await update_session(room_code, status="finished", winner_id=opponent_id)
    from database.db import update_user_stats
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

    await callback.message.edit_text(
        "🏳️ Ты сдался!\n\nЭто был *" + name + "*",
        parse_mode="Markdown",
        reply_markup=play_again_pvp_keyboard()
    )

    giver_name = callback.from_user.first_name or "Соперник"
    try:
        await bot.send_message(
            opponent_id,
            "🏆 *" + giver_name + "* сдался! Ты победил!\n\nЭто был *" + name + "*",
            parse_mode="Markdown",
            reply_markup=play_again_pvp_keyboard()
        )
    except Exception:
        pass

    await callback.answer()