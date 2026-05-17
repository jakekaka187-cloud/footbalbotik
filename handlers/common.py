from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import BOT_USERNAME, ADMIN_ID
from database.db import get_or_create_user, apply_referral, get_referral_stats, get_bot_stats
from keyboards.keyboards import main_menu_keyboard, back_to_menu_keyboard
from utils.messages import welcome_text, MENU_TEXT
from utils.check_subscription import check_subscription, is_subscribed

router = Router()

REFERRAL_BONUS = 1500


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()

    subscribed = await check_subscription(bot, message)
    if not subscribed:
        return

    # Detect referral parameter: /start ref_123456
    args = message.text.split(maxsplit=1)
    ref_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1][4:])
        except ValueError:
            ref_id = None

    is_new = False
    from database.db import get_user
    existing = await get_user(message.from_user.id)
    if existing is None:
        is_new = True

    user = await get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    # Apply referral bonus if this is a new user joining via ref link
    if is_new and ref_id:
        bonus_given = await apply_referral(message.from_user.id, ref_id)
        if bonus_given:
            try:
                await bot.send_message(
                    ref_id,
                    f"🎉 По твоей ссылке зарегистрировался новый игрок!\n\n"
                    f"💰 *+{REFERRAL_BONUS} очков* начислено на твой счёт! 🔥",
                    parse_mode="Markdown",
                )
            except Exception:
                pass

    await message.answer(
        welcome_text(user.first_name),
        reply_markup=main_menu_keyboard(),
    )
    await message.answer(MENU_TEXT, parse_mode="Markdown")


@router.message(Command("ref"))
@router.message(F.text == "🔗 Пригласить друга")
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


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    s = await get_bot_stats()
    medals = ["🥇", "🥈", "🥉"]
    top_lines = []
    for i, row in enumerate(s["top3"]):
        name = row.get("username") or row.get("first_name", "Игрок")
        top_lines.append(f"{medals[i]} {name} — {row['season_score']} оч. ({row['season_wins']} побед)")

    top_text = "\n".join(top_lines) if top_lines else "Пока никто не играл"

    await message.answer(
        f"📊 *Статистика бота*\n\n"
        f"👥 Всего пользователей: *{s['total_users']}*\n"
        f"🕐 Активных сегодня: *{s['active_today']}*\n"
        f"📅 Активных за неделю: *{s['active_week']}*\n"
        f"🎮 Всего игр сыграно: *{s['total_games']}*\n"
        f"🔗 Пришли по реф-ссылке: *{s['total_referrals']}*\n\n"
        f"🏆 *Топ конкурса:*\n{top_text}",
        parse_mode="Markdown",
    )


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
            first_name=callback.from_user.first_name,
        )
        await callback.message.answer(
            welcome_text(user.first_name),
            reply_markup=main_menu_keyboard(),
        )
        await callback.message.answer(MENU_TEXT, parse_mode="Markdown")
    else:
        await callback.answer(
            "❌ Ты ещё не подписан! Подпишись и попробуй снова.",
            show_alert=True,
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
