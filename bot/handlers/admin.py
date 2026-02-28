# bot/handlers/admin.py
"""Admin-only commands for bot management."""
import json
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from config import config
from database.manager import get_leaderboard

router = Router(name="admin")

# Filter: only admins
def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Siz admin emassiz.")
        return
    
    from bot.keyboards.inline import admin_kb
    await msg.answer(
        "🛠️ <b>ADMIN PANEL</b>\n\nXush kelibsiz, admin!",
        parse_mode="HTML",
        reply_markup=admin_kb()
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("❌ Ruxsat yo'q", show_alert=True)
        return
    
    import sqlite3, os
    db_size = os.path.getsize("database/bot.db") / 1024 if os.path.exists("database/bot.db") else 0
    
    import sqlite3
    conn = sqlite3.connect("database/bot.db")
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    pull_count = conn.execute("SELECT COUNT(*) FROM pull_history").fetchone()[0]
    card_count = conn.execute("SELECT COUNT(*) FROM user_cards").fetchone()[0]
    conn.close()
    
    text = (
        f"📊 <b>BOT STATISTIKASI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Foydalanuvchilar: <b>{user_count}</b>\n"
        f"🎲 Jami pulllar:     <b>{pull_count}</b>\n"
        f"🎴 Jami kartalar:    <b>{card_count}</b>\n"
        f"💾 DB hajmi:         <b>{db_size:.1f} KB</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Admin panel", callback_data="admin_back"))
    
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await cb.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        return
    from bot.keyboards.inline import admin_kb
    await cb.message.edit_text(
        "🛠️ <b>ADMIN PANEL</b>", parse_mode="HTML", reply_markup=admin_kb()
    )
    await cb.answer()


@router.message(Command("give"))
async def give_astrites(msg: Message):
    """Usage: /give <user_id> <amount>"""
    if not is_admin(msg.from_user.id):
        return
    
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.answer("Foydalanish: /give <user_id> <miqdor>")
        return
    
    try:
        target_id = int(parts[1])
        amount    = int(parts[2])
    except ValueError:
        await msg.answer("❌ Noto'g'ri format")
        return
    
    from database.manager import update_user_stats, get_user
    user = get_user(target_id)
    if not user:
        await msg.answer("❌ Foydalanuvchi topilmadi")
        return
    
    update_user_stats(target_id, astrites=user["astrites"] + amount)
    await msg.answer(f"✅ {target_id} ga {amount:,} Astrites berildi.")


@router.message(Command("addcard"))
async def add_card_to_user_cmd(msg: Message):
    """Usage: /addcard <user_id> <card_code>"""
    if not is_admin(msg.from_user.id):
        return
    
    parts = msg.text.split()
    if len(parts) != 3:
        await msg.answer("Foydalanish: /addcard <user_id> <kod>")
        return
    
    try:
        target_id = int(parts[1])
        card_code = parts[2].upper()
    except ValueError:
        await msg.answer("❌ Noto'g'ri format")
        return
    
    from utils.cards import get_card_by_code
    from database.manager import add_card_to_user
    
    card = get_card_by_code(card_code)
    if not card:
        await msg.answer(f"❌ {card_code} kartasi topilmadi")
        return
    
    is_new = add_card_to_user(target_id, card_code)
    status = "yangi" if is_new else "allaqachon bor edi"
    await msg.answer(f"✅ {target_id} ga {card['name']} ({card_code}) kartasi qo'shildi — {status}.")
