# bot/handlers/collection.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from database.manager import get_or_create_user, get_user_cards, count_user_cards, get_leaderboard
from utils.cards import get_card_by_code, get_rarity_config, get_all_cards

router = Router(name="collection")

CARDS_PER_PAGE = 8


def build_collection_page(user_cards: list[str], page: int) -> tuple[str, int]:
    """Returns (text, total_pages)."""
    if not user_cards:
        return "📭 <b>Koleksiyangiz bo'sh.</b>\n\n🎰 Pull qilish uchun: /pull", 1

    all_cards_data = get_all_cards(include_disabled=True)
    cards_map = {c["code"]: c for c in all_cards_data}
    
    # Sort by rarity stars desc, then code
    owned_details = [
        cards_map[code] for code in user_cards
        if code in cards_map
    ]
    owned_details.sort(key=lambda c: (-c["rarity_stars"], c["code"]))
    
    total_pages = max(1, (len(owned_details) + CARDS_PER_PAGE - 1) // CARDS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    
    start = page * CARDS_PER_PAGE
    page_cards = owned_details[start : start + CARDS_PER_PAGE]
    
    # Count by rarity
    rarity_counts = {}
    for c in owned_details:
        rarity_counts[c["rarity"]] = rarity_counts.get(c["rarity"], 0) + 1
    
    lines = [
        f"👜 <b>KOLEKSIYAM</b>  [{len(user_cards)}/{len(all_cards_data)} ta]",
        "━━━━━━━━━━━━━━━━━━━━━━",
    ]
    
    # Rarity summary
    for rarity in ["Legendary", "Epic", "Rare", "Uncommon"]:
        cnt = rarity_counts.get(rarity, 0)
        if cnt > 0:
            cfg = get_rarity_config(rarity)
            lines.append(f"{cfg.get('emoji','⭐')} {rarity}: <b>{cnt}</b>")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    
    current_rarity = None
    for card in page_cards:
        if card["rarity"] != current_rarity:
            current_rarity = card["rarity"]
            cfg = get_rarity_config(current_rarity)
            lines.append(f"\n{cfg.get('emoji','⭐')} <b>{current_rarity}</b>")
        
        lines.append(
            f"  • <b>{card['name']}</b>  "
            f"<code>/card {card['code']}</code>"
        )
    
    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"📄 Sahifa {page+1}/{total_pages}")
    
    return "\n".join(lines), total_pages


@router.message(Command("collection"))
async def collection_command(msg: Message):
    get_or_create_user(msg.from_user.id, msg.from_user.username, msg.from_user.full_name)
    user_cards = get_user_cards(msg.from_user.id)
    text, total = build_collection_page(user_cards, 0)
    
    from bot.keyboards.inline import collection_nav_kb
    kb = collection_nav_kb(0, total, msg.from_user.id)
    await msg.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "my_collection")
async def collection_callback(cb: CallbackQuery):
    user_cards = get_user_cards(cb.from_user.id)
    text, total = build_collection_page(user_cards, 0)
    
    from bot.keyboards.inline import collection_nav_kb
    kb = collection_nav_kb(0, total, cb.from_user.id)
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("col_page_"))
async def collection_page_nav(cb: CallbackQuery):
    page = int(cb.data.split("_")[-1])
    user_cards = get_user_cards(cb.from_user.id)
    text, total = build_collection_page(user_cards, page)
    
    from bot.keyboards.inline import collection_nav_kb
    kb = collection_nav_kb(page, total, cb.from_user.id)
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


# ─────────────────────────────────────────────────────────────
#  Leaderboard
# ─────────────────────────────────────────────────────────────
@router.message(Command("top"))
async def top_command(msg: Message):
    await _show_leaderboard(msg)


@router.callback_query(F.data == "leaderboard")
async def leaderboard_callback(cb: CallbackQuery):
    await _show_leaderboard(cb.message, cb)


async def _show_leaderboard(msg_or_obj, cb=None):
    rows = get_leaderboard(10)
    
    medals = ["🥇", "🥈", "🥉"]
    lines = [
        "🏆 <b>TOP 10 KOLLEKTORLAR</b>",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]
    
    for i, row in enumerate(rows):
        medal = medals[i] if i < 3 else f"{i+1}."
        lines.append(
            f"{medal} <b>{row['full_name']}</b>\n"
            f"    🎴 {row['card_count']} karta  |  🎲 {row['total_pulls']} pull"
        )
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu"))

    if cb:
        await msg_or_obj.edit_text("\n".join(lines), parse_mode="HTML", reply_markup=builder.as_markup())
        await cb.answer()
    else:
        await msg_or_obj.answer("\n".join(lines), parse_mode="HTML", reply_markup=builder.as_markup())
