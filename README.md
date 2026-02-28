# 🎮 Anime Card Collector Bot

Telegram anime karta to'plash boti — Gacha tizimi, profil, koleksiya va reyting.

---

## 📁 Fayl Strukturasi

```
anime_card_bot/
├── main.py                    ← Ishga tushirish
├── config.py                  ← Barcha sozlamalar
├── requirements.txt
├── .env.example               ← Token namunasi
│
├── data/
│   └── cards.json             ← Karta ma'lumotlari (JSON)
│
├── database/
│   ├── manager.py             ← SQLite CRUD
│   └── bot.db                 ← Avtomatik yaratiladi
│
├── utils/
│   └── cards.py               ← Gacha engine + formatter
│
└── bot/
    ├── handlers/
    │   ├── start.py            ← /start, /help, menu
    │   ├── card.py             ← /card [kod]
    │   ├── profile.py          ← /profile, /daily
    │   ├── gacha.py            ← /pull, /multipull
    │   ├── collection.py       ← /collection, /top
    │   └── admin.py            ← /admin, /give, /addcard
    ├── keyboards/
    │   └── inline.py           ← Inline tugmalar
    └── middlewares/
        └── rate_limit.py       ← Spam himoya
```

---

## ⚙️ O'rnatish

### 1. Muhit tayyorlash
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# yoki
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 2. Token sozlash
```bash
cp .env.example .env
```
`.env` faylini ochib `BOT_TOKEN` ni to'ldiring:
```
BOT_TOKEN=sizning_tokeningiz
ADMIN_IDS=sizning_telegram_id
```

### 3. Ishga tushirish
```bash
python main.py
```

---

## 🎮 Buyruqlar

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Bosh menu |
| `/help` | Buyruqlar ro'yxati |
| `/profile` | Profilingiz (stats, pity) |
| `/card WW001` | Karta ma'lumoti |
| `/collection` | Koleksiyangiz |
| `/pull` | 1x pull (160 ⭐) |
| `/multipull` | 10x pull (1600 ⭐) |
| `/daily` | Kunlik sovg'a (60 ⭐) |
| `/top` | Top 10 reyting |

### Admin buyruqlari
| Buyruq | Tavsif |
|--------|--------|
| `/admin` | Admin panel |
| `/give <user_id> <miqdor>` | Foydalanuvchiga Astrites berish |
| `/addcard <user_id> <kod>` | Kartani qo'shib berish |

---

## 🃏 cards.json ga karta qo'shish

```json
{
  "id": 11,
  "code": "WW011",
  "name": "Yangi Karakter",
  "title": "Unvon",
  "rarity": "Legendary",
  "rarity_stars": 5,
  "element": "Fusion",
  "weapon": "Sword",
  "series": "Wuthering Waves",
  "description": "Tavsif matni",
  "image_url": "https://...",
  "image_file_id": null,
  "base_stats": { "hp": 10000, "attack": 450, "defense": 300 },
  "drop_rate": 0.7
}
```

### Rasmlarni bot orqali keshlashtirish
Bot birinchi marta rasmni Telegram ga yuborganda, `file_id` ni olib `image_file_id` ga saqlang.
Bu tezlikni 10x oshiradi (Telegram CDN dan tez yuklanadi).

---

## ⭐ Pity Tizimi

- **60-pull:** Yumshoq pity — Legendary ehtimoli oshib boradi
- **80-pull:** Kafolatlangan Legendary!
- Multi-pull (10x) da kamida 1 ta Epic garantiyalangan

---

## 📊 Ma'lumotlar Bazasi

SQLite, 3 ta jadval:
- `users` — Profil, astrites, pity, statistika
- `user_cards` — Kimda qaysi karta bor (unique constraint)
- `pull_history` — Barcha pull loglari

---

## 🔧 Kengaytirish

Yangi seriya qo'shish uchun faqat `data/cards.json` ga yangi kartalar qo'shing —
kod o'zgarmaydi. Rarity, element va weapon emoji'lari ham JSON da boshqariladi.
