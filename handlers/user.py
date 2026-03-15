# handlers/user.py
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database import db
from utils.force_join import check_force_join, force_join_message


async def help_command(client: Client, message: Message):
    """Handle /help command."""
    text = (
        "📖 **Help & Commands**\n\n"
        "**How to use this bot:**\n\n"
        "1️⃣ Join our main channel: @{channel}\n"
        "2️⃣ Find the anime/episode you want\n"
        "3️⃣ Click the download button/link\n"
        "4️⃣ The bot will send you the file\n"
        "5️⃣ Download before auto-delete timer expires!\n\n"
        "**User Commands:**\n"
        "▸ `/start` - Start the bot\n"
        "▸ `/help` - Show this help\n"
        "▸ `/about` - About this bot\n"
        "▸ `/mystats` - Your usage stats\n\n"
        "**⏰ Auto-Delete:**\n"
        "Files are automatically deleted after "
        "{minutes} minutes. Forward files to your "
        "**Saved Messages** to keep them permanently!\n\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    ).format(
        channel=Config.FORCE_JOIN_CHANNEL,
        minutes=Config.AUTO_DELETE_SECONDS // 60
    )
    
    await message.reply_text(text)


async def about_command(client: Client, message: Message):
    """Handle /about command."""
    text = (
        "🤖 **About Anime Space Bot**\n\n"
        "This bot is designed to deliver anime episodes "
        "directly to your Telegram chat.\n\n"
        "**Features:**\n"
        "✅ Fast file delivery\n"
        "✅ Auto-delete for privacy\n"
        "✅ Batch download support\n"
        "✅ Episode organization\n\n"
        f"📢 **Channel:** @{Config.FORCE_JOIN_CHANNEL}\n"
        f"🤖 **Bot:** @{Config.BOT_USERNAME}\n\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await message.reply_text(text)


async def my_stats_command(client: Client, message: Message):
    """Show user's personal stats."""
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    if user:
        text = (
            "📊 **Your Statistics**\n\n"
            f"🆔 User ID: `{user_id}`\n"
            f"📁 Files Received: `{user.get('files_received', 0)}`\n"
            f"📅 Joined: `{user.get('joined_date', 'Unknown')}`\n"
            f"🕐 Last Active: `{user.get('last_active', 'Unknown')}`\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = "❌ No stats found. Use /start first!"
    
    await message.reply_text(text)


def register_user_handlers(app: Client):
    """Register user command handlers."""
    app.on_message(filters.command("help") & filters.private)(help_command)
    app.on_message(filters.command("about") & filters.private)(about_command)
    app.on_message(filters.command("mystats") & filters.private)(my_stats_command)