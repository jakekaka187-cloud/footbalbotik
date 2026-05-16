from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
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


def play_again_pvp_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👥 Новая дуэль!", callback_data="play_again_pvp"),
        InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu"),
    )
    return builder.as_markup()