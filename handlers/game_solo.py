import random
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from services.game_service import (
    start_solo_game, process_solo_guess, skip_solo_club,
    give_up_solo, get_clubs_so_far, get_club_display, all_clubs_shown
)
from keyboards.keyboards import solo_game_keyboard, play_again_solo_keyboard, main_menu_keyboard
from utils.states import SoloGameStates
from utils.messages import (
    solo_start_text, solo_next_club_text, solo_win_text,
    solo_lose_text, solo_giveup_text, solo_wrong_answer_texts,
    ERROR_SESSION_NOT_FOUND
)

router = Router()


@router.message(F.text == "⚽ Угадай карьеру соло")
@router.callback_query(F.data == "play_again_solo")
async def start_solo(event, state: FSMContext, bot: Bot):
    await state.clear()
    is_callback = isinstance(event, CallbackQuery)
    user_id = event.from_user.id
    message = event.message if is_callback else event

    from utils.check_subscription import check_subscription
    subscribed = await check_subscription(bot, event)
    if not subscribed:
        return

    game = await start_solo_game(user_id)
    footballer = game["footballer"]
    session_id = game["session_id"]

    first_club = get_club_display(footballer, 0)
    await state.set_state(SoloGameStates.waiting_for_guess)
    await state.update_data(session_id=session_id, last_chance=False)

    from database.db import update_session
    await update_session(session_id, clubs_shown=1)

    text = solo_start_text(footballer, first_club)

    if is_callback:
        await event.answer()
        await message.answer(text, parse_mode="Markdown", reply_markup=solo_game_keyboard(session_id))
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=solo_game_keyboard(session_id))


@router.message(SoloGameStates.waiting_for_guess)
async def handle_solo_guess(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    last_chance = data.get("last_chance", False)

    if not session_id:
        await message.answer(ERROR_SESSION_NOT_FOUND, reply_markup=main_menu_keyboard())
        await state.clear()
        return

    if last_chance:
        from database.db import get_session, update_session, update_user_stats, save_game_history
        from services.game_service import check_answer, calculate_score
        from data.footballers import get_footballer_by_id

        session = await get_session(session_id)
        if not session or session["status"] != "active":
            await message.answer(ERROR_SESSION_NOT_FOUND, reply_markup=main_menu_keyboard())
            await state.clear()
            return

        footballer = get_footballer_by_id(session["footballer_id"])
        clubs_shown = session["clubs_shown"]

        if check_answer(message.text, footballer):
            score = calculate_score(clubs_shown)
            await update_session(session_id, status="finished", winner_id=message.from_user.id)
            await update_user_stats(message.from_user.id, won=True, score=score)
            await save_game_history(message.from_user.id, footballer["id"], clubs_shown, score, "win")
            await state.clear()
            await message.answer(
                solo_win_text(footballer, score, clubs_shown),
                parse_mode="Markdown",
                reply_markup=play_again_solo_keyboard()
            )
        else:
            await update_session(session_id, status="finished")
            await update_user_stats(message.from_user.id, won=False, score=0)
            await save_game_history(message.from_user.id, footballer["id"], clubs_shown, 0, "loss")
            await state.clear()
            await message.answer(
                solo_lose_text(footballer),
                parse_mode="Markdown",
                reply_markup=play_again_solo_keyboard()
            )
        return

    result = await process_solo_guess(session_id, message.from_user.id, message.text)

    if "error" in result:
        await message.answer(ERROR_SESSION_NOT_FOUND, reply_markup=main_menu_keyboard())
        await state.clear()
        return

    if result["correct"]:
        await state.clear()
        await message.answer(
            solo_win_text(result["footballer"], result["score"], result["clubs_shown"]),
            parse_mode="Markdown",
            reply_markup=play_again_solo_keyboard()
        )
        return

    footballer = result["footballer"]
    clubs_shown = result["clubs_shown"]
    max_clubs = len(footballer["clubs"])
    clubs_text = get_clubs_so_far(footballer, clubs_shown)

    if result.get("last_chance"):
        await state.update_data(last_chance=True)
        await message.answer(random.choice(solo_wrong_answer_texts()))
        await message.answer(
            f"⚠️ *Последний шанс!* Вот вся карьера ({clubs_shown}/{max_clubs}):\n\n"
            f"{clubs_text}\n\n"
            f"Кто это? Последняя попытка! 🎯",
            parse_mode="Markdown",
            reply_markup=solo_game_keyboard(session_id)
        )
        return

    await message.answer(random.choice(solo_wrong_answer_texts()))
    await message.answer(
        solo_next_club_text(clubs_text, clubs_shown, max_clubs),
        parse_mode="Markdown",
        reply_markup=solo_game_keyboard(session_id)
    )


@router.callback_query(F.data.startswith("skip:"))
async def handle_solo_skip(callback: CallbackQuery, state: FSMContext):
    session_id = callback.data.split(":")[1]

    # Если уже последний шанс — больше подсказок нет
    data = await state.get_data()
    if data.get("last_chance"):
        await callback.answer("⚠️ Это последний шанс! Напиши имя!", show_alert=True)
        return

    result = await skip_solo_club(session_id)

    if "error" in result:
        await callback.answer(ERROR_SESSION_NOT_FOUND)
        await state.clear()
        return

    footballer = result["footballer"]
    clubs_shown = result["clubs_shown"]
    max_clubs = len(footballer["clubs"])
    clubs_text = get_clubs_so_far(footballer, clubs_shown)

    if result.get("last_chance"):
        await state.update_data(last_chance=True)
        await callback.message.edit_text(
            f"⚠️ *Последний шанс!* Вот вся карьера ({clubs_shown}/{max_clubs}):\n\n"
            f"{clubs_text}\n\n"
            f"Кто это? Последняя попытка! 🎯",
            parse_mode="Markdown",
            reply_markup=solo_game_keyboard(session_id)
        )
        await callback.answer("⚠️ Последний шанс!")
        return

    await callback.message.edit_text(
        solo_next_club_text(clubs_text, clubs_shown, max_clubs),
        parse_mode="Markdown",
        reply_markup=solo_game_keyboard(session_id)
    )
    await callback.answer("💡 Подсказка добавлена!")


@router.callback_query(F.data.startswith("giveup:"))
async def handle_solo_giveup(callback: CallbackQuery, state: FSMContext):
    session_id = callback.data.split(":")[1]
    result = await give_up_solo(session_id, callback.from_user.id)

    await state.clear()
    footballer = result.get("footballer", {})
    if not footballer:
        await callback.answer(ERROR_SESSION_NOT_FOUND)
        return

    await callback.message.edit_text(
        solo_giveup_text(footballer),
        parse_mode="Markdown",
        reply_markup=play_again_solo_keyboard()
    )
    await callback.answer()