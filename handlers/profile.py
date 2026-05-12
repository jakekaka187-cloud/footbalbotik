from aiogram import Router, F
from aiogram.types import Message

from database.db import get_or_create_user
from keyboards.keyboards import back_to_menu_keyboard
from utils.messages import profile_text

router = Router()


@router.message(F.text == "📊 Мой профиль")
async def cmd_profile(message: Message):
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    await message.answer(
        profile_text(user),
        parse_mode="Markdown",
        reply_markup=back_to_menu_keyboard()
    )