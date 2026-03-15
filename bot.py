# bot.py
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, idle
from config import Config
from handlers import register_all_handlers

# ─── Logging Setup ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ─── Health Check Web Server (Required for Render) ───
async def health_check(request):
    """Health check endpoint for Render."""
    return web.Response(text="Anime Space Bot is running!", status=200)


async def start_health_server():
    """Start a simple HTTP server for Render health checks."""
    app_web = web.Application()
    app_web.router.add_get("/", health_check)
    app_web.router.add_get("/health", health_check)
    
    runner = web.AppRunner(app_web)
    await runner.setup()
    
    site = web.TCPSite(runner, "0.0.0.0", Config.PORT)
    await site.start()
    logger.info(f"Health check server started on port {Config.PORT}")


# ─── Bot Application ───
app = Client(
    name="AnimeSpaceBot",
    bot_token=Config.BOT_TOKEN,
    api_id=None,      # Not needed for bot-only usage via bot_token
    api_hash=None,     # Not needed for bot-only usage via bot_token
    # If you have API_ID and API_HASH, uncomment and add:
    # api_id=Config.API_ID,
    # api_hash=Config.API_HASH,
)


async def main():
    """Main entry point."""
    
    # Register all handlers
    register_all_handlers(app)
    
    # Start health check server for Render
    await start_health_server()
    
    # Start the bot
    await app.start()
    
    bot_info = await app.get_me()
    logger.info(f"Bot started: @{bot_info.username} ({bot_info.id})")
    logger.info(f"Storage Channel: {Config.STORAGE_CHANNEL_ID}")
    logger.info(f"Force Join: @{Config.FORCE_JOIN_CHANNEL}")
    logger.info(f"Auto-Delete Timer: {Config.AUTO_DELETE_SECONDS}s")
    logger.info(f"Admins: {Config.ADMIN_IDS}")
    
    # Keep the bot running
    await idle()
    
    # Cleanup
    await app.stop()
    logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())