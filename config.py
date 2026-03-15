# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot Token from BotFather
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    
    # MongoDB URI
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://username:password@cluster.mongodb.net/anime_space")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "anime_space_bot")
    
    # Storage Channel ID (private channel where files are stored)
    # Must include -100 prefix for supergroups/channels
    STORAGE_CHANNEL_ID = int(os.getenv("STORAGE_CHANNEL_ID", "0"))
    
    # Force Join Channel/Group username (without @)
    FORCE_JOIN_CHANNEL = os.getenv("FORCE_JOIN_CHANNEL", "AnimeSpace")
    
    # Force Join Channel ID (for API verification)
    FORCE_JOIN_CHANNEL_ID = int(os.getenv("FORCE_JOIN_CHANNEL_ID", "0"))
    
    # Admin User IDs (comma-separated)
    ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "0").split(",")))
    
    # Auto-delete timer in seconds (default 15 minutes = 900 seconds)
    AUTO_DELETE_SECONDS = int(os.getenv("AUTO_DELETE_SECONDS", "900"))
    
    # Bot Username (without @)
    BOT_USERNAME = os.getenv("BOT_USERNAME", "Anime_Space_Bot")
    
    # Web App URL (optional - for web-based viewing)
    WEB_APP_URL = os.getenv("WEB_APP_URL", "")
    
    # Render Web Service Port
    PORT = int(os.getenv("PORT", "10000"))
    
    # Render External URL (for webhook)
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    
    # Whether to use webhook (True for Render) or polling (False for local)
    USE_WEBHOOK = os.getenv("USE_WEBHOOK", "True").lower() == "true"