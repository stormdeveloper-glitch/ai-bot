# bot/handlers/ai.py
import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from ai_core.engine import get_ai_response
from config import config

router = Router(name="ai")

# Simple memory-based cooldown (user_id -> last_timestamp)
AI_COOLDOWN = {}

@router.message(Command("ai"))
async def ai_command(msg: Message):
    """Handle /ai <question> command."""
    user_id = msg.from_user.id
    now = asyncio.get_event_loop().time()
    
    # 5-second cooldown
    if user_id in AI_COOLDOWN and now - AI_COOLDOWN[user_id] < 5:
        await msg.reply("⏳ <b>Iltimos, biroz kuting!</b>\nAI ga har 5 soniyada faqat bitta savol berish mumkin.", parse_mode="HTML")
        return
    AI_COOLDOWN[user_id] = now
    # Extract question from message
    args = msg.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await msg.reply(
            f"🧙‍♀️ <b>{config.BOT_NAME} AI</b>\n\n"
            "Sehrgar sifatida savollaringizga javob beraman:\n"
            "<code>/ai Sizning savolingiz</code>\n\n"
            "Misol: <code>/ai Sehr-jodu haqida nimalarni bilasan?</code>",
            parse_mode="HTML"
        )
        return

    question = args[1].strip()

    # Show typing action
    async with ChatActionSender.typing(bot=msg.bot, chat_id=msg.chat.id):
        response_text, latency_ms, is_online = await get_ai_response(msg.from_user.id, question)

    # Status indicators
    status = "🟢 Online" if is_online else "🔴 Offline"
    latency_info = f" · ⚡{latency_ms:.0f}ms" if latency_ms > 0 else ""

    await msg.reply(
        f"🧙‍♀️ <b>{config.BOT_NAME} AI</b> <i>({status}{latency_info})</i>\n\n{response_text}",
        parse_mode="HTML"
    )
