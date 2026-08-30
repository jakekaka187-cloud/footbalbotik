import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

from config import BOT_TOKEN, PORT, DISABLE_POLLING
from database.db import init_db
from handlers import common
from webapp.api import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_web_server(bot: Bot):
    app = create_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Web server started on 0.0.0.0:{PORT}")
    await asyncio.Event().wait()


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await init_db()

    dp.include_router(common.router)

    if DISABLE_POLLING:
        logger.info("DISABLE_POLLING=1 — running web server only (local dev mode)")
        await run_web_server(bot)
    else:
        logger.info("Bot started!")
        await asyncio.gather(
            dp.start_polling(bot),
            run_web_server(bot),
        )


if __name__ == "__main__":
    asyncio.run(main())
