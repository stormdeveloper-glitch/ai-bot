# bot/handlers/profile.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, URLInputFile

from database.manager import get_or_create_user, count_user_cards, claim_daily
from config import config

router = Router(name="profile")


def build_profile_text(user, card_count: int) -> str:
    username = f"@{user['username']}" if user["username"] else "—"
    astrites = user["astrites"]
    approx_pulls = astrites // 160

    return (
        f"🧙‍♀️ <b>{config.BOT_NAME.upper()}'S JOURNEY</b> — <i>Mage License</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Mage:</b>         {user['full_name']} ({username})\n"
        f"🆔 <b>Soul ID:</b>      <code>{user['user_id']}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>BATTLE STATS</b>\n"
        f"🔮 <b>Mana (MP):</b>    {user['aura']:,}\n"
        f"🍀 <b>Luck Rate:</b>    {user['luck_rate']:.1f}%\n"
        f"⭐ <b>Astrites:</b>     {astrites:,} <tg-spoiler>(~ {approx_pulls} pulls)</tg-spoiler>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👗 <b>Collection:</b>   {card_count} Grimoires\n"
        f"🎲 <b>Total Wishes:</b> {user['total_pulls']}\n"
        f"🌙 <b>Pity (Star):</b>  {user['celestia_pity']} / {config.PITY_HARD}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Traveler, the path to Aureole is long.</i>"
    )


def profile_kb() -> object:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="�️ View Collection", callback_data="my_collection")
    )
    return builder.as_markup()


@router.message(Command("profile"))
async def profile_command(msg: Message):
    # Check for reply
    target_user = msg.reply_to_message.from_user if msg.reply_to_message else msg.from_user
    
    user = get_or_create_user(target_user.id, target_user.username, target_user.full_name)
    card_count = count_user_cards(target_user.id)
    
    await msg.answer_photo(
        photo=URLInputFile(config.PROFILE_IMAGE_URL),
        caption=build_profile_text(user, card_count),
        parse_mode="HTML",
        reply_markup=profile_kb()
    )


@router.callback_query(F.data == "my_profile")
async def profile_callback(cb: CallbackQuery):
    user = get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
    card_count = count_user_cards(cb.from_user.id)
    
    # Since the previous message might be text, we better send a new photo or delete the old one
    try:
        await cb.message.delete()
    except:
        pass
        
    await cb.message.answer_photo(
        photo=URLInputFile(config.PROFILE_IMAGE_URL),
        caption=build_profile_text(user, card_count),
        parse_mode="HTML",
        reply_markup=profile_kb()
    )
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
