import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import config
from database import db
from handlers import user_router, admin_router, tracker_router
from middlewares import ThrottlingMiddleware, AuthMiddleware
from utils import logger

async def on_startup():
    logger.info("Bot starting...")
    await db.connect()
    logger.info("Database initialized")

async def on_shutdown():
    logger.info("Bot shutting down...")
    await db.close()

async def main():
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    dp.message.middleware(ThrottlingMiddleware())
    dp.message.middleware(AuthMiddleware())
    
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(tracker_router)
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    try:
        logger.info("Bot started successfully")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Critical error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)