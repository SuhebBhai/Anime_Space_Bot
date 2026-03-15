# handlers/admin.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database import db
from utils.helpers import (
    encode_message_id, encode_batch_ids, encode_data,
    generate_episode_code, format_file_size
)


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in Config.ADMIN_IDS


# ─── Admin Filter ───
admin_filter = filters.create(lambda _, __, msg: is_admin(msg.from_user.id))


async def admin_panel(client: Client, message: Message):
    """Show admin control panel."""
    if not is_admin(message.from_user.id):
        return
    
    total_users = await db.get_all_users_count()
    total_episodes = await db.get_total_episodes_count()
    
    text = (
        "🔧 **Admin Control Panel**\n\n"
        f"👥 Total Users: `{total_users}`\n"
        f"📁 Total Episodes: `{total_episodes}`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "**Available Commands:**\n\n"
        "📤 `/genlink` - Reply to a file to generate share link\n"
        "📦 `/batch` - Generate batch link for multiple files\n"
        "📝 `/addep` - Add episode mapping manually\n"
        "🗑️ `/delep` - Delete episode mapping\n"
        "📊 `/stats` - View detailed statistics\n"
        "📣 `/broadcast` - Broadcast message to all users\n"
        "🚫 `/ban` - Ban a user\n"
        "✅ `/unban` - Unban a user\n"
        "📋 `/listep` - List all episode mappings\n"
        "⚙️ `/settings` - Bot settings\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await message.reply_text(text)


async def generate_link(client: Client, message: Message):
    """
    Generate a shareable deep link for a file.
    Admin forwards a file from storage channel, or replies to a file,
    and the bot generates a link users can click to get that file.
    """
    if not is_admin(message.from_user.id):
        return
    
    # Check if replying to a message
    reply = message.reply_to_message
    
    if reply is None:
        await message.reply_text(
            "❌ **Reply to a file message to generate a link!**\n\n"
            "**Method 1:** Forward a file from storage channel to bot, "
            "then reply to it with `/genlink`\n\n"
            "**Method 2:** Send a file directly to the storage channel, "
            "note the message ID, and use:\n"
            "`/genlink <message_id>`"
        )
        return
    
    # If the reply contains a forwarded message from storage channel
    if reply.forward_from_chat and reply.forward_from_chat.id == Config.STORAGE_CHANNEL_ID:
        message_id = reply.forward_from_message_id
    elif reply.document or reply.video or reply.audio or reply.animation:
        # Admin needs to first forward to storage channel
        try:
            forwarded = await reply.forward(Config.STORAGE_CHANNEL_ID)
            message_id = forwarded.id
        except Exception as e:
            await message.reply_text(f"❌ Failed to forward to storage: {e}")
            return
    else:
        # Try extracting message_id from command argument
        parts = message.text.split()
        if len(parts) > 1:
            try:
                message_id = int(parts[1])
            except ValueError:
                await message.reply_text("❌ Invalid message ID!")
                return
        else:
            await message.reply_text("❌ Reply to a file or provide a message ID!")
            return
    
    # Generate the encoded link
    encoded = encode_message_id(message_id)
    bot_link = f"https://t.me/{Config.BOT_USERNAME}?start={encoded}"
    
    # Get file info
    file_name = "Unknown"
    file_size = "Unknown"
    if reply.document:
        file_name = reply.document.file_name or "Document"
        file_size = format_file_size(reply.document.file_size)
    elif reply.video:
        file_name = reply.video.file_name or "Video"
        file_size = format_file_size(reply.video.file_size)
    
    result_text = (
        "✅ **Link Generated Successfully!**\n\n"
        f"📁 **File:** `{file_name}`\n"
        f"📦 **Size:** `{file_size}`\n"
        f"🆔 **Storage Msg ID:** `{message_id}`\n\n"
        f"🔗 **Share Link:**\n`{bot_link}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Users who click this link will receive the file "
        f"after joining the required channel."
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Test Link", url=bot_link)
        ]
    ])
    
    await message.reply_text(result_text, reply_markup=keyboard)


async def generate_batch_link(client: Client, message: Message):
    """
    Generate a batch link for multiple consecutive files.
    Usage: /batch <start_msg_id> <end_msg_id>
    """
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    
    if len(parts) != 3:
        await message.reply_text(
            "❌ **Invalid format!**\n\n"
            "**Usage:** `/batch <start_id> <end_id>`\n"
            "**Example:** `/batch 10 25`\n\n"
            "This will create a link that sends all files "
            "from message ID 10 to 25 in the storage channel."
        )
        return
    
    try:
        start_id = int(parts[1])
        end_id = int(parts[2])
    except ValueError:
        await message.reply_text("❌ Message IDs must be numbers!")
        return
    
    if start_id > end_id:
        start_id, end_id = end_id, start_id
    
    total = end_id - start_id + 1
    
    if total > 20:
        await message.reply_text(
            f"⚠️ **Batch too large!** Maximum 20 files per batch.\n"
            f"Your range: {total} files."
        )
        return
    
    encoded = encode_batch_ids(start_id, end_id)
    bot_link = f"https://t.me/{Config.BOT_USERNAME}?start={encoded}"
    
    result_text = (
        "✅ **Batch Link Generated!**\n\n"
        f"📦 **Range:** Message ID `{start_id}` to `{end_id}`\n"
        f"📁 **Total Files:** `{total}`\n\n"
        f"🔗 **Batch Link:**\n`{bot_link}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Test Batch Link", url=bot_link)]
    ])
    
    await message.reply_text(result_text, reply_markup=keyboard)


async def add_episode_mapping(client: Client, message: Message):
    """
    Add an episode mapping to the database.
    Usage: /addep <code> <message_id> [anime_name] [episode_number]
    """
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split(maxsplit=4)
    
    if len(parts) < 3:
        await message.reply_text(
            "❌ **Invalid format!**\n\n"
            "**Usage:** `/addep <code> <msg_id> [anime] [ep_num]`\n"
            "**Example:** `/addep naruto_01 156 Naruto 1`\n\n"
            "This maps the code 'naruto_01' to message ID 156 "
            "in the storage channel."
        )
        return
    
    code = parts[1]
    try:
        msg_id = int(parts[2])
    except ValueError:
        await message.reply_text("❌ Message ID must be a number!")
        return
    
    anime_name = parts[3] if len(parts) > 3 else None
    ep_num = None
    if len(parts) > 4:
        try:
            ep_num = int(parts[4])
        except ValueError:
            ep_num = None
    
    await db.add_episode(code, msg_id, anime_name, ep_num)
    
    # Generate link for this episode
    encoded = encode_data(f"ep_{code}")
    bot_link = f"https://t.me/{Config.BOT_USERNAME}?start={encoded}"
    
    await message.reply_text(
        f"✅ **Episode Mapping Added!**\n\n"
        f"📝 Code: `{code}`\n"
        f"🆔 Message ID: `{msg_id}`\n"
        f"🎬 Anime: `{anime_name or 'N/A'}`\n"
        f"📺 Episode: `{ep_num or 'N/A'}`\n\n"
        f"🔗 Link: `{bot_link}`",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Test", url=bot_link)]
        ])
    )


async def delete_episode_mapping(client: Client, message: Message):
    """Delete an episode mapping."""
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply_text(
            "❌ **Usage:** `/delep <episode_code>`\n"
            "**Example:** `/delep naruto_01`"
        )
        return
    
    code = parts[1]
    deleted = await db.delete_episode(code)
    
    if deleted:
        await message.reply_text(f"✅ Episode `{code}` deleted successfully!")
    else:
        await message.reply_text(f"❌ Episode `{code}` not found!")


async def list_episodes(client: Client, message: Message):
    """List all episode mappings."""
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split(maxsplit=1)
    anime_filter = parts[1] if len(parts) > 1 else None
    
    episodes = await db.get_all_episodes(anime_filter)
    
    if not episodes:
        await message.reply_text("📭 No episodes found in database.")
        return
    
    text = "📋 **Episode Mappings:**\n\n"
    
    for i, ep in enumerate(episodes, 1):
        text += (
            f"**{i}.** `{ep['episode_code']}`\n"
            f"   📁 Msg ID: `{ep['message_id']}`"
        )
        if ep.get('anime_name'):
            text += f" | 🎬 {ep['anime_name']}"
        if ep.get('episode_number'):
            text += f" Ep {ep['episode_number']}"
        text += f" | 👁️ {ep.get('access_count', 0)} views\n\n"
        
        # Telegram message limit
        if len(text) > 3800:
            text += "... (truncated)"
            break
    
    await message.reply_text(text)


async def view_stats(client: Client, message: Message):
    """View detailed bot statistics."""
    if not is_admin(message.from_user.id):
        return
    
    total_users = await db.get_all_users_count()
    total_episodes = await db.get_total_episodes_count()
    today_accesses = await db.get_daily_stats()
    
    text = (
        "📊 **Bot Statistics**\n\n"
        f"👥 **Total Users:** `{total_users}`\n"
        f"📁 **Total Episodes:** `{total_episodes}`\n"
        f"📈 **Today's Accesses:** `{today_accesses}`\n\n"
        f"⏰ Auto-Delete Timer: `{Config.AUTO_DELETE_SECONDS // 60} minutes`\n"
        f"📢 Force Join: `@{Config.FORCE_JOIN_CHANNEL}`\n"
        f"🗄️ Storage Channel: `{Config.STORAGE_CHANNEL_ID}`\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await message.reply_text(text)


async def broadcast_message(client: Client, message: Message):
    """Broadcast a message to all users."""
    if not is_admin(message.from_user.id):
        return
    
    reply = message.reply_to_message
    if not reply:
        await message.reply_text(
            "❌ **Reply to a message to broadcast it!**\n\n"
            "The replied message will be sent to all bot users."
        )
        return
    
    user_ids = await db.get_all_user_ids()
    total = len(user_ids)
    
    progress_msg = await message.reply_text(
        f"📣 **Broadcasting...**\n\n"
        f"📤 Sending to {total} users..."
    )
    
    sent = 0
    failed = 0
    
    for user_id in user_ids:
        try:
            await reply.copy(user_id)
            sent += 1
        except Exception:
            failed += 1
        
        # Rate limiting
        if (sent + failed) % 25 == 0:
            await asyncio.sleep(1)
        
        # Update progress every 100 users
        if (sent + failed) % 100 == 0:
            try:
                await progress_msg.edit_text(
                    f"📣 **Broadcasting...**\n\n"
                    f"✅ Sent: {sent}\n"
                    f"❌ Failed: {failed}\n"
                    f"📊 Progress: {sent + failed}/{total}"
                )
            except Exception:
                pass
    
    await progress_msg.edit_text(
        f"📣 **Broadcast Complete!**\n\n"
        f"✅ Sent: `{sent}`\n"
        f"❌ Failed: `{failed}`\n"
        f"📊 Total: `{total}`"
    )


async def ban_user_cmd(client: Client, message: Message):
    """Ban a user from using the bot."""
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply_text("❌ **Usage:** `/ban <user_id>`")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.reply_text("❌ Invalid user ID!")
        return
    
    await db.ban_user(target_id)
    await message.reply_text(f"🚫 User `{target_id}` has been **banned**.")


async def unban_user_cmd(client: Client, message: Message):
    """Unban a user."""
    if not is_admin(message.from_user.id):
        return
    
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply_text("❌ **Usage:** `/unban <user_id>`")
        return
    
    try:
        target_id = int(parts[1])
    except ValueError:
        await message.reply_text("❌ Invalid user ID!")
        return
    
    await db.unban_user(target_id)
    await message.reply_text(f"✅ User `{target_id}` has been **unbanned**.")


async def channel_file_handler(client: Client, message: Message):
    """
    Automatically generate links when files are posted in storage channel.
    Bot listens for new files in the storage channel and auto-generates links.
    """
    if message.chat.id != Config.STORAGE_CHANNEL_ID:
        return
    
    message_id = message.id
    encoded = encode_message_id(message_id)
    bot_link = f"https://t.me/{Config.BOT_USERNAME}?start={encoded}"
    
    file_name = "Unknown"
    if message.document:
        file_name = message.document.file_name or "Document"
    elif message.video:
        file_name = message.video.file_name or "Video"
    elif message.audio:
        file_name = message.audio.file_name or "Audio"
    
    # Reply in the storage channel with the generated link
    try:
        await message.reply_text(
            f"🔗 **Auto-Generated Link:**\n\n"
            f"📁 File: `{file_name}`\n"
            f"🆔 Msg ID: `{message_id}`\n"
            f"🔗 Link: `{bot_link}`",
            quote=True
        )
    except Exception as e:
        print(f"[AUTO-LINK] Failed: {e}")


def register_admin_handlers(app: Client):
    """Register all admin command handlers."""
    app.on_message(filters.command("admin") & filters.private & admin_filter)(admin_panel)
    app.on_message(filters.command("genlink") & filters.private & admin_filter)(generate_link)
    app.on_message(filters.command("batch") & filters.private & admin_filter)(generate_batch_link)
    app.on_message(filters.command("addep") & filters.private & admin_filter)(add_episode_mapping)
    app.on_message(filters.command("delep") & filters.private & admin_filter)(delete_episode_mapping)
    app.on_message(filters.command("listep") & filters.private & admin_filter)(list_episodes)
    app.on_message(filters.command("stats") & filters.private & admin_filter)(view_stats)
    app.on_message(filters.command("broadcast") & filters.private & admin_filter)(broadcast_message)
    app.on_message(filters.command("ban") & filters.private & admin_filter)(ban_user_cmd)
    app.on_message(filters.command("unban") & filters.private & admin_filter)(unban_user_cmd)
    
    # Auto-link generation for files posted in storage channel
    app.on_message(
        filters.chat(Config.STORAGE_CHANNEL_ID) & 
        (filters.document | filters.video | filters.audio | filters.animation)
    )(channel_file_handler)