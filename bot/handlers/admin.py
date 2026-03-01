# bot/handlers/admin.py
"""Admin-only commands for bot management."""
import json
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import sys

from config import config
from database.manager import get_leaderboard

router = Router(name="admin")

# Filter: only admins
def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


class AddBotFSM(StatesGroup):
    token = State()
    admin_id = State()
    name = State()


@router.message(Command("admin"))
async def admin_panel(msg: Message):
    if not is_admin(msg.from_user.id):
        await msg.answer("❌ Siz admin emassiz.")
        return
    
    from bot.keyboards.inline import admin_kb
    await msg.answer(
        "🛠️ <b>ADMIN PANEL</b>\n\nCommands:\n"
        "/sync_cards - Reload cards from JSON\n"
        "/reset_astrites - Reset everyone to 1600\n"
        "/give <id> <val>\n"
        "/addcard <id> <pkg>\n"
        "/addbot <token> <admin_id> <name> - Add new bot",
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
    """Usage: /give [user_id] <amount> or reply to user with /give <amount>"""
    if not is_admin(msg.from_user.id):
        return
    
    parts = msg.text.split()
    target_id = None
    amount = None

    # Case 1: Reply to a message
    if msg.reply_to_message:
        if len(parts) < 2:
            await msg.answer("Foydalanish: Habarga reply qilib /give <miqdor> yozing.")
            return
        target_id = msg.reply_to_message.from_user.id
        try:
            amount = int(parts[1])
        except ValueError:
            await msg.answer("❌ Miqdor son bo'lishi kerak.")
            return
    
    # Case 2: Command with arguments
    else:
        if len(parts) != 3:
            await msg.answer("Foydalanish: /give <user_id> <miqdor>")
            return
        try:
            target_id = int(parts[1])
            amount    = int(parts[2])
        except ValueError:
            await msg.answer("❌ Noto'g'ri format.")
            return
    
    from database.manager import update_user_stats, get_user
    user = get_user(target_id)
    if not user:
        await msg.answer("❌ Foydalanuvchi topilmadi.")
        return
    
    update_user_stats(target_id, astrites=user["astrites"] + amount)
    await msg.answer(f"✅ {user['full_name']} ga {amount:,} Astrites berildi.")


@router.message(Command("addbot"))
async def add_bot_cmd(msg: Message):
    """Usage: /addbot <token> <admin_id> <name>"""
    if not is_admin(msg.from_user.id): return
    
    parts = msg.text.split(maxsplit=3)
    if len(parts) < 4:
        await msg.answer("Foydalanish: /addbot <token> <admin_id> <name>")
        return
    
    token = parts[1]
    try:
        admin_id = int(parts[2])
    except ValueError:
        await msg.answer("❌ Admin ID son bo'lishi kerak.")
        return
    name = parts[3]
    
    config_path = "config.json"
    import json, os, subprocess
    
    data = {"bots": []}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
    # Check if name already exists
    if any(b["name"] == name for b in data["bots"]):
        await msg.answer(f"❌ {name} nomli bot allaqachon mavjud.")
        return
        
    new_bot = {
        "name": name,
        "token": token,
        "admin_ids": [admin_id],
        "is_default": False
    }
    data["bots"].append(new_bot)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    await msg.answer(f"✅ Bot qo'shildi: {name}\nEndi uni ishga tushirishga harakat qilaman...")
    
    # Attempt to start the bot
    try:
        # We use a detached process if possible
        env = os.environ.copy()
        env["BOT_INSTANCE_NAME"] = name
        
        # On Windows
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        
        subprocess.Popen(
            [sys.executable, "main.py"],
            env=env,
            creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        await msg.answer(f"🚀 {name} ishga tushirildi (fon rejimida).")
    except Exception as e:
        await msg.answer(f"❌ Ishga tushirishda xatolik: {e}\nLekin config saqlandi.")


@router.callback_query(F.data == "admin_add_bot")
async def add_bot_start(cb: CallbackQuery, state: FSMContext):
    # Public: everyone can add a bot
    
    # Check limits first
    config_path = "config.json"
    import json, os
    
    config_data = {"bots": []}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
    
    # 1. Total limit (20 bots + 1 default)
    if len(config_data["bots"]) >= 21:
        await cb.answer("❌ Kechirasan, botlar soni maksimal miqdorga (20 ta) yetgan.", show_alert=True)
        return
        
    # 2. Per user limit (1 bot per user)
    # Default bot (creator_id will be missing or 0)
    user_bots = [b for b in config_data["bots"] if b.get("creator_id") == cb.from_user.id]
    if user_bots:
        await cb.answer("❌ Siz allaqachon bitta bot yaratgansiz. Faqat bitta botga ruxsat beriladi.", show_alert=True)
        return

    await state.set_state(AddBotFSM.token)
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back"))
    
    await cb.message.edit_text(
        "🤖 <b>YANGI BOT QO'SHISH</b>\n\n"
        "1️⃣ Bot <b>TOKEN</b>ini yuboring:",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await cb.answer()


@router.message(AddBotFSM.token)
async def add_bot_token(msg: Message, state: FSMContext):
    await state.update_data(token=msg.text.strip())
    await state.set_state(AddBotFSM.admin_id)
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back"))
    
    await msg.answer(
        "2️⃣ Yangi bot uchun <b>Admin ID</b> (raqam) yuboring:",
        reply_markup=kb.as_markup()
    )


@router.message(AddBotFSM.admin_id)
async def add_bot_admin_id(msg: Message, state: FSMContext):
    if not msg.text.strip().isdigit():
        await msg.answer("❌ Admin ID faqat raqam bo'lishi kerak.")
        return
    await state.update_data(admin_id=int(msg.text.strip()))
    await state.set_state(AddBotFSM.name)
    
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_back"))
    
    await msg.answer(
        "3️⃣ Bot uchun <b>NOM</b> (masalan: TestBot) yuboring:",
        reply_markup=kb.as_markup()
    )


@router.message(AddBotFSM.name)
async def add_bot_final(msg: Message, state: FSMContext):
    name = msg.text.strip()
    data = await state.get_data()
    token = data["token"]
    admin_id = data["admin_id"]
    await state.clear()
    
    config_path = "config.json"
    import json, os, subprocess
    
    config_data = {"bots": []}
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)
            
    if any(b["name"] == name for b in config_data["bots"]):
        await msg.answer(f"❌ {name} nomli bot allaqachon mavjud.")
        return
        
    new_bot = {
        "name": name,
        "token": token,
        "admin_ids": [admin_id],
        "is_default": False,
        "creator_id": msg.from_user.id
    }
    config_data["bots"].append(new_bot)
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)
        
    await msg.answer(f"✅ Bot qo'shildi: {name}\nUni ishga tushirishga harakat qilaman...")
    
    try:
        env = os.environ.copy()
        env["BOT_INSTANCE_NAME"] = name
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        
        subprocess.Popen(
            [sys.executable, "main.py"],
            env=env,
            creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        await msg.answer(f"🚀 {name} ishga tushirildi.")
    except Exception as e:
        await msg.answer(f"❌ Xatolik: {e}")


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


@router.message(Command("sync_cards"))
async def sync_cards_cmd(msg: Message):
    if not is_admin(msg.from_user.id): return
    from database.manager import sync_cards_from_json
    sync_cards_from_json()
    await msg.answer("✅ Kartalar bazasi yangilandi (JSON -> DB).")


@router.message(Command("reset_astrites"))
async def reset_astrites_cmd(msg: Message):
    if not is_admin(msg.from_user.id): return
    from database.manager import reset_all_astrites
    reset_all_astrites(1600)
    await msg.answer("✅ Barcha foydalanuvchilar balanslari 1600 ga reset qilindi.")


@router.callback_query(F.data == "admin_del_bot")
async def delete_bot_handler(cb: CallbackQuery):
    config_path = "config.json"
    import json, os
    
    if not os.path.exists(config_path):
        await cb.answer("❌ Config fayli topilmadi.", show_alert=True)
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Find bot created by this user (exclude default bot if it has no creator_id)
    user_bot = next((b for b in data.get("bots", []) if b.get("creator_id") == cb.from_user.id), None)
            
    if not user_bot:
        await cb.answer("❌ Siz hali bot yaratmagansiz.", show_alert=True)
        return
        
    bot_name = user_bot["name"]
    
    # Confirmation keyboard
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"admin_del_confirm_{bot_name}"),
        InlineKeyboardButton(text="❌ Yo'q", callback_data="admin_back"),
    )
    
    await cb.message.edit_text(
        f"⚠️ <b>{bot_name}</b> botini va barcha sozlamalarini o'chirib tashlaysizmi?\n\n"
        "<i>Eslatma: Bu faqat sizning botingizni o'chiradi, boshqalarnikiga ta'sir qilmaydi!</i>",
        parse_mode="HTML",
        reply_markup=kb.as_markup()
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin_del_confirm_"))
async def delete_bot_confirm(cb: CallbackQuery):
    bot_name = cb.data.replace("admin_del_confirm_", "")
    config_path = "config.json"
    import json
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Final check: existence and ownership
    bot = next((b for b in data["bots"] if b["name"] == bot_name), None)
    if not bot or bot.get("creator_id") != cb.from_user.id:
        await cb.answer("❌ Xatolik yoki ruxsat yo'q.", show_alert=True)
        return
        
    # Remove ONLY the user's specific bot
    data["bots"] = [b for b in data["bots"] if not (b["name"] == bot_name and b.get("creator_id") == cb.from_user.id)]
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    await cb.message.edit_text(
        f"✅ <b>{bot_name}</b> muvaffaqiyatli o'chirildi.",
        parse_mode="HTML"
    )
    await cb.answer("O'chirildi!", show_alert=True)


@router.message(Command("deletebot"))
async def delete_bot_cmd(msg: Message):
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🚀 Botingizni o'chirish", callback_data="admin_del_bot"))
    await msg.answer("Botni o'chirish uchun quyidagi tugmani bosing:", reply_markup=kb.as_markup())
