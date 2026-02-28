# bot/handlers/card.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database.manager import get_or_create_user, has_card
from utils.cards import get_card_by_code, get_all_cards, get_rarity_config, format_card_info

router = Router(name="card")


@router.message(Command("card"))
async def card_command(msg: Message):
    """Usage: /card <KOD>   e.g.  /card 1"""
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.answer(
            "❓ <b>Karta kodini kiriting.</b>\n\n"
            "Misol: <code>/card 1</code>\n\n"
            "Barcha kartalar: /collection",
            parse_mode="HTML"
        )
        return

    code = args[1].strip()
    card = get_card_by_code(code)

    if not card:
        await msg.answer(
            f"❌ <b>{code}</b> kodli karta topilmadi.\n\n"
            "Mavjud kartalarni ko'rish: <code>/collection</code>",
            parse_mode="HTML"
        )
        return

    get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    owned       = has_card(msg.from_user.id, card["code"])
    owned_badge = "\n🟢 <i>Bu karta sizda bor!</i>" if owned else "\n🔴 <i>Bu karta sizda yo'q</i>"
    caption     = format_card_info(card) + owned_badge

    async with ChatActionSender.upload_photo(bot=msg.bot, chat_id=msg.chat.id):
        if card.get("image_file_id"):
            await msg.answer_photo(
                photo      = card["image_file_id"],
                caption    = caption,
                parse_mode = "HTML"
            )
        else:
            no_img = (
                "\n\n🖼️ <i>Rasm qo'shilmagan.</i>\n"
                f"<i>Admin: rasmga reply → <code>/setimage {card['code']}</code></i>"
            )
            await msg.answer(caption + no_img, parse_mode="HTML")


@router.callback_query(F.data == "all_cards")
async def all_cards_handler(cb: CallbackQuery):
    cards = get_all_cards()

    lines = ["📖 <b>BARCHA KARTALAR RO'YXATI</b>", "━━━━━━━━━━━━━━━━━━━━━━"]

    current_rarity = None
    for card in sorted(cards, key=lambda c: -c.get("rarity_stars", 0)):
        if card["rarity"] != current_rarity:
            current_rarity = card["rarity"]
            cfg = get_rarity_config(current_rarity)
            lines.append(f"\n{cfg.get('emoji','⭐')} <b>{current_rarity}</b>")
        lines.append(f"  • <code>{card['code']}</code> — <b>{card['name']}</b>")

    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        "ℹ️ <i>Karta ma'lumoti: /card [kod]</i>"
    ]

    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu"))

    await cb.message.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=kb.as_markup())
    await cb.answer()
