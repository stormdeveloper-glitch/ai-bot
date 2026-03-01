# utils/imagen.py
"""
Google Imagen — AI rasm generatsiyasi.
NANO_BANANA_API_KEY orqali ishlaydi (Google AI Studio key).
"""
import asyncio
import aiohttp
import base64
from config import config
from utils.logger import get_logger

logger = get_logger("imagen")

IMAGEN_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "imagen-3.0-generate-002:predict"
)


async def generate_image(prompt: str, count: int = 1) -> list[bytes] | None:
    """
    Generate image(s) using Google Imagen API.
    Returns list of raw PNG bytes, or None on failure.
    """
    api_key = config.NANO_BANANA_API_KEY or config.GEMINI_API_KEY
    if not api_key:
        return None

    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": min(count, 4),
            "aspectRatio": "1:1",
            "personGeneration": "allow_adult",
            "enhancePrompt": True
        },
    }

    headers = {"Content-Type": "application/json"}
    url = f"{IMAGEN_API_URL}?key={api_key}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    images = []
                    predictions = data.get("predictions", [])
                    if not predictions:
                        logger.warning(f"Imagen API: No predictions. Response: {data}")
                        return None
                        
                    for pred in predictions:
                        b64 = pred.get("bytesBase64Encoded")
                        if b64:
                            images.append(base64.b64decode(b64))
                        else:
                            # Check for safety attributes or other reasons
                            logger.warning(f"Imagen API: Prediction missing bytes. Data: {pred}")
                    return images if images else None
                else:
                    error = await resp.text()
                    logger.error(f"Imagen API Error {resp.status}: {error}")
                    return None
    except Exception as e:
        logger.error(f"Imagen Exception: {str(e)}")
        return None
