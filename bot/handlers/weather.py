# bot/handlers/weather.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from utils.weather import get_today_bonus, format_weather_card

router = Router(name="weather")


@router.message(Command("weather", "obhavo"))
async def weather_command(msg: Message):
    await msg.answer("⏳ Ob-havo ma'lumotlari yuklanmoqda...")
    bonus = await get_today_bonus()
    text = format_weather_card(bonus)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_weather"),
        InlineKeyboardButton(text="🔙 Menu", callback_data="back_to_menu"),
    )
    await msg.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())


@router.callback_query(F.data == "refresh_weather")
async def refresh_weather(cb: CallbackQuery):
    await cb.answer("⏳ Yangilanmoqda...")
    bonus = await get_today_bonus()
    text = format_weather_card(bonus)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_weather"),
        InlineKeyboardButton(text="🔙 Menu", callback_data="back_to_menu"),
    )
    await cb.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
