import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from aiogram import Bot
from aiogram.utils.web_app import safe_parse_webapp_init_data
from aiohttp import web

from config import BOT_TOKEN, COMPETITION_END_DATE, COMPETITION_MIN_DRAFTS, DEV_MODE
from database.db import get_or_create_user, get_leaderboard, get_competition_leaderboard
from services import draft_service, referral_service
from services.draft_service import DraftError
from utils.check_subscription import is_subscribed, CHANNEL_USERNAME

logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@web.middleware
async def auth_middleware(request: web.Request, handler):
    dev_user_id = request.headers.get("X-Dev-User-Id")
    if DEV_MODE and dev_user_id:
        # Local-only bypass so the app can be clicked through in a plain browser
        # without a real Telegram session. Never active unless DEV_MODE=1 is set.
        request["tg_user"] = SimpleNamespace(
            id=int(dev_user_id), username=None,
            first_name=request.headers.get("X-Dev-Name", f"Тестер {dev_user_id}"),
        )
        request["start_param"] = request.headers.get("X-Dev-Start-Param") or None
    else:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("tma "):
            return web.json_response({"error": "Missing Telegram init data"}, status=401)

        init_data = auth_header[len("tma "):]
        try:
            parsed = safe_parse_webapp_init_data(BOT_TOKEN, init_data)
        except ValueError:
            return web.json_response({"error": "Invalid init data signature"}, status=401)

        if not parsed.user:
            return web.json_response({"error": "No user in init data"}, status=401)

        request["tg_user"] = parsed.user
        request["start_param"] = parsed.start_param

    try:
        return await handler(request)
    except DraftError as e:
        return web.json_response({"error": e.message}, status=e.status)


def _user_public_dict(user) -> dict:
    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "total_score": user.total_score,
        "season_score": user.season_score,
        "games_played": user.games_played,
        "referral_count": user.referral_count,
    }


async def handle_auth(request: web.Request) -> web.Response:
    tg_user = request["tg_user"]
    start_param = request["start_param"]
    bot: Bot = request.app["bot"]

    user = await get_or_create_user(
        telegram_id=tg_user.id, username=tg_user.username, first_name=tg_user.first_name
    )
    await referral_service.apply_start_param(tg_user.id, start_param, bot=bot)
    user = await get_or_create_user(
        telegram_id=tg_user.id, username=tg_user.username, first_name=tg_user.first_name
    )
    subscribed = True if DEV_MODE else await is_subscribed(bot, tg_user.id)

    return web.json_response({
        "user": _user_public_dict(user),
        "start_param": start_param,
        "subscribed": subscribed,
        "channel_username": CHANNEL_USERNAME,
    })


async def _require_subscribed(request: web.Request) -> Optional[web.Response]:
    """Hard server-side gate for endpoints that start/join a game — the frontend's
    GateScreen is only a UX nicety and can be bypassed by calling the API directly."""
    if DEV_MODE:
        return None
    bot: Bot = request.app["bot"]
    tg_user = request["tg_user"]
    if not await is_subscribed(bot, tg_user.id):
        return web.json_response(
            {"error": "Нужна подписка на канал, чтобы играть", "code": "not_subscribed",
             "channel_username": CHANNEL_USERNAME},
            status=403,
        )
    return None


async def handle_create_solo(request: web.Request) -> web.Response:
    if (err := await _require_subscribed(request)) is not None:
        return err
    tg_user = request["tg_user"]
    result = await draft_service.create_solo_session(tg_user.id)
    return web.json_response(result, status=201)


async def handle_create_pvp(request: web.Request) -> web.Response:
    if (err := await _require_subscribed(request)) is not None:
        return err
    tg_user = request["tg_user"]
    from config import BOT_USERNAME, WEBAPP_SHORT_NAME
    result = await draft_service.create_pvp_room(tg_user.id)
    result["invite_link"] = f"https://t.me/{BOT_USERNAME}/{WEBAPP_SHORT_NAME}?startapp={result['room_code']}"
    return web.json_response(result, status=201)


async def handle_join_pvp(request: web.Request) -> web.Response:
    if (err := await _require_subscribed(request)) is not None:
        return err
    tg_user = request["tg_user"]
    room_code = request.match_info["room_code"].upper()
    result = await draft_service.join_pvp_room(room_code, tg_user.id)
    return web.json_response(result)


async def handle_get_state(request: web.Request) -> web.Response:
    tg_user = request["tg_user"]
    session_id = request.match_info["session_id"].upper()
    result = await draft_service.get_session_state(session_id, tg_user.id)
    return web.json_response(result)


async def handle_reveal(request: web.Request) -> web.Response:
    tg_user = request["tg_user"]
    session_id = request.match_info["session_id"].upper()
    result = await draft_service.reveal_candidate(session_id, tg_user.id)
    return web.json_response(result)


async def handle_decide(request: web.Request) -> web.Response:
    tg_user = request["tg_user"]
    session_id = request.match_info["session_id"].upper()
    body = await request.json() if request.can_read_body else {}
    action = body.get("action")
    result = await draft_service.decide_candidate(session_id, tg_user.id, action)
    return web.json_response(result)


async def handle_result(request: web.Request) -> web.Response:
    tg_user = request["tg_user"]
    session_id = request.match_info["session_id"].upper()
    result = await draft_service.get_finished_result(session_id, tg_user.id)
    return web.json_response(result)


async def handle_leaderboard(request: web.Request) -> web.Response:
    scope = request.query.get("scope", "season")
    limit = min(int(request.query.get("limit", 10)), 50)
    if scope == "alltime":
        rows = await get_leaderboard(limit=limit)
        rows = [{"telegram_id": r["telegram_id"], "username": r["username"],
                  "first_name": r["first_name"], "score": r["total_score"],
                  "drafts_completed": r["games_played"]} for r in rows]
    else:
        rows = await get_competition_leaderboard(limit=limit)
        rows = [{"telegram_id": r["telegram_id"], "username": r["username"],
                  "first_name": r["first_name"], "score": r["season_score"],
                  "drafts_completed": r["season_wins"]} for r in rows]
    return web.json_response({
        "scope": scope,
        "rows": rows,
        "competition_end_date": COMPETITION_END_DATE,
        "competition_min_drafts": COMPETITION_MIN_DRAFTS,
    })


def create_api_app(bot: Bot) -> web.Application:
    api = web.Application(middlewares=[auth_middleware])
    api["bot"] = bot
    api.router.add_post("/auth", handle_auth)
    api.router.add_post("/draft/solo", handle_create_solo)
    api.router.add_post("/draft/pvp", handle_create_pvp)
    api.router.add_post("/draft/pvp/{room_code}/join", handle_join_pvp)
    api.router.add_get("/draft/{session_id}", handle_get_state)
    api.router.add_post("/draft/{session_id}/reveal", handle_reveal)
    api.router.add_post("/draft/{session_id}/decide", handle_decide)
    api.router.add_get("/draft/{session_id}/result", handle_result)
    api.router.add_get("/leaderboard", handle_leaderboard)
    return api


async def handle_index(request: web.Request) -> web.Response:
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.exists():
        return web.Response(text="Frontend build not found — run `npm run build` in frontend/", status=503)
    return web.FileResponse(index_file)


def create_app(bot: Bot) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.add_subapp("/api", create_api_app(bot))
    app.router.add_get("/", handle_index)
    if FRONTEND_DIST.exists():
        app.router.add_static("/", FRONTEND_DIST, show_index=False)
    return app
