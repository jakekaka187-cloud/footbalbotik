from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import BOT_USERNAME, ADMIN_ID, WEBAPP_URL, COMPETITION_MIN_DRAFTS
from database.db import get_or_create_user, get_user, get_referral_stats, get_bot_stats, get_competition_leaderboard
from keyboards.keyboards import webapp_open_keyboard
from services.referral_service import apply_start_param, REFERRAL_BONUS
from utils.check_subscription import check_subscription, is_subscribed

router = Router()

WELCOME_TEXT = (
    "⚽ *Футбольный драфт*\n\n"
    "Собери мечту-состав из 5 игроков: вратарь, защитник, 2 полузащитника и нападающий.\n"
    "На каждой позиции тебе покажут игрока — бери его или замени на другого (только один раз!).\n\n"
    "Играй один или позови друга — жми кнопку ниже 👇"
)


async def _send_open_app(message: Message, first_name: str):
    if not WEBAPP_URL:
        await message.answer(
            WELCOME_TEXT + "\n\n⚠️ Мини-приложение ещё не настроено (WEBAPP_URL).",
            parse_mode="Markdown",
        )
        return
    await message.answer(WELCOME_TEXT, parse_mode="Markdown", reply_markup=webapp_open_keyboard(WEBAPP_URL))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    subscribed = await check_subscription(bot, message)
    if not subscribed:
        return

    args = message.text.split(maxsplit=1)
    start_param = args[1] if len(args) > 1 else None

    existing = await get_user(message.from_user.id)
    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    if existing is None:
        await apply_start_param(message.from_user.id, start_param, bot=bot)

    await _send_open_app(message, user.first_name)


@router.message(Command("ref"))
async def cmd_ref(message: Message):
    stats = await get_referral_stats(message.from_user.id)
    count = stats.get("referral_count", 0)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{message.from_user.id}"
    await message.answer(
        f"🔗 *Твоя реферальная ссылка:*\n\n"
        f"`{link}`\n\n"
        f"За каждого нового друга, который зарегистрируется по ней, "
        f"ты получаешь *+{REFERRAL_BONUS} очков* в конкурс!\n\n"
        f"👥 Приглашено друзей: *{count}*\n"
        f"💰 Заработано на рефералах: *{count * REFERRAL_BONUS} очков*",
        parse_mode="Markdown",
    )


@router.message(Command("top"))
async def cmd_top(message: Message):
    rows = await get_competition_leaderboard(limit=10)
    if not rows:
        await message.answer(
            f"Пока никто не набрал {COMPETITION_MIN_DRAFTS}+ завершённых драфтов. Открой приложение и сыграй первым!"
        )
        return
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i + 1}."
        name = row.get("username") or row.get("first_name", "Игрок")
        lines.append(f"{medal} {name} — {row['season_score']} оч.")
    await message.answer("🏆 *Топ конкурса:*\n\n" + "\n".join(lines), parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    s = await get_bot_stats()
    medals = ["🥇", "🥈", "🥉"]
    top_lines = []
    for i, row in enumerate(s["top3"]):
        name = row.get("username") or row.get("first_name", "Игрок")
        top_lines.append(f"{medals[i]} {name} — {row['season_score']} оч. ({row['season_wins']} драфтов)")

    top_text = "\n".join(top_lines) if top_lines else "Пока никто не играл"

    await message.answer(
        f"📊 *Статистика бота*\n\n"
        f"👥 Всего пользователей: *{s['total_users']}*\n"
        f"🕐 Активных сегодня: *{s['active_today']}*\n"
        f"📅 Активных за неделю: *{s['active_week']}*\n"
        f"🎮 Драфтов завершено: *{s['total_games']}*\n"
        f"🔗 Пришли по реф-ссылке: *{s['total_referrals']}*\n\n"
        f"🏆 *Топ конкурса:*\n{top_text}",
        parse_mode="Markdown",
    )


@router.callback_query(F.data == "check_sub")
async def cb_check_sub(callback: CallbackQuery, state: FSMContext, bot: Bot):
    subscribed = await is_subscribed(bot, callback.from_user.id)

    if subscribed:
        await callback.answer("✅ Подписка подтверждена!", show_alert=True)
        user = await get_or_create_user(
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )
        await _send_open_app(callback.message, user.first_name)
    else:
        await callback.answer(
            "❌ Ты ещё не подписан! Подпишись и попробуй снова.",
            show_alert=True,
        )
