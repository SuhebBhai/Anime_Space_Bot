# handlers/callbacks.py
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import db


async def callback_handler(client: Client, callback: CallbackQuery):
    """Handle all inline keyboard callbacks."""
    data = callback.data
    user_id = callback.from_user.id
    
    if data == "help_menu":
        text = (
            "📖 **Help & Commands**\n\n"
            "**How to get episodes:**\n\n"
            "1️⃣ Join @{channel}\n"
            "2️⃣ Find your anime post\n"
            "3️⃣ Click the episode button\n"
            "4️⃣ Bot sends the file here\n"
            "5️⃣ Download before ⏰ auto-delete!\n\n"
            "💡 **Tip:** Forward files to "
            "**Saved Messages** to keep them!\n\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        ).format(channel=Config.FORCE_JOIN_CHANNEL)
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Home", callback_data="go_home")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    elif data == "my_stats":
        user = await db.get_user(user_id)
        files_count = user.get("files_received", 0) if user else 0
        
        text = (
            "📊 **Your Statistics**\n\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"📁 **Files Received:** `{files_count}`\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Home", callback_data="go_home")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    elif data == "about_bot":
        text = (
            "🤖 **About Anime Space Bot**\n\n"
            "A high-performance anime episode delivery bot.\n\n"
            "**Features:**\n"
            "✅ Instant file delivery\n"
            "✅ Auto-delete system\n"
            "✅ Batch downloads\n"
            "✅ Force-join protection\n"
            "✅ Admin controls\n\n"
            f"📢 @{Config.FORCE_JOIN_CHANNEL}\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back to Home", callback_data="go_home")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    elif data == "go_home":
        user_name = callback.from_user.first_name
        total_episodes = await db.get_total_episodes_count()
        total_users = await db.get_all_users_count()
        
        text = (
            f"🎌 **Welcome to Anime Space, {user_name}!**\n\n"
            f"I'm your anime episode delivery bot.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Stats:**\n"
            f"👥 Users: `{total_users}` | 📁 Episodes: `{total_episodes}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔹 Use episode links from our channel\n"
            f"🔹 Files auto-delete after {Config.AUTO_DELETE_SECONDS // 60} min\n\n"
            f"📢 @{Config.FORCE_JOIN_CHANNEL}"
        )
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "📢 Channel", url=f"https://t.me/{Config.FORCE_JOIN_CHANNEL}"
                ),
                InlineKeyboardButton("🔔 Updates", url=f"https://t.me/{Config.FORCE_JOIN_CHANNEL}")
            ],
            [
                InlineKeyboardButton("ℹ️ Help", callback_data="help_menu"),
                InlineKeyboardButton("📊 My Stats", callback_data="my_stats")
            ],
            [
                InlineKeyboardButton("👨‍💻 About", callback_data="about_bot")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
    
    else:
        await callback.answer("❌ Unknown action!", show_alert=True)


def register_callback_handlers(app: Client):
    """Register callback query handlers."""
    app.on_callback_query()(callback_handler)