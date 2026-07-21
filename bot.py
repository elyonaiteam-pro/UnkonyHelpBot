"""VeyraSupport — Telegram support bot."""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db
from handlers import admin, user

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def health_check(request):
    """Health check endpoint for Render."""
    return web.Response(text="Bot is running", status=200)


async def start_http_server():
    """Start lightweight aiohttp server for Render health checks."""
    app = web.Application()
    app.router.add_get("/", health_check)
    
    port = int(os.getenv("PORT", "10000"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    logger.info("HTTP server started on 0.0.0.0:%d", port)
    return runner


async def main() -> None:
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN missing. Copy .env.example → .env and fill it in.")
        sys.exit(1)
    if not ADMIN_IDS:
        logger.error("ADMIN_IDS missing. Add your Telegram user ID to .env.")
        sys.exit(1)

    await init_db()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(admin.router)
    dp.include_router(user.router)

    logger.info("Bot started. Admins: %s", ADMIN_IDS)
    
    # Start HTTP server and polling concurrently
    http_runner = await start_http_server()
    try:
        await asyncio.gather(
            dp.start_polling(bot),
            asyncio.sleep(float('inf'))  # Keep HTTP server alive
        )
    finally:
        await http_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
