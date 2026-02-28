# bot/handlers/gacha.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, URLInputFile
from aiogram.utils.chat_action import ChatActionSender

from database.manager import (
    get_or_create_user, get_user, update_user_stats,
    add_card_to_user, add_cards_to_user_bulk, get_user_cards, 
    log_pull, log_pulls_bulk, process_pull_transaction
)
from utils.cards import (
    do_single_pull, do_multi_pull,
    format_card_info, format_multi_pull_results,
    get_card_by_code
)
from bot.keyboards.inline import pull_confirm_kb, back_kb, multi_pull_back_kb
from config import config

router = Router(name="gacha")


# ─────────────────────────────────────────────────────────────
#  Pull commands (text)
# ─────────────────────────────────────────────────────────────
@router.message(Command("pull", "wish"))
async def pull_command(msg: Message):
    user = get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    await _show_pull_confirm(msg, user, "single")


@router.message(Command("multipull", "convene"))
async def multipull_command(msg: Message):
    user = get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    await _show_pull_confirm(msg, user, "multi")


async def _show_pull_confirm(msg_or_cb, user, pull_type: str):
    cost = config.PULL_COST if pull_type == "single" else config.PULL_COST * config.MULTI_PULL_COUNT
    count_label = "1x" if pull_type == "single" else f"{config.MULTI_PULL_COUNT}x"
    pity = user["celestia_pity"]
    
    text = (
        f"🎰 <b>{count_label} PULL</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ <b>Narxi:</b>   {cost:,} Astrites\n"
        f"💰 <b>Sizda:</b>   {user['astrites']:,} Astrites\n"
        f"🔄 <b>Pity:</b>    {pity}/{config.PITY_HARD}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    if user["astrites"] < cost:
        text += f"\n❌ <b>Yetarli Astrites yo'q!</b>\n<i>Kunlik sovg'ani oling: /daily</i>"
        from bot.keyboards.inline import InlineKeyboardBuilder, InlineKeyboardButton
        from aiogram.utils.keyboard import InlineKeyboardBuilder as KB
        kb = KB()
        kb.row(InlineKeyboardButton(text="🎁 Kunlik sovg'a", callback_data="daily_reward"))
        kb.row(InlineKeyboardButton(text="🔙 Menu", callback_data="back_to_menu"))
        if isinstance(msg_or_cb, Message):
            await msg_or_cb.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
        else:
            await msg_or_cb.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
        return

    if isinstance(msg_or_cb, Message):
        await msg_or_cb.answer(text, parse_mode="HTML", reply_markup=pull_confirm_kb(pull_type))
    else:
        await msg_or_cb.edit_text(text, parse_mode="HTML", reply_markup=pull_confirm_kb(pull_type))


# ─────────────────────────────────────────────────────────────
#  Pull callbacks
# ─────────────────────────────────────────────────────────────
@router.callback_query(F.data == "pull_single")
async def pull_single_callback(cb: CallbackQuery):
    user = get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
    await _show_pull_confirm(cb.message, user, "single")
    await cb.answer()


@router.callback_query(F.data == "pull_multi")
async def pull_multi_callback(cb: CallbackQuery):
    user = get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
    await _show_pull_confirm(cb.message, user, "multi")
    await cb.answer()


@router.callback_query(F.data == "confirm_pull_single")
async def confirm_single_pull(cb: CallbackQuery):
    await cb.answer("🎰 Pull qilinmoqda...")
    # Execute pull
    user = get_user(cb.from_user.id)
    if not user: return
    pity = user["celestia_pity"]
    card = do_single_pull(pity)
    
    # Atomic transaction
    success = process_pull_transaction(
        user_id = cb.from_user.id,
        cost    = config.PULL_COST,
        new_pity = 0 if card["rarity"] == "Legendary" else pity + 1,
        aura_gain = 0 if card["rarity"] == "Legendary" else 15,
        total_pulls_gain = 1
    )
    
    if not success:
        await cb.message.edit_text("❌ Yetarli Astrites yo'q!", parse_mode="HTML")
        return
        
    # Check if new card
    is_new = add_card_to_user(cb.from_user.id, card["code"])
    log_pull(cb.from_user.id, card["code"], "single")
    
    new_user = get_user(cb.from_user.id)
    new_astrites = new_user["astrites"]
    aura_gain = 0 if card["rarity"] == "Legendary" else 15
    log_pull(cb.from_user.id, card["code"], "single")
    
    # Format response
    caption = format_card_info(card, is_new=is_new)
    caption += f"\n\n⭐ <b>Qolgan Astrites:</b> {new_astrites:,}"
    if aura_gain:
        caption += f"\n🔮 <b>Aura olindi:</b> +{aura_gain}"

    async with ChatActionSender.upload_photo(bot=cb.bot, chat_id=cb.message.chat.id):
        if card.get("image_file_id"):
            await cb.message.answer_photo(
                photo      = card["image_file_id"],
                caption    = caption,
                parse_mode = "HTML",
                reply_markup = back_kb()
            )
            await cb.message.delete()
        else:
            no_img = "\n\n🖼️ <i>Rasm hali qo'shilmagan.</i>"
            await cb.message.edit_text(caption + no_img, parse_mode="HTML", reply_markup=back_kb())


@router.callback_query(F.data == "confirm_pull_multi")
async def confirm_multi_pull(cb: CallbackQuery):
    await cb.answer("🎲 10x Pull boshlandi...")
    # Execute pull
    user = get_user(cb.from_user.id)
    if not user: return
    cost = config.PULL_COST * config.MULTI_PULL_COUNT
    pity = user["celestia_pity"]
    owned_codes = get_user_cards(cb.from_user.id)
    cards = do_multi_pull(pity, config.MULTI_PULL_COUNT)

    # Calculate results
    legendary_pulled = [c for c in cards if c["rarity"] == "Legendary"]
    new_pity = 0 if legendary_pulled else min(pity + config.MULTI_PULL_COUNT, config.PITY_HARD)
    aura_gain = (config.MULTI_PULL_COUNT - len(legendary_pulled)) * 15

    # Atomic transaction
    success = process_pull_transaction(
        user_id = cb.from_user.id,
        cost    = cost,
        new_pity = new_pity,
        aura_gain = aura_gain,
        total_pulls_gain = config.MULTI_PULL_COUNT
    )

    if not success:
        await cb.message.edit_text("❌ Yetarli Astrites yo'q!", parse_mode="HTML")
        return

    # Bulk update cards and logs
    card_codes = [c["code"] for c in cards]
    add_cards_to_user_bulk(cb.from_user.id, card_codes)
    log_pulls_bulk(cb.from_user.id, card_codes, "multi")

    new_user = get_user(cb.from_user.id)
    new_astrites = new_user["astrites"]

    result_text = format_multi_pull_results(cards, owned_codes)
    result_text += f"\n\n⭐ <b>Qolgan Astrites:</b> {new_astrites:,}"
    if aura_gain:
        result_text += f"\n🔮 <b>Aura olindi:</b> +{aura_gain}"

    await cb.message.edit_text(result_text, parse_mode="HTML", reply_markup=multi_pull_back_kb())
