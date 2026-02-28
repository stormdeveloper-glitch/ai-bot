# bot/keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎴 Mening koleksiyam",  callback_data="my_collection"),
        InlineKeyboardButton(text="👤 Profilim",           callback_data="my_profile"),
    )
    builder.row(
        InlineKeyboardButton(text="🎰 1x Pull (160 ⭐)",   callback_data="pull_single"),
        InlineKeyboardButton(text="🎲 10x Pull (1600 ⭐)", callback_data="pull_multi"),
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Kunlik sovg'a",      callback_data="daily_reward"),
        InlineKeyboardButton(text="🏆 Reyting",            callback_data="leaderboard"),
    )
    builder.row(
        InlineKeyboardButton(text="📖 Barcha kartalar",    callback_data="all_cards"),
    )
    return builder.as_markup()


def pull_confirm_kb(pull_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    cost = "160 ⭐" if pull_type == "single" else "1,600 ⭐"
    count = "1x" if pull_type == "single" else "10x"
    builder.row(
        InlineKeyboardButton(
            text=f"✅ Ha, {count} pull ({cost})",
            callback_data=f"confirm_pull_{pull_type}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")
    )
    return builder.as_markup()


def collection_nav_kb(page: int, total_pages: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"col_page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"col_page_{page+1}"))
    builder.row(*nav)
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu"))
    return builder.as_markup()


def back_kb(callback: str = "back_to_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎰 Yana pull", callback_data="pull_single"),
        InlineKeyboardButton(text="🔙 Menu",      callback_data="back_to_menu"),
    )
    return builder.as_markup()


def multi_pull_back_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎲 Yana 10x",    callback_data="pull_multi"),
        InlineKeyboardButton(text="👜 Koleksiya",   callback_data="my_collection"),
        InlineKeyboardButton(text="🔙 Menu",        callback_data="back_to_menu"),
    )
    return builder.as_markup()


def admin_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📊 Statistika",      callback_data="admin_stats"),
        InlineKeyboardButton(text="📢 Xabar yuborish",  callback_data="admin_broadcast"),
    )
    builder.row(
        InlineKeyboardButton(text="➕ Karta qo'shish",   callback_data="admin_add_card"),
        InlineKeyboardButton(text="🔙 Orqaga",           callback_data="back_to_menu"),
    )
    return builder.as_markup()


def admin_cardstatus_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🃏 Karta menejeri", callback_data="open_card_manager"),
        InlineKeyboardButton(text="🔙 Admin panel",    callback_data="admin_back"),
    )
    return builder.as_markup()
