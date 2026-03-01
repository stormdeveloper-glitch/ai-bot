# ai_core/offline.py
"""
Offline javoblar tizimi — Gemini API ishlamay qolganda ishlaydi.
Kalit so'zlar asosida eng mos javobni qaytaradi.
"""
import random
import re
from config import config

# ─── Javoblar bazasi ─────────────────────────────────────────────
RESPONSES = {
    "pull|wish|convene|gacha|summon": [
        "🎰 Pull qilish uchun /pull yoki /wish buyrug'ini ishlating!\n"
        "💎 1x pull = 160 Astrites\n"
        "🎲 10x pull = 1600 Astrites (kafolatlangan epik karta!)",

        "🌟 Gacha tizimi haqida:\n"
        "• Pity tizimi bor — 80 ta pull ga legendar karta kafolatlanadi\n"
        "• 60-pulldan boshlab (soft pity) ehtimollik oshadi\n"
        "• 10x pull da kamida 1 ta Epic yoki Legendary karta bo'ladi!",
    ],
    "karta|card|kolleksiya|collection|kol": [
        "🃏 Kartangizni ko'rish uchun:\n"
        "• /card [id] — ma'lum karta haqida\n"
        "• /collection — barcha kartalaringiz",

        "🎴 Noyob kartalar raritelari:\n"
        "• 💮 Celestia — Eng noyob (Legendary)\n"
        "• 🔮 Arcborne — Juda noyob (Epic)\n"
        "• 💫 Vibra — Noyob (Rare)\n"
        "• 🌀 Echo — Oddiy (Common)",
    ],
    "mana|mp|refine|luck|omad|bless|duo": [
        "🔮 Mana (MP) tizimi:\n"
        "• Sarguzasht davomida Mana yig'asiz (+15 har pull)\n"
        "• /refine — 1000 Mana → +5% Luck\n"
        "• /bless — 700 Mana bilan boshqaga Luck bering",

        "🍀 Luck (omad) darajasi qanchalik yuqori bo'lsa,\n"
        "noyob grimoirlar chiqish ehtimoli shunchalik ortadi!\n"
        "/refine buyrug'i bilan Mana'ni Luck ga aylantiring.",
    ],
    "profil|profile|stats|statistika": [
        "👤 Mage License (profilingiz)ni ko'rish uchun /profile buyrug'ini ishlating!\n"
        "U yerda:\n"
        "• 💎 Astrites miqdori\n"
        "• 🔮 Mana (MP) miqdori\n"
        "• 🍀 Luck darajasi\n"
        "• 📚 Grimoirlar soni\n"
        "• 🔄 Pity hisoblagich",
    ],
    "kunlik|daily|sovga|sovg": [
        "🎁 Kunlik sovg'a olish uchun /daily buyrug'ini ishlating!\n"
        "Har kuni 60 Astrites bepul olishingiz mumkin.",
    ],
    "astrites|pul|valyuta|currency|coin": [
        "⭐ Astrites — botdagi asosiy valyuta.\n"
        "Qanday yig'ish mumkin:\n"
        "• /daily — har kuni 60 Astrites\n"
        "• Pull natijasida (dublikat kartalar Astrites ga aylanadi)",
    ],
    "pity|kafolat|guarantee": [
        "🔄 Pity tizimi:\n"
        "• Har pull da hisoblagich +1 bo'ladi\n"
        "• 60-pulldan boshlab (soft pity) Legendary ehtimoli oshadi\n"
        "• 80-pull da (hard pity) Legendary 100% kafolatlanadi\n"
        "• Legendary olgandan keyin hisoblagich nolga tushadi",
    ],
    "admin|bosh": [
        "🛡️ Admin buyruqlari faqat adminlarga ko'rsatiladi.\n"
        "Agar admin bo'lsangiz, /admin buyrug'ini ishlating.",
    ],
    "yordam|help|qo'llanma|guide": [
        "📚 Asosiy buyruqlar:\n"
        "/start — Boshlash\n"
        "/pull yoki /wish — 1x pull\n"
        "/multipull yoki /convene — 10x pull\n"
        "/profile — Profilingiz\n"
        "/daily — Kunlik sovg'a\n"
        "/collection — Kartalaringiz\n"
        "/refine — Aura → Luck\n"
        "/ai — AI yordamchi",
    ],
    "salom|hello|hi|hey|assalomu": [
        f"👋 Salom. Men {config.BOT_NAME}man. Men senga sehrli sayohatingda yordam beraman.\n"
        "Savollaring bo'lsa, /ai orqali so'ra.",

        f"✨ Assalomu alaykum. {config.BOT_NAME}'s Journey'ga xush kelibsiz.\n"
        "Sizga sayohatingizda qanday yordam bera olaman?",
    ],
    "rahmat|thanks|tashakkur|spasibo": [
        "😊 Arzimaydi! Yana savol bo'lsa murojaat qiling!",
        "🌟 Xush kelibsiz! Boshqa savolingiz bo'lsa — bemalol so'rang!",
    ],
}

# ─── Default javoblar ───────────────────────────────────────────
DEFAULT_RESPONSES = [
    "🤖 Kechirasan, seni tushunmadim. Men uzoq umr ko'rganman, lekin hamma narsani ham bilmayman.\n"
    "Yordam uchun /help buyrug'ini ishlating.",

    "🔍 Bu mavzu bo'yicha bilimga ega emasman. Kutubxonadan (help'dan) qidirib ko'r.",

    "💡 Aniqroq so'ra. Sehr-jodu aniqlikni yoqtiradi.",
]


def find_offline_response(message: str) -> str:
    """Find the best offline response for the given message."""
    msg_lower = message.lower()

    for pattern, answers in RESPONSES.items():
        keywords = pattern.split("|")
        if any(kw in msg_lower for kw in keywords):
            return random.choice(answers)

    return random.choice(DEFAULT_RESPONSES)
