# bot/handlers/economy.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database.manager import get_user, update_user_stats
from config import config

router = Router(name="economy")

@router.message(Command("refine"))
async def refine_luck(msg: Message):
    user = get_user(msg.from_user.id)
    if not user: return
    
    if user["aura"] < config.AURA_REFINE_COST:
        await msg.reply(
            f"❌ <b>Aura yetarli emas!</b>\n\n"
            f"Sizga kamida <code>{config.AURA_REFINE_COST}</code> Aura kerak.\n"
            f"Hozirgi Aura: <code>{user['aura']}</code>",
            parse_mode="HTML"
        )
        return

    new_aura = user["aura"] - config.AURA_REFINE_COST
    new_luck = user["luck_rate"] + config.LUCK_PER_REFINE
    
    update_user_stats(msg.from_user.id, aura=new_aura, luck_rate=new_luck)
    
    await msg.reply(
        f"💎 <b>OMAD REFINEMENT!</b>\n\n"
        f"🔮 Aura ishlatildi: <code>-{config.AURA_REFINE_COST}</code>\n"
        f"🍀 Yangi omad darajasi: <b>{new_luck:.1f}%</b>",
        parse_mode="HTML"
    )

@router.message(Command("bless"))
async def bless_user(msg: Message):
    if not msg.reply_to_message:
        await msg.reply("❌ Foydalanuvchiga <b>reply</b> qiling!")
        return
    
    target = msg.reply_to_message.from_user
    if target.id == msg.from_user.id:
        await msg.reply("❌ O'zingizni duo qila olmaysiz!")
        return

    user = get_user(msg.from_user.id)
    target_user = get_user(target.id)
    
    if not user: return
    if not target_user:
        await msg.reply("❌ Maqsadli foydalanuvchi botda ro'yxatdan o'tmagan.")
        return

    if user["aura"] < config.BLESS_AURA_COST:
        await msg.reply(
            f"❌ <b>Aura yetarli emas!</b>\n"
            f"Kerak: <code>{config.BLESS_AURA_COST}</code>",
            parse_mode="HTML"
        )
        return

    if target_user["luck_rate"] >= 50.0:
        await msg.reply("❌ Bu foydalanuvchining omadi allaqachon juda baland!")
        return

    update_user_stats(msg.from_user.id, aura=user["aura"] - config.BLESS_AURA_COST)
    update_user_stats(target.id, luck_rate=target_user["luck_rate"] + config.BLESS_LUCK_GIVEN)

    await msg.reply(
        f"✨ <b>DUO QILINDI (BLESS)!</b>\n\n"
        f"👤 <b>{target.full_name}</b> ga <b>+{config.BLESS_LUCK_GIVEN}%</b> omad berildi.\n"
        f"🔮 Sizdan <code>{config.BLESS_AURA_COST}</code> Aura olib tashlandi.",
        parse_mode="HTML"
    )
