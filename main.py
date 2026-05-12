import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from handlers import common, game_solo, game_pvp, profile, leaderboard, game_clubs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Init DB
    await init_db()

    # Register routers
    dp.include_router(common.router)
    dp.include_router(game_solo.router)
    dp.include_router(game_pvp.router)
    dp.include_router(profile.router)
    dp.include_router(leaderboard.router)
    dp.include_router(game_clubs.router)

    logger.info("Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())