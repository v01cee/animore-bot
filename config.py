"""Configuration — loads secrets from .env file."""

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# Telegram bot API limit for file uploads
TELEGRAM_FILE_LIMIT_MB = 50

# Allowed Telegram user IDs (only these users can interact with the bot)
ADMIN_IDS = [1133696726, 5818121757]

# Proxy for yt-dlp (needed if server IP is blocked by TikTok)
# Format: socks5://user:pass@host:port or http://host:port
PROXY_URL = os.getenv("PROXY_URL", "")
