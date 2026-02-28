# ai_core/engine.py
import hashlib
import time
import structlog
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from config import config
from ai_core.cache import get_cached_response, set_cached_response
from ai_core.database import add_to_history, get_recent_history
from ai_core.offline import find_offline_response

log = structlog.get_logger()

# Configure the Gemini API
genai.configure(api_key=config.GEMINI_API_KEY)

MODEL_NAME = "gemini-1.5-flash"

SYSTEM_PROMPT = """
Sen "AuraX" — anime va gacha o'yinlarida mutaxassis bo'lgan AI yordamchisisan.
Sening asosiy vazifalaring:
- Foydalanuvchilarga karta kolleksiyasi bo'yicha maslahat berish
- Gacha tizimlarini tushuntirish
- Bot buyruqlari haqida yordam berish
- Qisqa, aniq va do'stona javoblar berish (Telegram uchun)

Qoidalar:
- Har doim O'zbek tilida javob ber
- Javoblarni qisqa va aniq qil (max 200 so'z)
- Emoji ishlat, lekin ortiqcha emas
- Agar bilmasang, ochiqchasiga ayt
"""

def build_prompt(history: list, user_message: str) -> str:
    """Build a conversation prompt from history and new message."""
    prompt_parts = [SYSTEM_PROMPT, "\n\n---\n"]
    for role, content in history:
        prefix = "Foydalanuvchi" if role == "user" else "AuraX"
        prompt_parts.append(f"{prefix}: {content}")
    prompt_parts.append(f"Foydalanuvchi: {user_message}")
    prompt_parts.append("AuraX:")
    return "\n".join(prompt_parts)

async def get_ai_response(user_id: int, message: str) -> tuple[str, float, bool]:
    """
    Get an AI response for the given message.
    Returns (response_text, latency_ms, is_online).
    is_online=False means offline fallback was used.
    """
    # Check cache first
    cache_key = hashlib.md5(f"{user_id}:{message}".encode()).hexdigest()
    cached = get_cached_response(cache_key)
    if cached:
        log.info("ai_cache_hit", user_id=user_id)
        return cached, 0.0, True

    # If no API key configured, go offline immediately
    if not config.GEMINI_API_KEY:
        log.warning("ai_no_api_key", user_id=user_id)
        return find_offline_response(message), 0.0, False

    # Get chat history
    history = get_recent_history(user_id, limit=6)
    prompt = build_prompt(history, message)

    # Call Gemini API
    start = time.perf_counter()
    is_online = True
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        log.info("ai_online_response", user_id=user_id,
                 latency_ms=round((time.perf_counter() - start) * 1000, 2))

    except (ResourceExhausted, ServiceUnavailable) as e:
        # API limit yoki server muammosi — offline rejimga o'tish
        log.warning("ai_fallback_offline", user_id=user_id, reason=str(e)[:60])
        response_text = find_offline_response(message)
        is_online = False

    except Exception as e:
        log.error("ai_error", user_id=user_id, error=str(e)[:80])
        response_text = find_offline_response(message)
        is_online = False

    latency_ms = (time.perf_counter() - start) * 1000

    # Save to history and cache only for online responses
    if is_online:
        add_to_history(user_id, "user", message)
        add_to_history(user_id, "assistant", response_text)
        set_cached_response(cache_key, response_text, expire=1800)

    return response_text, latency_ms, is_online
