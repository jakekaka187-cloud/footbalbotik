import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot")  # без @, нужен для реф-ссылок и deep link'ов
ADMIN_ID = 724703528
DATABASE_URL = os.getenv("DATABASE_URL", "football_bot.db")

# Web server (Mini App backend)
PORT = int(os.getenv("PORT", 8000))
WEBAPP_URL = os.getenv("WEBAPP_URL", "")  # публичный HTTPS-адрес мини-аппы, из Railway
WEBAPP_SHORT_NAME = os.getenv("WEBAPP_SHORT_NAME", "")  # short name мини-аппы, из BotFather

# Local dev only — NEVER set these in production (Railway)
DEV_MODE = os.getenv("DEV_MODE", "0") == "1"  # bypasses Telegram initData signature check
DISABLE_POLLING = os.getenv("DISABLE_POLLING", "0") == "1"  # run web server without bot polling

# Draft game
DRAFT_FORMATION = ["GK", "DEF", "MID1", "MID2", "FWD"]
SLOT_POSITION = {
    "GK": "Вратарь",
    "DEF": "Защитник",
    "MID1": "Полузащитник",
    "MID2": "Полузащитник",
    "FWD": "Нападающий",
}

# Competition
COMPETITION_END_DATE = "01.06.2026"
COMPETITION_MIN_DRAFTS = 3

# PvP settings
PVP_ROOM_EXPIRY_SECONDS = 600
