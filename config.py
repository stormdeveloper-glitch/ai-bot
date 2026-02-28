# config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file
load_dotenv()

@dataclass
class Config:
    # ─── Telegram ───────────────────────────────────────────
    BOT_TOKEN: str      = os.getenv("BOT_TOKEN", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    NANO_BANANA_API_KEY: str = os.getenv("NANO_BANANA_API_KEY", "")
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    WEATHER_CITY: str   = os.getenv("WEATHER_CITY", "Toshkent")
    ADMIN_IDS: list     = None

    # ─── Paths ──────────────────────────────────────────────
    DB_PATH: str    = "database/bot.db"
    CARDS_JSON: str = "data/cards.json"

    # ─── Gacha Settings ─────────────────────────────────────
    PULL_COST: int          = 160       # Astrites per pull
    MULTI_PULL_COUNT: int   = 10        # pulls in multi-pull
    PITY_SOFT: int          = 60        # soft pity starts
    PITY_HARD: int          = 80        # guaranteed legendary
    DAILY_ASTRITES: int     = 60        # daily reward
    STARTING_ASTRITES: int  = 1600      # new user bonus (10 pulls)

    # ─── Aura & Luck ────────────────────────────────────────
    AURA_REFINE_COST: int   = 1000      # Aura to Luck
    LUCK_PER_REFINE: float  = 5.0       # Luck % per refine
    BLESS_AURA_COST: int    = 700       # Aura to bless others
    BLESS_LUCK_GIVEN: float = 5.0       # Luck % given to others

    # ─── Rate Limiting ──────────────────────────────────────
    RATE_LIMIT_MESSAGES: int = 5
    RATE_LIMIT_SECONDS: int  = 10

    def __post_init__(self):
        if self.ADMIN_IDS is None:
            admin_str = os.getenv("ADMIN_IDS", "")
            self.ADMIN_IDS = [
                int(x) for x in admin_str.split(",")
                if x.strip().isdigit()
            ]

config = Config()
