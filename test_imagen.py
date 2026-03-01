import asyncio
import aiohttp
import base64
import os
import sys

# Ad-hoc setup to import config
sys.path.append(os.getcwd())
from config import config

IMAGEN_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "imagen-3.0-generate-002:predict"
)

async def test():
    api_key = config.NANO_BANANA_API_KEY or config.GEMINI_API_KEY
    if not api_key:
        print("Error: No API key found in .env or config.")
        return

    print(f"Using API Key ending in: ...{api_key[-5:]}")
    
    prompt = "a cute robot with a lightbulb"
    payload = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "1:1",
        },
    }

    headers = {"Content-Type": "application/json"}
    url = f"{IMAGEN_API_URL}?key={api_key}"

    print(f"Testing Imagen API with prompt: '{prompt}'")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                print(f"Response Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    preds = data.get("predictions", [])
                    if preds:
                        print(f"Success! Received {len(preds)} prediction(s).")
                    else:
                        print("Error: No predictions in response.")
                else:
                    error_text = await resp.text()
                    print(f"API Error: {error_text}")
    except Exception as e:
        print(f"Exception during API call: {e}")

if __name__ == "__main__":
    asyncio.run(test())
