# ai_core/cache.py
import diskcache as dc
import os

# Ensure data directory exists
os.makedirs("data/cache", exist_ok=True)

cache = dc.Cache("data/cache/ai_response")

def get_cached_response(prompt_hash: str):
    """Retrieve response from cache if it exists."""
    return cache.get(prompt_hash)

def set_cached_response(prompt_hash: str, response: str, expire: int = 3600):
    """Store response in cache with an expiration (default 1 hour)."""
    cache.set(prompt_hash, response, expire=expire)
