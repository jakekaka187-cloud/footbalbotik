from aiogram import Bot
from aiogram.types import Message, CallbackQuery


CHANNEL_USERNAME = "@oldjacksons"


async def is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


async def check_subscription(bot: Bot, event) -> bool:
    """Проверяет подписку и отправляет сообщение если не подписан."""
    if isinstance(event, (Message, CallbackQuery)):
        user_id = event.from_user.id
    else:
        return False

    subscribed = await is_subscribed(bot, user_id)

    if not subscribed:
        text = (
            "🔒 *Доступ закрыт!*\n\n"
            "Чтобы играть — подпишись на наш канал:\n"
            "👉 @oldjacksons\n\n"
            "После подписки нажми /start"
        )
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="📢 Подписаться",
            url="https://t.me/oldjacksons"
        ))
        builder.add(InlineKeyboardButton(
            text="✅ Я подписался",
            callback_data="check_sub"
        ))

        if isinstance(event, Message):
            await event.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())
        elif isinstance(event, CallbackQuery):
            await event.message.answer(text, parse_mode="Markdown", reply_markup=builder.as_markup())
            await event.answer()

    return subscribed