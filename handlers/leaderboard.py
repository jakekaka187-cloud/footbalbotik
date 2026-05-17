from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.db import get_leaderboard, get_competition_leaderboard
from keyboards.keyboards import leaderboard_keyboard, scoring_rules_keyboard
from utils.messages import (
    competition_leaderboard_text, alltime_leaderboard_text, SCORING_RULES_TEXT
)
from config import COMPETITION_END_DATE, COMPETITION_MIN_WINS

router = Router()


@router.message(F.text == "🏆 Топ игроков")
async def cmd_leaderboard(message: Message):
    rows = await get_competition_leaderboard(10)
    await message.answer(
        competition_leaderboard_text(rows, COMPETITION_END_DATE, COMPETITION_MIN_WINS),
        parse_mode="Markdown",
        reply_markup=leaderboard_keyboard("season"),
    )


@router.callback_query(F.data == "leaderboard_season")
async def cb_leaderboard_season(callback: CallbackQuery):
    rows = await get_competition_leaderboard(10)
    await callback.message.edit_text(
        competition_leaderboard_text(rows, COMPETITION_END_DATE, COMPETITION_MIN_WINS),
        parse_mode="Markdown",
        reply_markup=leaderboard_keyboard("season"),
    )
    await callback.answer()


@router.callback_query(F.data == "leaderboard_alltime")
async def cb_leaderboard_alltime(callback: CallbackQuery):
    rows = await get_leaderboard(10)
    await callback.message.edit_text(
        alltime_leaderboard_text(rows),
        parse_mode="Markdown",
        reply_markup=leaderboard_keyboard("alltime"),
    )
    await callback.answer()


@router.callback_query(F.data == "scoring_rules")
async def cb_scoring_rules(callback: CallbackQuery):
    await callback.message.edit_text(
        SCORING_RULES_TEXT,
        parse_mode="Markdown",
        reply_markup=scoring_rules_keyboard(),
    )
    await callback.answer()
