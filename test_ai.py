# test_ai.py
import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

async def test():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment!")
        return
    print(f"Testing with API Key: {api_key[:10]}...")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    print("Sending async request...")
    try:
        response = await model.generate_content_async("Salom, kimsan?")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
