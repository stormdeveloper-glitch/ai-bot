import hashlib
import time
import asyncio
import structlog
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable

from config import config
from ai_core.cache import get_cached_response, set_cached_response
from ai_core.database import add_to_history, get_recent_history
from ai_core.offline import find_offline_response

log = structlog.get_logger()

AI_CONFIG_PATH = "data/ai.json"

def load_ai_config():
    import os, json
    default = {
        "system_prompt": "Sening isming {bot_name}. Sen sehgarisan.",
        "model_name": "gemini-1.5-flash",
        "max_history": 6,
        "cache_expire": 1800
    }
    if os.path.exists(AI_CONFIG_PATH):
        try:
            with open(AI_CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return default
    return default

ai_settings = load_ai_config()

# Configure the Gemini API
genai.configure(api_key=config.GEMINI_API_KEY)

def get_system_prompt():
    prompt_template = ai_settings.get("system_prompt", "")
    base_prompt = prompt_template.replace("{bot_name}", config.BOT_NAME)
    
    # Inject learned facts
    facts = ai_settings.get("learned_facts", [])
    if facts:
        base_prompt += "\n\nO'rganilgan ma'lumotlar:\n" + "\n".join(f"- {f}" for f in facts)
        
    return base_prompt

def build_prompt(history: list, user_message: str) -> str:
    """Build a conversation prompt from history and new message."""
    prompt_parts = [get_system_prompt(), "\n\n---\n"]
    for role, content in history:
        prefix = "Foydalanuvchi" if role == "user" else config.BOT_NAME
        prompt_parts.append(f"{prefix}: {content}")
    prompt_parts.append(f"Foydalanuvchi: {user_message}")
    prompt_parts.append(f"{config.BOT_NAME}:")
    return "\n".join(prompt_parts)

async def process_learning(user_message: str, ai_response: str):
    """
    Extract useful facts from the conversation and store them in ai.json.
    Includes a smart filter to avoid 'trash' info.
    """
    learning_prompt = f"""
    Suhbatni tahlil qil va yangi, foydali va aniq faktlar borligini aniqla. 
    Faqatgina kelajakda kerak bo'lishi mumkin bo'lgan ma'lumotlarni ajrat.
    Agar ma'lumot axlat, haqorat yoki foydasiz bo'lsa (masalan: salom, xayr, bot lox va h.k.), e'tiborsiz qoldir.
    
    Suhbat:
    User: {user_message}
    AI: {ai_response}
    
    Yangi fakt topilsa, uni qisqa, tushunarli qilib O'zbek tilida qaytar.
    Hech qanday fakt topilmasa yoki ma'lumot foydasiz bo'lsa, FAQATgina 'NULL' so'zini qaytar.
    """
    
    try:
        model = genai.GenerativeModel(ai_settings.get("model_name", "gemini-1.5-flash"))
        response = await model.generate_content_async(learning_prompt)
        fact = response.text.strip()
        
        if fact != "NULL" and len(fact) > 5:
            # Atomic update of ai.json
            import json, os
            if os.path.exists(AI_CONFIG_PATH):
                with open(AI_CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                if "learned_facts" not in data:
                    data["learned_facts"] = []
                
                if fact not in data["learned_facts"]:
                    data["learned_facts"].append(fact)
                    with open(AI_CONFIG_PATH, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    # Update global ai_settings
                    ai_settings["learned_facts"] = data["learned_facts"]
                    log.info("ai_learned_new_fact", fact=fact)
                    
    except Exception as e:
        log.error("ai_learning_error", error=str(e))

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
    history = get_recent_history(user_id, limit=ai_settings.get("max_history", 6))
    prompt = build_prompt(history, message)

    # Call Gemini API
    start = time.perf_counter()
    is_online = True
    try:
        model = genai.GenerativeModel(ai_settings.get("model_name", "gemini-1.5-flash"))
        response = await model.generate_content_async(prompt)
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
        set_cached_response(cache_key, response_text, expire=ai_settings.get("cache_expire", 1800))
        
        # Start learning process in background
        asyncio.create_task(process_learning(message, response_text))

    return response_text, latency_ms, is_online
