# bot/handlers/ai.py
import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender
from ai_core.engine import get_ai_response

router = Router(name="ai")

@router.message(Command("ai"))
async def ai_command(msg: Message):
    """Handle /ai <question> command."""
    # Extract question from message
    args = msg.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await msg.reply(
            "🤖 <b>AuraX AI</b>\n\n"
            "Savol berish uchun:\n"
            "<code>/ai Sizning savolingiz</code>\n\n"
            "Misol: <code>/ai Celestia kartasini qanday olaman?</code>",
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
        f"🤖 <b>AuraX AI</b> <i>({status}{latency_info})</i>\n\n{response_text}",
        parse_mode="HTML"
    )
