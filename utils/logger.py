# utils/logger.py
import logging
import sys
import os
from datetime import datetime

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Main logger configuration
LOG_FILE = f"logs/bot_{datetime.now().strftime('%Y-%m-%d')}.log"

def setup_logger():
    """Setup global logging to both console and file."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding='utf-8')
        ]
    )
    
    # Suppress verbose logs from some libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

def get_logger(name: str):
    return logging.getLogger(name)
