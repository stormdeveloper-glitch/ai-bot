# config.py
import os
import json
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
    PROFILE_IMAGE_URL: str = "https://i.imgur.com/8YlQ3L3.jpeg"  # Frieren-themed background
    BOT_NAME: str       = "FRIEREN"

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
        # Load from config.json if it exists
        config_path = "config.json"
        instance_name = os.getenv("BOT_INSTANCE_NAME")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    bots = data.get("bots", [])
                    
                    # Find instance by name or use default
                    bot_config = None
                    if instance_name:
                        bot_config = next((b for b in bots if b["name"] == instance_name), None)
                    
                    if not bot_config:
                        bot_config = next((b for b in bots if b.get("is_default")), None)
                    
                    if bot_config:
                        if bot_config.get("token"):
                            self.BOT_TOKEN = bot_config["token"]
                        if bot_config.get("admin_ids"):
                            self.ADMIN_IDS = bot_config["admin_ids"]
                        if bot_config.get("name"):
                            self.BOT_NAME = bot_config["name"]
                        # You can add more fields here as needed
            except Exception as e:
                print(f"Error loading config.json: {e}")

        # Final fallback for ADMIN_IDS from .env if still None
        if self.ADMIN_IDS is None:
            admin_str = os.getenv("ADMIN_IDS", "")
            self.ADMIN_IDS = [
                int(x) for x in admin_str.split(",")
                if x.strip().isdigit()
            ]

config = Config()
