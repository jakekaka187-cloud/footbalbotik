import random
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from data.transfers import TRANSFERS, get_transfer_by_id, get_all_transfer_ids, format_amount
from database.db import update_user_stats
from keyboards.keyboards import transfer_game_keyboard, play_again_transfer_keyboard, main_menu_keyboard
from utils.states import TransferGameStates

router = Router()

SCORES = {1: 100, 2: 60, 3: 30}

WRONG_TEXTS = [
    "❌ Не угадал! Даю подсказку...",
    "🤔 Не то... Ещё зацепка:",
    "😅 Мимо! Смотри внимательнее:",
    "⚡ Нет! Вот ещё подсказка:",
]


def check_answer(user_answer: str, transfer: dict) -> bool:
    ans = user_answer.strip().lower()
    name = transfer["name"].lower()
    if ans == name:
        return True
    parts = name.split()
    if len(parts) >= 2 and ans == parts[-1]:
        return True
    if len(parts) >= 2 and ans == parts[0]:
        return True
    if len(ans) >= 4 and ans in name:
        return True
    return False


def build_hint_text(transfer: dict, hints_shown: int, last_chance: bool = False) -> str:
    from_line = f"{transfer['from_emoji']} {transfer['from_club']}"
    to_line = f"{transfer['to_emoji']} {transfer['to_club']}"
    text = f"💱 *Угадай трансфер!*\n\n➡️ Откуда: {from_line}\n🏆 Куда: {to_line}"

    if hints_shown >= 2:
        text += f"\n📅 Сезон: {transfer['season']}"
    if hints_shown >= 3:
        text += f"\n💶 Сумма: ~{format_amount(transfer['amount'])} млн €"

    if last_chance:
        text += "\n\n⚠️ *Последняя попытка!* Кто это? 🎯"
    else:
        text += "\n\nКто этот игрок? Напиши имя! 👇"
    return text


@router.message(F.text == "💱 Угадай трансфер")
@router.callback_query(F.data == "transfer_play_again")
async def start_transfer_game(event, state: FSMContext, bot: Bot):
    await state.clear()
    is_callback = isinstance(event, CallbackQuery)
    user_id = event.from_user.id
    message = event.message if is_callback else event

    from utils.check_subscription import check_subscription
    subscribed = await check_subscription(bot, event)
    if not subscribed:
        return

    transfer_id = random.choice(get_all_transfer_ids())
    transfer = get_transfer_by_id(transfer_id)

    await state.set_state(TransferGameStates.waiting_for_guess)
    await state.update_data(transfer_id=transfer_id, hints_shown=1, last_chance=False)

    text = build_hint_text(transfer, hints_shown=1)

    if is_callback:
        await event.answer()
        await message.answer(text, parse_mode="Markdown", reply_markup=transfer_game_keyboard(transfer_id))
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=transfer_game_keyboard(transfer_id))


@router.message(TransferGameStates.waiting_for_guess)
async def handle_transfer_guess(message: Message, state: FSMContext):
    data = await state.get_data()
    transfer_id = data.get("transfer_id")
    hints_shown = data.get("hints_shown", 1)
    last_chance = data.get("last_chance", False)

    if not transfer_id:
        await message.answer("Начни новую игру!", reply_markup=main_menu_keyboard())
        await state.clear()
        return

    transfer = get_transfer_by_id(transfer_id)

    if check_answer(message.text, transfer):
        score = SCORES.get(hints_shown, 10)
        await update_user_stats(message.from_user.id, won=True, score=score)
        await state.clear()

        if hints_shown == 1:
            reaction = "🤯 ФЕНОМЕНАЛЬНО! С первой подсказки!"
        elif hints_shown == 2:
            reaction = "🔥 Отлично! Быстро разобрался!"
        else:
            reaction = "✅ Верно! Добрался до ответа!"

        await message.answer(
            f"{reaction}\n\n"
            f"💱 *{transfer['name']}*\n"
            f"{transfer['from_emoji']} {transfer['from_club']} → {transfer['to_emoji']} {transfer['to_club']}\n"
            f"📅 {transfer['season']} | 💶 ~{format_amount(transfer['amount'])} млн €\n\n"
            f"💰 *+{score} очков!*",
            parse_mode="Markdown",
            reply_markup=play_again_transfer_keyboard()
        )
        return

    if last_chance:
        await update_user_stats(message.from_user.id, won=False, score=0)
        await state.clear()
        await message.answer(
            f"😔 Не угадал... Это был:\n\n"
            f"💱 *{transfer['name']}*\n"
            f"{transfer['from_emoji']} {transfer['from_club']} → {transfer['to_emoji']} {transfer['to_club']}\n"
            f"📅 {transfer['season']} | 💶 ~{format_amount(transfer['amount'])} млн €\n\n"
            f"Попробуй ещё раз! 💪",
            parse_mode="Markdown",
            reply_markup=play_again_transfer_keyboard()
        )
        return

    await message.answer(random.choice(WRONG_TEXTS))

    new_hints = hints_shown + 1
    is_last = new_hints >= 3
    await state.update_data(hints_shown=new_hints, last_chance=is_last)

    text = build_hint_text(transfer, new_hints, last_chance=is_last)
    await message.answer(text, parse_mode="Markdown", reply_markup=transfer_game_keyboard(transfer_id))


@router.callback_query(F.data.startswith("transfer_hint:"))
async def handle_transfer_hint(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    hints_shown = data.get("hints_shown", 1)
    last_chance = data.get("last_chance", False)
    transfer_id = data.get("transfer_id")

    if last_chance:
        await callback.answer("⚠️ Это последняя подсказка! Напиши имя!", show_alert=True)
        return

    if hints_shown >= 3:
        await callback.answer("⚠️ Все подсказки уже открыты!", show_alert=True)
        return

    transfer = get_transfer_by_id(transfer_id)
    new_hints = hints_shown + 1
    is_last = new_hints >= 3
    await state.update_data(hints_shown=new_hints, last_chance=is_last)

    text = build_hint_text(transfer, new_hints, last_chance=is_last)
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=transfer_game_keyboard(transfer_id))
    await callback.answer("💡 Подсказка открыта!")


@router.callback_query(F.data.startswith("transfer_giveup:"))
async def handle_transfer_giveup(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    transfer_id = data.get("transfer_id")
    transfer = get_transfer_by_id(transfer_id)

    await update_user_stats(callback.from_user.id, won=False, score=0)
    await state.clear()

    await callback.message.edit_text(
        f"🏳️ Сдался!\n\n"
        f"Это был:\n💱 *{transfer['name']}*\n"
        f"{transfer['from_emoji']} {transfer['from_club']} → {transfer['to_emoji']} {transfer['to_club']}\n"
        f"📅 {transfer['season']} | 💶 ~{format_amount(transfer['amount'])} млн €",
        parse_mode="Markdown",
        reply_markup=play_again_transfer_keyboard()
    )
    await callback.answer()
