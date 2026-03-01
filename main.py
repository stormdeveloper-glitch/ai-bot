# main.py
"""
╔══════════════════════════════════════════════════════╗
║         FRIEREN'S JOURNEY — Telegram Bot             ║
║         Senior-level architecture                    ║
╚══════════════════════════════════════════════════════╝

Buyruqlar:
  /start         — Boshlash / bosh menu
  /help          — Yordam
  /profile       — Profilingiz
  /card WW001    — Karta ma'lumoti
  /collection    — Koleksiyangiz
  /pull          — 1x pull (160 ⭐)
  /multipull     — 10x pull (1600 ⭐)
  /daily         — Kunlik sovg'a (60 ⭐)
  /top           — Top 10 reyting
  /admin         — Admin panel

Admin buyruqlar:
  /cardmanager   — Kartalarni yoqish/o'chirish (inline)
  /enablecard    — Kartani yoqish
  /disablecard   — Kartani o'chirish
  /cardstatus    — Yoqilgan/o'chirilgan statistika
  /setimage      — Karta rasmi (file_id) o'rnatish
  /editcard      — Karta maydonlarini tahrirlash
  /give          — Foydalanuvchiga Astrites berish
  /addcard       — Kartani qo'lda berish
"""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.manager import init_db
from bot.middlewares.rate_limit import RateLimitMiddleware

# ─── Handlers ────────────────────────────────────────────────
from bot.handlers import start, card, profile, gacha, collection, admin, economy, ai as ai_handler, weather, imagine, inline_mode
from bot.handlers import admin_cards

from utils.logger import setup_logger, get_logger

# Setup global logging
setup_logger()
logger = get_logger("main")


async def main():
    # Init database
    init_db()
    logger.info("✅ Database initialized")

    # Bot instance
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Dispatcher with FSM memory storage (for admin states)
    dp = Dispatcher(storage=MemoryStorage())

    # Middlewares
    dp.message.middleware(RateLimitMiddleware(
        rate        = config.RATE_LIMIT_MESSAGES,
        per_seconds = config.RATE_LIMIT_SECONDS,
    ))

    # Include routers  (order matters — admin_cards before admin)
    dp.include_router(admin_cards.router)   # FSM states first
    dp.include_router(start.router)
    dp.include_router(card.router)
    dp.include_router(profile.router)
    dp.include_router(gacha.router)
    dp.include_router(collection.router)
    dp.include_router(economy.router)
    dp.include_router(ai_handler.router)
    dp.include_router(weather.router)
    dp.include_router(imagine.router)
    dp.include_router(inline_mode.router)
    dp.include_router(admin.router)

    # Bot info
    bot_info = await bot.get_me()
    logger.info(f"🤖 Bot started: @{bot_info.username}")

    # Start polling
    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
