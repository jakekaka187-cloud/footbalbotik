import random
from typing import Optional


# ─── Welcome & Menu ──────────────────────────────────────────────────────────

WELCOME_MESSAGES = [
    "🔥 Йоу, {name}! Готов показать, что ты реально разбираешься в футболе?\n\n"
    "Угадывай футболистов по клубам — чем быстрее, тем больше очков! 💪",

    "⚽ Хей, {name}! Время проверить свои знания!\n\n"
    "Я буду называть клубы, а ты угадываешь футболиста. Поехали? 🚀",

    "🏆 {name}, добро пожаловать в футбольную викторину!\n\n"
    "Тут всё по-честному — только знания и скорость реакции. Готов? 🎯",
]

def welcome_text(name: str) -> str:
    return random.choice(WELCOME_MESSAGES).format(name=name)


MENU_TEXT = (
    "🏠 *Главное меню*\n\n"
    "⚽ *Угадай карьеру соло* — угадывай футболистов по клубам\n"
    "👥 *Угадай карьеру с другом* — сразись с другом напрямую\n"
    "🏟️ *Угадай клуб* — угадай клуб по национальностям игроков\n"
    "📊 *Мой профиль* — статистика и рейтинг\n"
    "🏆 *Топ игроков* — кто лучший?"
)


# ─── Solo game messages ───────────────────────────────────────────────────────

def solo_start_text(footballer: dict, club_display: str) -> str:
    max_clubs = len(footballer["clubs"])
    return (
        f"🎮 *Новая игра началась!*\n\n"
        f"Я загадал футболиста. Угадывай по клубам!\n"
        f"Всего клубов в карьере: {max_clubs}\n\n"
        f"📍 *Клуб №1:*\n{club_display}\n\n"
        f"Напиши имя футболиста или нажми «Следующая подсказка» ⬇️"
    )


def solo_wrong_answer_texts() -> list:
    return [
        "❌ Не угадал! Даю следующий клуб...",
        "🤔 Не то... Ещё одна зацепка:",
        "😅 Мимо! Смотри внимательнее:",
        "⚡ Нет! Но я верю в тебя, вот ещё подсказка:",
    ]


def solo_next_club_text(clubs_so_far: str, clubs_shown: int, max_clubs: int) -> str:
    return (
        f"📋 *Карьера этого игрока ({clubs_shown}/{max_clubs}):*\n\n"
        f"{clubs_so_far}\n\n"
        f"Кто это? Пиши имя! 👇"
    )


def solo_win_text(footballer: dict, score: int, clubs_shown: int) -> str:
    if clubs_shown == 1:
        intro = "🤩 НЕВЕРОЯТНО! С первого клуба!"
    elif clubs_shown <= 2:
        intro = "🔥 ОГОНЬ! Быстрее некуда!"
    elif clubs_shown <= 3:
        intro = "💪 Красавчик! Хорошая реакция!"
    else:
        intro = "✅ Верно! Добрался до ответа!"

    return (
        f"{intro}\n\n"
        f"⚽ *{footballer['name']}*\n"
        f"{footballer['nationality']} | {footballer['position']}\n\n"
        f"🏆 *+{score} очков!*\n"
        f"📍 Угадал за {clubs_shown} {'клуб' if clubs_shown == 1 else 'клуба' if clubs_shown <= 4 else 'клубов'}"
    )


def solo_lose_text(footballer: dict) -> str:
    return (
        f"😔 Не угадал... Это был:\n\n"
        f"⚽ *{footballer['name']}*\n"
        f"{footballer['nationality']} | {footballer['position']}\n\n"
        f"💡 Факт: {footballer.get('hint_text', 'Отличный игрок!')}\n\n"
        f"Попробуй ещё раз! 💪"
    )


def solo_giveup_text(footballer: dict) -> str:
    return (
        f"🏳️ Сдался, бывает...\n\n"
        f"Правильный ответ: *{footballer['name']}*\n"
        f"{footballer['nationality']} | {footballer['position']}\n\n"
        f"💡 {footballer.get('hint_text', '')}\n\n"
        f"Давай сыграем ещё! 🔄"
    )


# ─── PvP messages ────────────────────────────────────────────────────────────

def pvp_room_created_text(room_code: str) -> str:
    return (
        f"🎮 *Комната создана!*\n\n"
        f"Код комнаты: `{room_code}`\n\n"
        f"Отправь этот код другу — пусть напишет мне /join {room_code}\n"
        f"Или просто перешли это сообщение 👆\n\n"
        f"⏳ Жду соперника..."
    )


def pvp_joined_text(host_name: str) -> str:
    return (
        f"🔥 Соперник найден!\n\n"
        f"Ты играешь против *{host_name}*\n\n"
        f"Правила: по очереди называете клубы, кто первый угадает — тот победил!\n"
        f"Первым ходит хозяин комнаты."
    )


def pvp_your_turn_text(clubs_so_far: str, clubs_shown: int) -> str:
    return (
        f"👉 *ТВОЙ ХОД!*\n\n"
        f"📋 Клубы этого игрока ({clubs_shown}):\n\n"
        f"{clubs_so_far}\n\n"
        f"Напиши имя футболиста! 🎯"
    )


def pvp_opponent_turn_text(clubs_so_far: str, clubs_shown: int) -> str:
    return (
        f"⏳ Ход соперника...\n\n"
        f"📋 Клубы ({clubs_shown}):\n\n"
        f"{clubs_so_far}\n\n"
        f"Следи за игрой!"
    )


def pvp_win_text(footballer: dict, score: int) -> str:
    return (
        f"🏆 *ТЫ ПОБЕДИЛ!*\n\n"
        f"⚽ Это был *{footballer['name']}*\n"
        f"{footballer['nationality']} | {footballer['position']}\n\n"
        f"🔥 *+{score} очков!*\n"
        f"Красавчик, показал класс! 💪"
    )


def pvp_lose_text(footballer: dict, winner_name: str) -> str:
    return (
        f"😤 Соперник оказался быстрее...\n\n"
        f"*{winner_name}* угадал правильно!\n"
        f"Это был *{footballer['name']}*\n\n"
        f"Следующий раз будет твоим! 🔄"
    )


def pvp_draw_text(footballer: dict) -> str:
    return (
        f"🤝 Никто не угадал...\n\n"
        f"Это был *{footballer['name']}*\n"
        f"{footballer['nationality']} | {footballer['position']}\n\n"
        f"💡 {footballer.get('hint_text', '')}"
    )


# ─── Profile ─────────────────────────────────────────────────────────────────

def profile_text(user) -> str:
    win_rate = 0
    if user.games_played > 0:
        win_rate = round(user.games_won / user.games_played * 100)

    streak_emoji = "🔥" if user.current_streak >= 3 else "⚡" if user.current_streak > 0 else "💤"

    return (
        f"📊 *Профиль игрока*\n\n"
        f"👤 {user.first_name}\n\n"
        f"🎮 Игр сыграно: {user.games_played}\n"
        f"✅ Побед: {user.games_won}\n"
        f"❌ Поражений: {user.games_lost}\n"
        f"📈 Процент побед: {win_rate}%\n\n"
        f"💰 Всего очков: {user.total_score}\n"
        f"🏅 Лучший результат: {user.best_score} очков\n\n"
        f"{streak_emoji} Текущая серия: {user.current_streak}\n"
        f"🔝 Рекорд серии: {user.best_streak}"
    )


# ─── Leaderboard ─────────────────────────────────────────────────────────────

def leaderboard_text(rows: list) -> str:
    medals = ["🥇", "🥈", "🥉"]
    lines = ["🏆 *Топ игроков по очкам*\n"]
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i + 1}."
        name = row.get("username") or row.get("first_name", "Игрок")
        score = row["total_score"]
        wins = row["games_won"]
        lines.append(f"{medal} *{name}* — {score} очков ({wins} побед)")
    return "\n".join(lines)


# ─── Errors ──────────────────────────────────────────────────────────────────

ERROR_SESSION_NOT_FOUND = (
    "⚠️ Игра не найдена. Возможно, она уже завершилась.\n"
    "Начни новую игру! ⚽"
)

ERROR_NOT_YOUR_TURN = (
    "⏳ Подожди, сейчас ход соперника!"
)

ERROR_ROOM_NOT_FOUND = (
    "❌ Комната не найдена. Проверь код и попробуй снова.\n"
    "Или создай свою комнату! 🎮"
)

ERROR_CANT_JOIN_OWN = (
    "😅 Нельзя играть против себя! Позови друга."
)