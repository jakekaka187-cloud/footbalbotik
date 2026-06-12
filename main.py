import asyncio
import json
import logging
import os
from pathlib import Path

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.db import init_db
from handlers import common, game_solo, game_pvp, profile, leaderboard, game_clubs, game_transfers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

WEBAPP_DIR = Path(__file__).parent / "webapp"


async def webapp_handler(request: web.Request) -> web.Response:
    path = request.match_info.get("path", "index.html") or "index.html"
    file_path = WEBAPP_DIR / path
    if not file_path.exists() or not file_path.is_file():
        file_path = WEBAPP_DIR / "index.html"
    content_types = {
        ".html": "text/html; charset=utf-8",
        ".css":  "text/css; charset=utf-8",
        ".js":   "application/javascript; charset=utf-8",
        ".png":  "image/png",
        ".jpg":  "image/jpeg",
        ".svg":  "image/svg+xml",
        ".ico":  "image/x-icon",
    }
    ct = content_types.get(file_path.suffix, "application/octet-stream")
    return web.Response(body=file_path.read_bytes(), content_type=ct.split(";")[0].strip(),
                        headers={"charset": "utf-8"} if "charset" in ct else {})


async def health_handler(request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def start_web_server() -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/",             health_handler)
    app.router.add_get("/health",       health_handler)
    app.router.add_get("/webapp",       webapp_handler)
    app.router.add_get("/webapp/",      webapp_handler)
    app.router.add_get("/webapp/{path:.*}", webapp_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web server started on port {port}")
    return runner


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await init_db()

    dp.include_router(common.router)
    dp.include_router(game_solo.router)
    dp.include_router(game_pvp.router)
    dp.include_router(profile.router)
    dp.include_router(leaderboard.router)
    dp.include_router(game_clubs.router)
    dp.include_router(game_transfers.router)

    runner = await start_web_server()
    logger.info("Bot started!")

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
