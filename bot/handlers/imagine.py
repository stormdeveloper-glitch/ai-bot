# bot/handlers/imagine.py
import io
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender

from utils.imagen import generate_image
from config import config

router = Router(name="imagine")


@router.message(Command("imagine", "img", "rasm"))
async def imagine_command(msg: Message):
    """Generate an image from a text prompt using Google Imagen."""
    args = msg.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await msg.reply(
            "🎨 <b>AI Rasm Generatsiyasi</b>\n\n"
            "Ishlatish:\n"
            "<code>/imagine anime girl with blue hair, fantasy forest</code>\n\n"
            "Buyruq nomlari:\n"
            "• /imagine\n"
            "• /img\n"
            "• /rasm",
            parse_mode="HTML"
        )
        return

    prompt = args[1].strip()

    # Check API key
    api_key = config.NANO_BANANA_API_KEY or config.GEMINI_API_KEY
    if not api_key:
        await msg.reply(
            "❌ <b>Imagen API kalit sozlanmagan.</b>\n"
            "<code>NANO_BANANA_API_KEY</code> ni .env ga qo'shing.",
            parse_mode="HTML"
        )
        return

    status_msg = await msg.reply("🎨 <b>Rasm yaratilmoqda...</b> ⏳", parse_mode="HTML")

    async with ChatActionSender.upload_photo(bot=msg.bot, chat_id=msg.chat.id):
        images = await generate_image(prompt)

    if not images:
        await status_msg.edit_text(
            "❌ Rasm yaratilmadi. Qayta urinib ko'ring yoki promptni o'zgartiring.",
            parse_mode="HTML"
        )
        return

    # Send first generated image
    img_bytes = images[0]
    img_file = BufferedInputFile(img_bytes, filename="aura_generated.png")

    await msg.answer_photo(
        photo=img_file,
        caption=(
            f"🎨 <b>AI Generated</b>\n"
            f"📝 <i>{prompt[:100]}</i>"
        ),
        parse_mode="HTML"
    )
    await status_msg.delete()
