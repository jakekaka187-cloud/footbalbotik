from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import WEBAPP_URL


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🎮 Мини-игры ЧМ 2026", web_app=WebAppInfo(url=WEBAPP_URL)),
    )
    builder.row(
        KeyboardButton(text="⚽ Угадай карьеру соло"),
        KeyboardButton(text="👥 Угадай карьеру с другом"),
    )
    builder.row(
        KeyboardButton(text="🏟️ Угадай клуб"),
        KeyboardButton(text="💱 Угадай трансфер"),
    )
    builder.row(
        KeyboardButton(text="📊 Мой профиль"),
        KeyboardButton(text="🏆 Топ игроков"),
    )
    builder.row(
        KeyboardButton(text="🔗 Пригласить друга"),
    )
    return builder.as_markup(resize_keyboard=True)


def solo_game_keyboard(session_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💡 Следующая подсказка", callback_data=f"skip:{session_id}"),
        InlineKeyboardButton(text="🏳️ Сдаться", callback_data=f"giveup:{session_id}"),
    )
    return builder.as_markup()


def pvp_join_keyboard(room_code: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🟢 Принять вызов!",
            callback_data=f"join_pvp:{room_code}"
        )
    )
    return builder.as_markup()


def pvp_game_keyboard(room_code: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🏳️ Сдаться", callback_data=f"pvp_giveup:{room_code}"),
    )
    return builder.as_markup()


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu"))
    return builder.as_markup()


def play_again_solo_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚽ Ещё раз!", callback_data="play_again_solo"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def transfer_game_keyboard(transfer_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💡 Подсказка", callback_data=f"transfer_hint:{transfer_id}"),
        InlineKeyboardButton(text="🏳️ Сдаться", callback_data=f"transfer_giveup:{transfer_id}"),
    )
    return builder.as_markup()


def play_again_transfer_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💱 Ещё раз!", callback_data="transfer_play_again"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def leaderboard_keyboard(mode: str = "season") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    tabs = []
    if mode != "season":
        tabs.append(InlineKeyboardButton(text="🏆 Конкурс", callback_data="leaderboard_season"))
    if mode != "alltime":
        tabs.append(InlineKeyboardButton(text="🕐 Все времена", callback_data="leaderboard_alltime"))
    if mode != "webapp":
        tabs.append(InlineKeyboardButton(text="🎮 Мини-игры ЧМ", callback_data="leaderboard_webapp"))
    builder.row(*tabs)
    builder.row(
        InlineKeyboardButton(text="📊 Таблица очков", callback_data="scoring_rules"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def ref_webapp_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎮 Открыть Мини-игры ЧМ 2026", web_app=WebAppInfo(url=WEBAPP_URL)))
    return builder.as_markup()


def scoring_rules_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🏆 Конкурс", callback_data="leaderboard_season"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return builder.as_markup()


def play_again_pvp_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Новая дуэль!", callback_data="play_again_pvp"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return builder.as_markup()