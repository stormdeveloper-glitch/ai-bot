# utils/weather.py
"""
OpenWeatherMap API integratsiyasi.
Ob-havoga qarab gacha bonus tizimi.
"""
import aiohttp
from config import config

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# ─── Ob-havo bonuslari ────────────────────────────────────────
# OpenWeatherMap "weather id" asosida bonuslar
# https://openweathermap.org/weather-conditions
WEATHER_BONUSES = {
    "thunderstorm": {
        "emoji": "⛈️",
        "name": "Bo'ron",
        "pity_bonus": 5,       # Pity ga +5
        "luck_bonus": 0.0,
        "aura_mult": 1.0,
        "daily_mult": 1.0,
        "desc": "⚡ Bo'ron kuchi: Pity +5 bonus!",
    },
    "drizzle": {
        "emoji": "🌦️",
        "name": "Mayda yomg'ir",
        "pity_bonus": 0,
        "luck_bonus": 2.0,
        "aura_mult": 1.5,
        "daily_mult": 1.0,
        "desc": "💧 Mayda yomg'ir: Aura ×1.5 bonus!",
    },
    "rain": {
        "emoji": "🌧️",
        "name": "Yomg'ir",
        "pity_bonus": 0,
        "luck_bonus": 0.0,
        "aura_mult": 2.0,
        "daily_mult": 1.0,
        "desc": "🌧️ Yomg'irli kun: Aura ×2 bonus!",
    },
    "snow": {
        "emoji": "❄️",
        "name": "Qor",
        "pity_bonus": 0,
        "luck_bonus": 0.0,
        "aura_mult": 1.0,
        "daily_mult": 2.0,
        "desc": "❄️ Qorli kun: Kunlik sovg'a ×2!",
    },
    "clear": {
        "emoji": "☀️",
        "name": "Ochiq havo",
        "pity_bonus": 0,
        "luck_bonus": 10.0,
        "aura_mult": 1.0,
        "daily_mult": 1.0,
        "desc": "☀️ Quyoshli kun: +10% Luck bonus!",
    },
    "clouds": {
        "emoji": "☁️",
        "name": "Bulutli",
        "pity_bonus": 2,
        "luck_bonus": 2.0,
        "aura_mult": 1.2,
        "daily_mult": 1.0,
        "desc": "☁️ Bulutli kun: Luck +2%, Pity +2, Aura ×1.2",
    },
}

DEFAULT_BONUS = {
    "emoji": "🌍",
    "name": "Normal",
    "pity_bonus": 0,
    "luck_bonus": 0.0,
    "aura_mult": 1.0,
    "daily_mult": 1.0,
    "desc": "Bugun bonus yo'q.",
}


async def get_weather(city: str = None) -> dict | None:
    """Fetch weather data for the configured or given city."""
    city = city or config.WEATHER_CITY
    if not config.WEATHER_API_KEY or not city:
        return None

    params = {
        "q": city,
        "appid": config.WEATHER_API_KEY,
        "units": "metric",
        "lang": "uz",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(BASE_URL, params=params, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception:
        return None
    return None


def parse_bonus(weather_data: dict) -> dict:
    """Parse weather data and return the corresponding bonus dict."""
    if not weather_data:
        return DEFAULT_BONUS

    condition_id = weather_data.get("weather", [{}])[0].get("id", 800)

    if 200 <= condition_id < 300:
        key = "thunderstorm"
    elif 300 <= condition_id < 400:
        key = "drizzle"
    elif 400 <= condition_id < 600:
        key = "rain"
    elif 600 <= condition_id < 700:
        key = "snow"
    elif condition_id == 800:
        key = "clear"
    else:
        key = "clouds"

    bonus = WEATHER_BONUSES[key].copy()

    # Attach raw weather info
    bonus["temp"] = round(weather_data.get("main", {}).get("temp", 0))
    bonus["humidity"] = weather_data.get("main", {}).get("humidity", 0)
    bonus["wind"] = round(weather_data.get("wind", {}).get("speed", 0), 1)
    bonus["city"] = weather_data.get("name", config.WEATHER_CITY)

    return bonus


async def get_today_bonus(city: str = None) -> dict:
    """Get today's weather-based gacha bonus."""
    data = await get_weather(city)
    return parse_bonus(data)


def format_weather_card(bonus: dict) -> str:
    """Format weather bonus as a Telegram message."""
    return (
        f"{bonus['emoji']} <b>Bugungi Ob-havo Bonusi</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📍 Shahar: <b>{bonus.get('city', '—')}</b>\n"
        f"🌡️ Harorat: <b>{bonus.get('temp', '—')}°C</b>\n"
        f"💧 Namlik: <b>{bonus.get('humidity', '—')}%</b>\n"
        f"💨 Shamol: <b>{bonus.get('wind', '—')} m/s</b>\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🎁 <b>Bugungi bonus:</b>\n"
        f"{bonus['desc']}\n\n"
        + (f"🍀 Luck: +<b>{bonus['luck_bonus']:.0f}%</b>\n" if bonus['luck_bonus'] else "")
        + (f"🔮 Aura: ×<b>{bonus['aura_mult']}</b>\n" if bonus['aura_mult'] != 1.0 else "")
        + (f"🎁 Daily: ×<b>{bonus['daily_mult']}</b>\n" if bonus['daily_mult'] != 1.0 else "")
        + (f"🔄 Pity: +<b>{bonus['pity_bonus']}</b>\n" if bonus['pity_bonus'] else "")
    )
