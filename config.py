import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "football_bot.db")

# Game settings
MAX_HINTS_BEFORE_PENALTY = 3       # After 3 clubs shown — reduced points
MAX_CLUBS_TOTAL = 15                # Max clubs to show before game ends
POINTS_TABLE = {
    1: 100,   # Guessed after 1 club
    2: 85,
    3: 70,
    4: 55,
    5: 40,
    6: 25,
    7: 15,
    8: 5,
}

# PvP settings
PVP_ROOM_EXPIRY_SECONDS = 600      # 10 minutes to join
PVP_TURN_TIMEOUT_SECONDS = 60      # 1 minute per turn