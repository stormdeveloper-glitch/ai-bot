# bot/handlers/admin_cards.py
"""
Admin karta boshqaruv paneli.

Imkoniyatlar:
  • Barcha kartalarni ko'rish (element bo'yicha filter)
  • Karta yoqish / o'chirish (gacha pooldan)
  • Karta maydonlarini tahrirlash
  • Yangi karta qo'shish (step-by-step FSM)
  • Foydalanuvchiga karta berish
"""
import json
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config

router = Router(name="admin_cards")

CARDS_PATH = "data/cards.json"

# ─── Constants ──────────────────────────────────────────────
ELEMENTS = ["Glacio", "Fusion", "Electro", "Aero", "Spectro", "Havoc"]
WEAPONS  = ["Sword", "Broadblade", "Pistols", "Rectifier", "Gauntlets"]
RARITIES = ["Legendary", "Epic"]

RARITY_STARS  = {"Legendary": 5, "Epic": 4}
RARITY_RATE   = {"Legendary": 0.7, "Epic": 6.0}
RARITY_HP     = {"Legendary": 10000, "Epic": 7500}
RARITY_ATK    = {"Legendary": 450,   "Epic": 360}
RARITY_DEF    = {"Legendary": 300,   "Epic": 260}

ELEMENT_EMOJIS = {
    "Glacio": "❄️", "Fusion": "🔥", "Aero": "💨",
    "Electro": "⚡", "Havoc": "🌀", "Spectro": "✨"
}
WEAPON_EMOJIS = {
    "Sword": "⚔️", "Broadblade": "🗡️", "Pistols": "🔫",
    "Rectifier": "🔮", "Gauntlets": "👊"
}
RARITY_EMOJI = {"Legendary": "🌟", "Epic": "💜"}


# ─── FSM ────────────────────────────────────────────────────
class AddCardFSM(StatesGroup):
    name        = State()
    rarity      = State()
    element     = State()
    weapon      = State()
    title       = State()
    description = State()
    confirm     = State()


class EditFieldFSM(StatesGroup):
    waiting = State()


class GiveCardFSM(StatesGroup):
    user_id   = State()
    card_code = State()


# ─── Helpers ────────────────────────────────────────────────
def is_admin(uid: int) -> bool:
    return uid in config.ADMIN_IDS


def load_json() -> dict:
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict):
    with open(CARDS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_card(code: str) -> dict | None:
    code = code.strip()
    for c in load_json()["cards"]:
        if c["code"] == code:
            return c
    return None


def next_code(data: dict) -> tuple[int, str]:
    new_id = max((c["id"] for c in data["cards"]), default=0) + 1
    return new_id, str(new_id)


def card_detail_text(c: dict) -> str:
    em     = ELEMENT_EMOJIS.get(c["element"], "🔹")
    wm     = WEAPON_EMOJIS.get(c["weapon"], "⚔️")
    rem    = RARITY_EMOJI.get(c["rarity"], "⭐")
    status = "✅ Faol" if c.get("enabled", True) else "❌ O'chirilgan"
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🃏 <b>KARTA BOSHQARUVI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Nom:</b>     {c['name']}\n"
        f"🏷️ <b>Unvon:</b>  {c['title']}\n"
        f"🔑 <b>Kod:</b>    <code>{c['code']}</code>\n"
        f"{rem} <b>Daraja:</b> {c['rarity']}\n"
        f"{em} <b>Element:</b> {c['element']}\n"
        f"{wm} <b>Qurol:</b>  {c['weapon']}\n"
        f"⚔️ HP/ATK/DEF: "
        f"<code>{c['base_stats']['hp']:,}</code> / "
        f"<code>{c['base_stats']['attack']}</code> / "
        f"<code>{c['base_stats']['defense']}</code>\n"
        f"🎲 <b>Drop rate:</b> {c['drop_rate']}%\n"
        f"📊 <b>Holat:</b>    {status}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )


def card_detail_kb(c: dict) -> InlineKeyboardMarkup:
    enabled = c.get("enabled", True)
    toggle_text = "❌ Pooldan chiqar" if enabled else "✅ Poolga qo'sh"
    toggle_cb   = f"acd_off_{c['code']}" if enabled else f"acd_on_{c['code']}"
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text=toggle_text, callback_data=toggle_cb))
    b.row(
        InlineKeyboardButton(text="✏️ Tahrirlash", callback_data=f"acd_edit_{c['code']}"),
        InlineKeyboardButton(text="🗑️ O'chirish",  callback_data=f"acd_del_{c['code']}"),
    )
    b.row(InlineKeyboardButton(text="🔙 Ro'yxat", callback_data="acd_list_all"))
    return b.as_markup()


def main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="📋 Barcha kartalar",      callback_data="acd_list_all"),
        InlineKeyboardButton(text="🔍 Element bo'yicha",     callback_data="acd_filter"),
    )
    b.row(
        InlineKeyboardButton(text="✅ Faol kartalar",        callback_data="acd_list_on"),
        InlineKeyboardButton(text="❌ O'chirilgan kartalar", callback_data="acd_list_off"),
    )
    b.row(
        InlineKeyboardButton(text="➕ Yangi karta qo'sh",   callback_data="acd_add"),
        InlineKeyboardButton(text="🎁 Karta ber",           callback_data="acd_give"),
    )
    b.row(InlineKeyboardButton(text="🔙 Admin menu", callback_data="admin_back"))
    return b.as_markup()


# ─── Entry Point ────────────────────────────────────────────
@router.message(Command("admincards"))
async def cmd_admincards(msg: Message):
    if not is_admin(msg.from_user.id):
        return await msg.answer("❌ Ruxsat yo'q.")
    await msg.answer(
        "🃏 <b>KARTA BOSHQARUV PANELI</b>\n\nAmalni tanlang:",
        parse_mode="HTML", reply_markup=main_kb()
    )


@router.callback_query(F.data == "acd_back")
async def back_main(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text(
        "🃏 <b>KARTA BOSHQARUV PANELI</b>\n\nAmalni tanlang:",
        parse_mode="HTML", reply_markup=main_kb()
    )
    await cb.answer()


# ─── List Kartalar ──────────────────────────────────────────
def build_list(cards: list, title: str, page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    PER = 8
    total = max(1, (len(cards) + PER - 1) // PER)
    page  = max(0, min(page, total - 1))
    chunk = cards[page * PER: (page + 1) * PER]

    lines = [f"📋 <b>{title}</b>  [{len(cards)} ta]", "━━━━━━━━━━━━━━━━━━━━━━"]
    for c in chunk:
        em  = ELEMENT_EMOJIS.get(c["element"], "🔹")
        rem = RARITY_EMOJI.get(c["rarity"], "⭐")
        st  = "✅" if c.get("enabled", True) else "❌"
        lines.append(f"{st} {rem} {em} <b>{c['name']}</b>  <code>{c['code']}</code>")

    lines.append(f"\n📄 {page+1}/{total}")

    b = InlineKeyboardBuilder()
    for c in chunk:
        st = "✅" if c.get("enabled", True) else "❌"
        b.row(InlineKeyboardButton(
            text=f"{st} {c['name']}  [{c['code']}]",
            callback_data=f"acd_card_{c['code']}"
        ))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"acd_pg_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total}", callback_data="noop"))
    if page < total - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"acd_pg_{page+1}"))
    if nav:
        b.row(*nav)
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="acd_back"))
    return "\n".join(lines), b.as_markup()


@router.callback_query(F.data == "acd_list_all")
async def list_all(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    t, kb = build_list(load_json()["cards"], "BARCHA KARTALAR")
    await cb.message.edit_text(t, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data == "acd_list_on")
async def list_on(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    cards = [c for c in load_json()["cards"] if c.get("enabled", True)]
    t, kb = build_list(cards, "✅ FAOL KARTALAR")
    await cb.message.edit_text(t, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data == "acd_list_off")
async def list_off(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    cards = [c for c in load_json()["cards"] if not c.get("enabled", True)]
    t, kb = build_list(cards, "❌ O'CHIRILGAN KARTALAR")
    await cb.message.edit_text(t, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


@router.callback_query(F.data.startswith("acd_pg_"))
async def page_nav(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    page = int(cb.data.split("_")[-1])
    t, kb = build_list(load_json()["cards"], "BARCHA KARTALAR", page)
    await cb.message.edit_text(t, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


# ─── Element Filter ─────────────────────────────────────────
@router.callback_query(F.data == "acd_filter")
async def filter_menu(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    b = InlineKeyboardBuilder()
    for el in ELEMENTS:
        b.row(InlineKeyboardButton(
            text=f"{ELEMENT_EMOJIS[el]} {el}",
            callback_data=f"acd_el_{el}"
        ))
    b.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="acd_back"))
    await cb.message.edit_text("🔍 <b>Element tanlang:</b>", parse_mode="HTML", reply_markup=b.as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("acd_el_"))
async def filter_by_el(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    el    = cb.data.replace("acd_el_", "")
    cards = [c for c in load_json()["cards"] if c["element"] == el]
    em    = ELEMENT_EMOJIS.get(el, "🔹")
    t, kb = build_list(cards, f"{em} {el.upper()} KARTALAR")
    await cb.message.edit_text(t, parse_mode="HTML", reply_markup=kb)
    await cb.answer()


# ─── Card Detail ────────────────────────────────────────────
@router.callback_query(F.data.startswith("acd_card_"))
async def show_card(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    code = cb.data.replace("acd_card_", "")
    c    = get_card(code)
    if not c: return await cb.answer("Topilmadi!", show_alert=True)
    await cb.message.edit_text(card_detail_text(c), parse_mode="HTML", reply_markup=card_detail_kb(c))
    await cb.answer()


# ─── Toggle Enabled ─────────────────────────────────────────
@router.callback_query(F.data.startswith("acd_on_"))
async def enable_card(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    code = cb.data.replace("acd_on_", "")
    data = load_json()
    for c in data["cards"]:
        if c["code"] == code:
            c["enabled"] = True
            save_json(data)
            await cb.message.edit_text(card_detail_text(c), parse_mode="HTML", reply_markup=card_detail_kb(c))
            return await cb.answer(f"✅ {c['name']} yoqildi!", show_alert=True)
    await cb.answer("Topilmadi!", show_alert=True)


@router.callback_query(F.data.startswith("acd_off_"))
async def disable_card(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    code = cb.data.replace("acd_off_", "")
    data = load_json()
    for c in data["cards"]:
        if c["code"] == code:
            c["enabled"] = False
            save_json(data)
            await cb.message.edit_text(card_detail_text(c), parse_mode="HTML", reply_markup=card_detail_kb(c))
            return await cb.answer(f"❌ {c['name']} o'chirildi!", show_alert=True)
    await cb.answer("Topilmadi!", show_alert=True)


# ─── Edit Card Fields ───────────────────────────────────────
FIELD_LABELS = {
    "name":    "Yangi nom",
    "title":   "Yangi unvon",
    "rarity":  f"Daraja: {' / '.join(RARITIES)}",
    "element": f"Element: {' / '.join(ELEMENTS)}",
    "weapon":  f"Qurol: {' / '.join(WEAPONS)}",
    "desc":    "Yangi tavsif",
}


def edit_menu_kb(code: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="📝 Nom",     callback_data=f"acd_ef_name_{code}"),
        InlineKeyboardButton(text="🏷️ Unvon",  callback_data=f"acd_ef_title_{code}"),
    )
    b.row(
        InlineKeyboardButton(text="🌟 Daraja",  callback_data=f"acd_ef_rarity_{code}"),
        InlineKeyboardButton(text="🔹 Element", callback_data=f"acd_ef_element_{code}"),
    )
    b.row(
        InlineKeyboardButton(text="⚔️ Qurol",   callback_data=f"acd_ef_weapon_{code}"),
        InlineKeyboardButton(text="📖 Tavsif",  callback_data=f"acd_ef_desc_{code}"),
    )
    b.row(InlineKeyboardButton(text="🔙 Karta", callback_data=f"acd_card_{code}"))
    return b.as_markup()


@router.callback_query(F.data.startswith("acd_edit_"))
async def edit_menu(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    code = cb.data.replace("acd_edit_", "")
    c    = get_card(code)
    if not c: return await cb.answer("Topilmadi!")
    await cb.message.edit_text(
        f"✏️ <b>{c['name']}</b> — qaysi maydonni o'zgartirish?",
        parse_mode="HTML", reply_markup=edit_menu_kb(code)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("acd_ef_"))
async def edit_field_prompt(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    # acd_ef_<field>_<code>
    parts = cb.data.split("_", 3)   # ['acd','ef','field','code']
    field = parts[2]
    code  = parts[3]

    await state.set_state(EditFieldFSM.waiting)
    await state.update_data(field=field, code=code)

    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🚫 Bekor", callback_data=f"acd_card_{code}"))
    await cb.message.edit_text(
        f"✏️ <b>{code}</b> — {FIELD_LABELS.get(field, field)} yozing:",
        parse_mode="HTML", reply_markup=b.as_markup()
    )
    await cb.answer()


@router.message(EditFieldFSM.waiting)
async def save_field(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): await state.clear(); return
    d = await state.get_data()
    await state.clear()
    field, code, value = d["field"], d["code"], msg.text.strip()

    data = load_json()
    card = next((c for c in data["cards"] if c["code"] == code), None)
    if not card:
        return await msg.answer("❌ Karta topilmadi.")

    if field == "name":
        card["name"] = value
    elif field == "title":
        card["title"] = value
    elif field == "rarity":
        if value not in RARITIES:
            return await msg.answer(f"❌ Noto'g'ri. ({' / '.join(RARITIES)})")
        card["rarity"]       = value
        card["rarity_stars"] = RARITY_STARS[value]
        card["drop_rate"]    = RARITY_RATE[value]
    elif field == "element":
        if value not in ELEMENTS:
            return await msg.answer(f"❌ Noto'g'ri. ({' / '.join(ELEMENTS)})")
        card["element"] = value
    elif field == "weapon":
        if value not in WEAPONS:
            return await msg.answer(f"❌ Noto'g'ri. ({' / '.join(WEAPONS)})")
        card["weapon"] = value
    elif field == "desc":
        card["description"] = value

    save_json(data)
    await msg.answer(
        f"✅ Saqlandi!\n\n" + card_detail_text(card),
        parse_mode="HTML", reply_markup=card_detail_kb(card)
    )


# ─── Delete Card ────────────────────────────────────────────
@router.callback_query(F.data.startswith("acd_del_"))
async def delete_confirm(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    code = cb.data.replace("acd_del_", "")
    c    = get_card(code)
    if not c: return await cb.answer("Topilmadi!")
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="🗑️ Ha, o'chir!", callback_data=f"acd_delok_{code}"),
        InlineKeyboardButton(text="❌ Yo'q",         callback_data=f"acd_card_{code}"),
    )
    await cb.message.edit_text(
        f"⚠️ <b>{c['name']}</b> (<code>{code}</code>) ni o'chirasizmi?\n"
        "<i>Bu amalni qaytarib bo'lmaydi!</i>",
        parse_mode="HTML", reply_markup=b.as_markup()
    )
    await cb.answer()


@router.callback_query(F.data.startswith("acd_delok_"))
async def delete_ok(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    code = cb.data.replace("acd_delok_", "")
    data = load_json()
    before = len(data["cards"])
    data["cards"] = [c for c in data["cards"] if c["code"] != code]
    if len(data["cards"]) == before:
        return await cb.answer("Topilmadi!", show_alert=True)
    save_json(data)
    await cb.message.edit_text(
        f"🗑️ <code>{code}</code> o'chirildi.", parse_mode="HTML", reply_markup=main_kb()
    )
    await cb.answer("O'chirildi!", show_alert=True)


# ─── Add New Card (FSM) ─────────────────────────────────────
def _cancel_btn(code: str = "") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🚫 Bekor", callback_data="acd_back"))
    return b.as_markup()


def sel_kb(items: list, prefix: str, emojis: dict = {}) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    for item in items:
        em = emojis.get(item, "")
        b.row(InlineKeyboardButton(text=f"{em} {item}".strip(), callback_data=f"{prefix}{item}"))
    b.row(InlineKeyboardButton(text="🚫 Bekor", callback_data="acd_back"))
    return b.as_markup()


@router.callback_query(F.data == "acd_add")
async def add_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    await state.set_state(AddCardFSM.name)
    await cb.message.edit_text(
        "➕ <b>YANGI KARTA QO'SHISH</b>\n\n"
        "1️⃣ Personaj <b>nomini</b> yozing:",
        parse_mode="HTML", reply_markup=_cancel_btn()
    )
    await cb.answer()


@router.message(AddCardFSM.name)
async def add_name(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): await state.clear(); return
    await state.update_data(name=msg.text.strip())
    await state.set_state(AddCardFSM.rarity)
    await msg.answer(
        "2️⃣ <b>Daraja</b> tanlang:",
        parse_mode="HTML",
        reply_markup=sel_kb(RARITIES, "acd_nr_", RARITY_EMOJI)
    )


@router.callback_query(F.data.startswith("acd_nr_"), AddCardFSM.rarity)
async def add_rarity(cb: CallbackQuery, state: FSMContext):
    await state.update_data(rarity=cb.data.replace("acd_nr_", ""))
    await state.set_state(AddCardFSM.element)
    await cb.message.edit_text(
        "3️⃣ <b>Element</b> tanlang:",
        parse_mode="HTML",
        reply_markup=sel_kb(ELEMENTS, "acd_ne_", ELEMENT_EMOJIS)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("acd_ne_"), AddCardFSM.element)
async def add_element(cb: CallbackQuery, state: FSMContext):
    await state.update_data(element=cb.data.replace("acd_ne_", ""))
    await state.set_state(AddCardFSM.weapon)
    await cb.message.edit_text(
        "4️⃣ <b>Qurol</b> tanlang:",
        parse_mode="HTML",
        reply_markup=sel_kb(WEAPONS, "acd_nw_", WEAPON_EMOJIS)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("acd_nw_"), AddCardFSM.weapon)
async def add_weapon(cb: CallbackQuery, state: FSMContext):
    await state.update_data(weapon=cb.data.replace("acd_nw_", ""))
    await state.set_state(AddCardFSM.title)
    await cb.message.edit_text(
        "5️⃣ Personaj <b>unvonini</b> yozing\n"
        "<i>Misol: Crimson Aria</i>",
        parse_mode="HTML", reply_markup=_cancel_btn()
    )
    await cb.answer()


@router.message(AddCardFSM.title)
async def add_title(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): await state.clear(); return
    await state.update_data(title=msg.text.strip())
    await state.set_state(AddCardFSM.description)
    await msg.answer("6️⃣ Qisqa <b>tavsif</b> yozing:", parse_mode="HTML", reply_markup=_cancel_btn())


@router.message(AddCardFSM.description)
async def add_desc(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): await state.clear(); return
    await state.update_data(description=msg.text.strip())
    await state.set_state(AddCardFSM.confirm)

    d = await state.get_data()
    r = d["rarity"]
    preview = (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆕 <b>YANGI KARTA</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {d['name']}\n"
        f"🏷️ {d['title']}\n"
        f"{RARITY_EMOJI[r]} {r}  {ELEMENT_EMOJIS[d['element']]} {d['element']}  {WEAPON_EMOJIS[d['weapon']]} {d['weapon']}\n"
        f"📖 {d['description']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ Tasdiqlaysizmi?"
    )
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Saqlash", callback_data="acd_save"),
        InlineKeyboardButton(text="❌ Bekor",   callback_data="acd_back"),
    )
    await msg.answer(preview, parse_mode="HTML", reply_markup=b.as_markup())


@router.callback_query(F.data == "acd_save", AddCardFSM.confirm)
async def save_new_card(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): await state.clear(); return
    d = await state.get_data()
    await state.clear()

    data    = load_json()
    rarity  = d["rarity"]
    nid, nc = next_code(data)

    new = {
        "id":            nid,
        "code":          nc,
        "name":          d["name"],
        "title":         d["title"],
        "rarity":        rarity,
        "rarity_stars":  RARITY_STARS[rarity],
        "element":       d["element"],
        "weapon":        d["weapon"],
        "series":        "Wuthering Waves",
        "enabled":       True,
        "description":   d["description"],
        "image_url":     None,
        "image_file_id": None,
        "base_stats":    {
            "hp":      RARITY_HP[rarity],
            "attack":  RARITY_ATK[rarity],
            "defense": RARITY_DEF[rarity],
        },
        "drop_rate": RARITY_RATE[rarity],
    }
    data["cards"].append(new)
    save_json(data)

    await cb.message.edit_text(
        f"✅ <b>{new['name']}</b> qo'shildi!\n"
        f"📌 Kod: <code>{nc}</code>\n\n"
        + card_detail_text(new),
        parse_mode="HTML", reply_markup=card_detail_kb(new)
    )
    await cb.answer("✅ Saqlandi!", show_alert=True)


# ─── Give Card ──────────────────────────────────────────────
@router.callback_query(F.data == "acd_give")
async def give_start(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): return await cb.answer("❌")
    await state.set_state(GiveCardFSM.user_id)
    await cb.message.edit_text(
        "🎁 <b>KARTA BERISH</b>\n\n"
        "Foydalanuvchi <b>Telegram ID</b>sini yozing:",
        parse_mode="HTML", reply_markup=_cancel_btn()
    )
    await cb.answer()


@router.message(GiveCardFSM.user_id)
async def give_uid(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): await state.clear(); return
    if not msg.text.strip().isdigit():
        return await msg.answer("❌ Faqat raqam (Telegram ID) kiriting.")
    await state.update_data(target=int(msg.text.strip()))
    await state.set_state(GiveCardFSM.card_code)
    await msg.answer(
        "Karta <b>kodini</b> yozing (masalan: <code>WW001</code>):",
        parse_mode="HTML", reply_markup=_cancel_btn()
    )


@router.message(GiveCardFSM.card_code)
async def give_code(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id): await state.clear(); return
    d    = await state.get_data()
    code = msg.text.strip().upper()
    await state.clear()

    card = get_card(code)
    if not card:
        return await msg.answer(f"❌ <code>{code}</code> topilmadi.", parse_mode="HTML")

    from database.manager import get_user, add_card_to_user
    user = get_user(d["target"])
    if not user:
        return await msg.answer("❌ Bu ID dagi foydalanuvchi topilmadi.")

    is_new = add_card_to_user(d["target"], code)
    status = "✅ Yangi karta berildi!" if is_new else "ℹ️ Bu karta foydalanuvchida allaqachon bor."
    await msg.answer(
        f"{status}\n\n"
        f"👤 <b>{user['full_name']}</b>\n"
        f"🃏 {card['name']}  <code>{code}</code>",
        parse_mode="HTML", reply_markup=main_kb()
    )


# ─── Set Card Image via Reply ────────────────────────────────
# Foydalanish:
#   1. Chatga rasm tashlang
#   2. Shu rasmga REPLY qiling: /setimage WW001
# Natija: cards.json da image_file_id yangilanadi
#
@router.message(Command("setimage"))
async def set_image_via_reply(msg: Message):
    """
    Admin rasmga reply qilib /setimage WW001 deb yozadi.
    Bot o'sha rasmning file_id ni cards.json ga yozadi.
    """
    if not is_admin(msg.from_user.id):
        return

    # ── 1. Karta kodi tekshiruvi ──────────────────────────────
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        return await msg.reply(
            "❌ <b>Kod kiritilmadi.</b>\n\n"
            "To'g'ri foydalanish:\n"
            "1. Chatga rasm yuboring\n"
            "2. O'sha rasmga reply qiling: <code>/setimage 1</code>",
            parse_mode="HTML"
        )

    code = args[1].strip().upper()
    card = get_card(code)
    if not card:
        return await msg.reply(
            f"❌ <code>{code}</code> kodi topilmadi.\n"
            f"Mavjud kodlar: 1 – 42",
            parse_mode="HTML"
        )

    # ── 2. Reply xabar va rasm tekshiruvi ─────────────────────
    replied = msg.reply_to_message
    if not replied:
        return await msg.reply(
            "❌ <b>Rasmga reply qilmadingiz!</b>\n\n"
            "Qanday qilish kerak:\n"
            "1. Chatdagi rasmni toping\n"
            "2. U rasmga <b>Reply</b> bosing\n"
            f"3. Yozing: <code>/setimage {code}</code>",
            parse_mode="HTML"
        )

    # Rasm turini aniqlash (photo yoki document sifatida yuborilgan)
    file_id = None
    file_type = None

    if replied.photo:
        # Telegram photo — eng katta o'lchamni olish
        file_id   = replied.photo[-1].file_id
        file_type = "photo"
    elif replied.document and replied.document.mime_type and replied.document.mime_type.startswith("image/"):
        # Fayl sifatida yuborilgan rasm (original sifat)
        file_id   = replied.document.file_id
        file_type = "document"
    elif replied.sticker:
        file_id   = replied.sticker.file_id
        file_type = "sticker"
    else:
        return await msg.reply(
            "❌ <b>Reply qilingan xabarda rasm yo'q.</b>\n\n"
            "<i>Faqat rasm (photo) yoki rasm-fayl (document) bo'lishi kerak.</i>",
            parse_mode="HTML"
        )

    # ── 3. cards.json ga yozish ───────────────────────────────
    old_file_id = card.get("image_file_id")
    data = load_json()
    for c in data["cards"]:
        if c["code"] == code:
            c["image_file_id"] = file_id
            break
    save_json(data)

    # ── 4. Tasdiqlash xabari ──────────────────────────────────
    action = "Yangilandi" if old_file_id else "O'rnatildi"
    rem    = RARITY_EMOJI.get(card["rarity"], "⭐")
    em     = ELEMENT_EMOJIS.get(card["element"], "🔹")

    confirm_text = (
        f"✅ <b>Rasm {action}!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{rem} <b>{card['name']}</b>  {em}\n"
        f"📌 Kod: <code>{code}</code>\n"
        f"🖼️ Tur: <code>{file_type}</code>\n"
        f"🔑 File ID: <code>{file_id[:30]}...</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Endi /card {code} da rasm ko'rinadi.</i>"
    )

    # Preview: saqlangan rasmni ko'rsatamiz
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text=f"🃏 {card['name']} kartasini ko'r", callback_data=f"acd_card_{code}"),
    )
    b.row(
        InlineKeyboardButton(text="📋 Barcha kartalar", callback_data="acd_list_all"),
    )

    if file_type == "photo":
        await msg.reply_photo(
            photo   = file_id,
            caption = confirm_text,
            parse_mode="HTML",
            reply_markup=b.as_markup()
        )
    else:
        await msg.reply(confirm_text, parse_mode="HTML", reply_markup=b.as_markup())


@router.message(Command("saveimage"))
async def save_image_to_db(msg: Message):
    """
    Rasmga reply qilib /saveimage <kod> deb yozilsa, rasm faqat DB ga saqlanadi.
    """
    if not is_admin(msg.from_user.id): return

    args = msg.text.split()
    if len(args) < 2:
        return await msg.reply("Foydalanish: Rasmga reply qilib <code>/saveimage WW001</code> deb yozing.", parse_mode="HTML")

    code = args[1].strip().upper()
    replied = msg.reply_to_message
    if not replied:
        return await msg.reply("❌ Rasmga reply qiling!")

    file_id = None
    if replied.photo:
        file_id = replied.photo[-1].file_id
    elif replied.document and replied.document.mime_type and replied.document.mime_type.startswith("image/"):
        file_id = replied.document.file_id

    if not file_id:
        return await msg.reply("❌ Reply qilingan xabarda rasm topilmadi.")

    from database.manager import add_card_image
    add_card_image(code, file_id)

    await msg.reply(f"✅ Rasm <code>{code}</code> koleksiyasiga (DB) saqlandi.", parse_mode="HTML")
