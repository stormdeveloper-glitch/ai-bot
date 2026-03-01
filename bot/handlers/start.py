# bot/handlers/start.py
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery

from database.manager import get_or_create_user
from bot.keyboards.inline import main_menu_kb
from config import config

router = Router(name="start")

def get_welcome_text():
    return f"""
🧙‍♀️ <b>{config.BOT_NAME.upper()}'S JOURNEY</b> ga xush kelibsiz!

━━━━━━━━━━━━━━━━━━━━━━
Siz bu yerda:

🎴 Anime kartalarini (Grimoirlarni) <b>to'playsiz</b>
🎰 Gacha tizimi orqali <b>pull qilasiz</b>
👤 O'z <b>sehrgar profilingizni</b> ko'rasiz
🏆 <b>Reytingda</b> o'rinni egallaysiz

━━━━━━━━━━━━━━━━━━━━━━
🎁 <b>Yangi o'yinchi bonusi: 1,600 ⭐ Astrites</b>
<i>(10 ta bepul pull!)</i>
━━━━━━━━━━━━━━━━━━━━━━
"""

HELP_TEXT = """
📖 <b>BUYRUQLAR RO'YXATI</b>
━━━━━━━━━━━━━━━━━━━━━━

🎮 <b>Asosiy buyruqlar:</b>
/start        — Bosh menu
/help         — Buyruqlar ro'yxati
/profile      — Profilingiz
/card [kod]    — Karta ma'lumoti
/collection   — Koleksiyangiz
/pull         — 1x pull (160 ⭐)
/multipull    — 10x pull (1600 ⭐)
/daily        — Kunlik sovg'a
/top          — Reyting

🤖 <b>AI va Kommunikatsiya:</b>
/ai [savol]    — AI yordamchi (Frieren)
/weather [joy] — Ob-havo ma'lumoti
/imagine [text] — Rasm chizish (AI)
@bot_username — Inline qidiruv (chatda)

⚙️ <b>Botni Boshqarish:</b>
/addbot       — Yangi bot qo'shish
/deletebot    — O'zingiz yaratgan botni o'chirish
/admin        — Admin panel (faqat adminlar)

━━━━━━━━━━━━━━━━━━━━━━
⭐ <b>Pity tizimi:</b>
• 60-pull: Yumshoq pity boshlanadi
• 80-pull: Kafolatlangan Legendary!
━━━━━━━━━━━━━━━━━━━━━━
"""


@router.message(CommandStart())
async def start_handler(msg: Message):
    user = get_or_create_user(
        user_id   = msg.from_user.id,
        username  = msg.from_user.username,
        full_name = msg.from_user.full_name,
    )
    await msg.answer(get_welcome_text(), parse_mode="HTML", reply_markup=main_menu_kb())


@router.message(Command("help"))
async def help_handler(msg: Message):
    await msg.answer(HELP_TEXT, parse_mode="HTML")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(cb: CallbackQuery):
    await cb.message.edit_text(
        f"🧙‍♀️ <b>{config.BOT_NAME.upper()}'S JOURNEY</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
    await cb.answer()


@router.callback_query(F.data == "cancel")
async def cancel_handler(cb: CallbackQuery):
    await cb.message.edit_text(
        "❌ <b>Bekor qilindi.</b>",
        parse_mode="HTML",
        reply_markup=main_menu_kb()
    )
    await cb.answer()


@router.callback_query(F.data == "noop")
async def noop_handler(cb: CallbackQuery):
    await cb.answer()
