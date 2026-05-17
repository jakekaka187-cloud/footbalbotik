import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot")  # без @, нужен для реф-ссылок
DATABASE_URL = os.getenv("DATABASE_URL", "football_bot.db")

# Game settings
MAX_HINTS_BEFORE_PENALTY = 3       # After 3 clubs shown — reduced points
MAX_CLUBS_TOTAL = 15                # Max clubs to show before game ends
# ── Scoring (all games normalized to same scale) ──────────────────────────────
# Career solo/PvP: points by clubs shown
POINTS_TABLE = {
    1: 100,
    2: 80,
    3: 60,
    4: 40,
    5: 20,
}
POINTS_DEFAULT = 10  # 6+ clubs shown

# Competition
COMPETITION_END_DATE = "01.06.2026"
COMPETITION_MIN_WINS = 3  # minimum wins to appear in competition leaderboard

# PvP settings
PVP_ROOM_EXPIRY_SECONDS = 600      # 10 minutes to join
PVP_TURN_TIMEOUT_SECONDS = 60      # 1 minute per turn