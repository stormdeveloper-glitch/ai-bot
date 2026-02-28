# bot/handlers/profile.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database.manager import get_or_create_user, count_user_cards, claim_daily
from config import config

router = Router(name="profile")


def build_profile_text(user, card_count: int) -> str:
    from datetime import date
    today = date.today().isoformat()
    daily_status = "✅ Olindi" if user["last_daily"] == today else "🎁 Tayyor!"

    # Progress bar for pity
    def pity_bar(current: int, max_val: int, length: int = 10) -> str:
        filled = int((current / max_val) * length)
        return "█" * filled + "░" * (length - filled)

    cel_bar = pity_bar(user["celestia_pity"],  config.PITY_HARD)
    arc_bar = pity_bar(user["arcborne_pity"],  config.PITY_HARD)

    username = f"@{user['username']}" if user["username"] else "—"

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"◆ <b>PROFIL</b> ◆\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"👤 <b>Ism:</b>      {user['full_name']}\n"
        f"🆔 <b>Soul ID:</b>  <code>{user['user_id']}</code>\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"\n"
        f"━━ 📊 STATISTIKA ━━\n"
        f"⭐ <b>Astrites:</b>       <code>{user['astrites']:,}</code>\n"
        f"🔮 <b>Aura:</b>           <code>{user['aura']:,}</code>\n"
        f"🍀 <b>Omad darajasi:</b>  {user['luck_rate']:.1f}%\n"
        f"🎴 <b>Kartalar:</b>       {card_count} ta\n"
        f"🎲 <b>Jami pulllar:</b>   {user['total_pulls']}\n"
        f"\n"
        f"━━ 🔄 PITY ━━\n"
        f"🌙 <b>Celestia:</b>  {user['celestia_pity']:2d}/{config.PITY_HARD}  [{cel_bar}]\n"
        f"🌀 <b>Arcborne:</b>  {user['arcborne_pity']:2d}/{config.PITY_HARD}  [{arc_bar}]\n"
        f"\n"
        f"🎁 <b>Kunlik sovg'a:</b> {daily_status}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Ro'yxatdan: {user['created_at'][:10]}</i>"
    )


def profile_kb() -> object:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👜 Koleksiyam",    callback_data="my_collection"),
        InlineKeyboardButton(text="🎁 Kunlik sovg'a", callback_data="daily_reward"),
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")
    )
    return builder.as_markup()


@router.message(Command("profile"))
async def profile_command(msg: Message):
    user = get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    card_count = count_user_cards(msg.from_user.id)
    await msg.answer(build_profile_text(user, card_count), parse_mode="HTML", reply_markup=profile_kb())


@router.callback_query(F.data == "my_profile")
async def profile_callback(cb: CallbackQuery):
    user = get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
    card_count = count_user_cards(cb.from_user.id)
    await cb.message.edit_text(build_profile_text(user, card_count), parse_mode="HTML", reply_markup=profile_kb())
    await cb.answer()


@router.message(Command("daily"))
async def daily_command(msg: Message):
    await _give_daily(msg.from_user.id, msg.from_user.username, msg.from_user.full_name, msg)


@router.callback_query(F.data == "daily_reward")
async def daily_callback(cb: CallbackQuery):
    await _give_daily(cb.from_user.id, cb.from_user.username, cb.from_user.full_name, cb.message, cb)


async def _give_daily(user_id, username, full_name, msg_or_obj, cb=None):
    from aiogram.types import Message as Msg
    get_or_create_user(user_id, username, full_name)
    
    claimed = claim_daily(user_id, config.DAILY_ASTRITES)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎰 Pull qilish", callback_data="pull_single"),
        InlineKeyboardButton(text="🔙 Menu",        callback_data="back_to_menu"),
    )

    if claimed:
        text = (
            f"🎁 <b>KUNLIK SOVG'A!</b>\n\n"
            f"✨ <b>+{config.DAILY_ASTRITES} Astrites</b> qo'shildi!\n\n"
            f"<i>Ertaga yana keling 😊</i>"
        )
    else:
        text = (
            f"⏳ <b>Kunlik sovg'a allaqachon olindi.</b>\n\n"
            f"<i>Ertaga qaytib keling!</i>"
        )

    if cb:
        await msg_or_obj.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        await cb.answer("✅ Olindi!" if claimed else "⏳ Ertaga!")
    else:
        await msg_or_obj.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
