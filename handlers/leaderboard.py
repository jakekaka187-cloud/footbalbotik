from aiogram import Router, F
from aiogram.types import Message
from database.db import get_leaderboard
from keyboards.keyboards import back_to_menu_keyboard
from utils.messages import leaderboard_text

router = Router()

@router.message(F.text == "🏆 Топ игроков")
async def cmd_leaderboard(message: Message):
    rows = await get_leaderboard(10)
    await message.answer(
        leaderboard_text(rows),
        parse_mode="Markdown",
        reply_markup=back_to_menu_keyboard()
    )