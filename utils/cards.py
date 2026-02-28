# utils/cards.py
import json
import random
from typing import Optional

_cards_cache: dict = {}

def load_cards(path: str = "data/cards.json") -> dict:
    global _cards_cache
    if not _cards_cache:
        with open(path, "r", encoding="utf-8") as f:
            _cards_cache = json.load(f)
    return _cards_cache


def get_all_cards(include_disabled: bool = False) -> list:
    """Returns cards. By default only enabled cards (for gacha/collection)."""
    cards = load_cards()["cards"]
    if include_disabled:
        return cards
    return [c for c in cards if c.get("enabled", True)]


def get_card_by_code(code: str) -> Optional[dict]:
    """Search all cards (including disabled) by code."""
    code = code.strip()
    for card in load_cards()["cards"]:
        if card["code"] == code:
            return card
    return None


def get_card_by_id(card_id: int) -> Optional[dict]:
    for card in get_all_cards():
        if card["id"] == card_id:
            return card
    return None


def get_rarity_config(rarity: str) -> dict:
    return load_cards()["rarity_config"].get(rarity, {})


def get_element_emoji(element: str) -> str:
    return load_cards()["element_emojis"].get(element, "🔹")


def get_weapon_emoji(weapon: str) -> str:
    return load_cards()["weapon_emojis"].get(weapon, "⚔️")


# ─────────────────────────────────────────────────────────────
#  Gacha Engine
# ─────────────────────────────────────────────────────────────
def calculate_pull_rate(pity: int, soft_pity: int = 60, hard_pity: int = 80) -> float:
    """Dynamic rate based on pity counter."""
    if pity >= hard_pity:
        return 100.0
    if pity >= soft_pity:
        # Exponential rate increase from 0.7% to ~100%
        extra = pity - soft_pity
        return min(0.7 + (extra * extra * 0.5), 100.0)
    return 0.7


def do_single_pull(pity: int = 0) -> dict:
    """Execute one pull. Returns card dict."""
    cards = get_all_cards()
    legendary_rate = calculate_pull_rate(pity)
    
    roll = random.uniform(0, 100)
    
    if roll <= legendary_rate:
        pool = [c for c in cards if c["rarity"] == "Legendary"]
    elif roll <= legendary_rate + 6.0:
        pool = [c for c in cards if c["rarity"] == "Epic"]
    elif roll <= legendary_rate + 6.0 + 20.0:
        pool = [c for c in cards if c["rarity"] == "Rare"]
    else:
        pool = [c for c in cards if c["rarity"] == "Uncommon"]
    
    if not pool:
        pool = cards
    
    return random.choice(pool)


def do_multi_pull(pity: int = 0, count: int = 10) -> list[dict]:
    """Execute 10 pulls with pity tracking."""
    results = []
    current_pity = pity
    has_legendary = False
    
    for i in range(count):
        card = do_single_pull(current_pity)
        results.append(card)
        
        if card["rarity"] == "Legendary":
            current_pity = 0
            has_legendary = True
        else:
            current_pity += 1
    
    # Guarantee at least 1 Epic in 10 pulls
    if not has_legendary and not any(c["rarity"] in ("Epic", "Legendary") for c in results):
        epic_pool = [c for c in get_all_cards() if c["rarity"] == "Epic"]
        replace_idx = random.randint(0, count - 1)
        results[replace_idx] = random.choice(epic_pool)
    
    return results


# ─────────────────────────────────────────────────────────────
#  Message Formatters
# ─────────────────────────────────────────────────────────────
def format_card_info(card: dict, is_new: bool = False) -> str:
    rarity_cfg = get_rarity_config(card["rarity"])
    elem_emoji  = get_element_emoji(card["element"])
    weap_emoji  = get_weapon_emoji(card["weapon"])
    stars       = rarity_cfg.get("stars", "⭐")
    rarity_em   = rarity_cfg.get("emoji", "💎")
    new_badge   = "  ✨ <b>NEW!</b>" if is_new else ""

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎴 <b>KARTA MA'LUMOTLARI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"\n"
        f"👤 <b>Nomi:</b>     <code>{card['name']}</code>{new_badge}\n"
        f"🏷️ <b>Unvoni:</b>  {card['title']}\n"
        f"🔑 <b>Kod:</b>     <code>{card['code']}</code>\n"
        f"{rarity_em} <b>Daraja:</b>   {stars} {card['rarity']}\n"
        f"{elem_emoji} <b>Element:</b> {card['element']}\n"
        f"{weap_emoji} <b>Qurol:</b>   {card['weapon']}\n"
        f"📚 <b>Seriya:</b>  {card['series']}\n"
        f"\n"
        f"📖 <i>{card['description']}</i>\n"
        f"\n"
        f"⚔️ <b>Bazaviy kuchlar:</b>\n"
        f"  • HP:  <code>{card['base_stats']['hp']:,}</code>\n"
        f"  • ATK: <code>{card['base_stats']['attack']:,}</code>\n"
        f"  • DEF: <code>{card['base_stats']['defense']:,}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )


def format_multi_pull_results(results: list[dict], user_cards: list) -> str:
    lines = [
        "🎰 <b>10x PULL NATIJALARI</b>",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]
    
    for i, card in enumerate(results, 1):
        rarity_cfg = get_rarity_config(card["rarity"])
        rarity_em  = rarity_cfg.get("emoji", "💎")
        is_new     = card["code"] not in user_cards
        new_tag    = " ✨" if is_new else ""
        
        lines.append(
            f"{i:02d}. {rarity_em} <b>{card['name']}</b>"
            f" <code>[{card['code']}]</code>{new_tag}"
        )
    
    legendary_count = sum(1 for c in results if c["rarity"] == "Legendary")
    epic_count      = sum(1 for c in results if c["rarity"] == "Epic")
    
    lines += [
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🌟 Legendary: <b>{legendary_count}</b>  💜 Epic: <b>{epic_count}</b>"
    ]
    return "\n".join(lines)
