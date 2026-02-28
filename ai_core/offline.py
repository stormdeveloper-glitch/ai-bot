# ai_core/offline.py
"""
Offline javoblar tizimi — Gemini API ishlamay qolganda ishlaydi.
Kalit so'zlar asosida eng mos javobni qaytaradi.
"""
import random
import re

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
    "aura|refine|luck|omad|bless|duo": [
        "🔮 Aura tizimi:\n"
        "• Pull qilganda Aura yig'asiz (+15 har pull)\n"
        "• /refine — 1000 Aura → +5% Luck\n"
        "• /bless — 700 Aura bilan boshqaga Luck bering",

        "🍀 Luck (omad) darajasi qanchalik yuqori bo'lsa,\n"
        "noyob kartalar chiqish ehtimoli shunchalik ortadi!\n"
        "/refine buyrug'i bilan Aura ni Luck ga aylantiring.",
    ],
    "profil|profile|stats|statistika": [
        "👤 Profilingizni ko'rish uchun /profile buyrug'ini ishlating!\n"
        "U yerda:\n"
        "• 💎 Astrites miqdori\n"
        "• 🔮 Aura miqdori\n"
        "• 🍀 Luck darajasi\n"
        "• 🎴 Kartalar soni\n"
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
        "👋 Salom! Men AuraX AI yordamchisiman.\n"
        "Gacha, kartalar, va bot haqida savol bering!",

        "✨ Assalomu alaykum! AuraX botiga xush kelibsiz!\n"
        "Qanday yordam bera olaman?",
    ],
    "rahmat|thanks|tashakkur|spasibo": [
        "😊 Arzimaydi! Yana savol bo'lsa murojaat qiling!",
        "🌟 Xush kelibsiz! Boshqa savolingiz bo'lsa — bemalol so'rang!",
    ],
}

# ─── Default javoblar ───────────────────────────────────────────
DEFAULT_RESPONSES = [
    "🤖 Savolingizni tushunmadim. Boshqacha so'rab ko'ring.\n"
    "Yordam uchun /help buyrug'ini ishlating.",

    "🔍 Bu mavzu bo'yicha ma'lumotim cheklangan. /help orqali mavjud buyruqlarni ko'ring.",

    "💡 Aniqroq savol bersangiz, yaxshiroq javob bera olaman!\n"
    "Masalan: 'pull qanday ishlaydi?' yoki 'aura nima?'",
]


def find_offline_response(message: str) -> str:
    """Find the best offline response for the given message."""
    msg_lower = message.lower()

    for pattern, answers in RESPONSES.items():
        keywords = pattern.split("|")
        if any(kw in msg_lower for kw in keywords):
            return random.choice(answers)

    return random.choice(DEFAULT_RESPONSES)
