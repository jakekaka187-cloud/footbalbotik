from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.db import get_or_create_user
from keyboards.keyboards import main_menu_keyboard, back_to_menu_keyboard
from utils.messages import welcome_text, MENU_TEXT
from utils.check_subscription import check_subscription, is_subscribed

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    subscribed = await check_subscription(bot, message)
    if not subscribed:
        return

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    await message.answer(
        welcome_text(user.first_name),
        reply_markup=main_menu_keyboard()
    )
    await message.answer(MENU_TEXT, parse_mode="Markdown")


@router.message(Command("menu"))
@router.message(F.text == "🏠 В главное меню")
async def cmd_menu(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    subscribed = await check_subscription(bot, message)
    if not subscribed:
        return

    await message.answer(MENU_TEXT, parse_mode="Markdown", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery, state: FSMContext, bot: Bot):
    subscribed = await is_subscribed(bot, callback.from_user.id)

    if subscribed:
        await callback.answer("✅ Подписка подтверждена!", show_alert=True)
        user = await get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name
        )
        await callback.message.answer(
            welcome_text(user.first_name),
            reply_markup=main_menu_keyboard()
        )
        await callback.message.answer(MENU_TEXT, parse_mode="Markdown")
    else:
        await callback.answer(
            "❌ Ты ещё не подписан! Подпишись и попробуй снова.",
            show_alert=True
        )


@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()

    subscribed = await is_subscribed(bot, callback.from_user.id)
    if not subscribed:
        await check_subscription(bot, callback)
        return

    await callback.message.edit_text(MENU_TEXT, parse_mode="Markdown")
    await callback.message.answer("👆 Выбирай!", reply_markup=main_menu_keyboard())
    await callback.answer()