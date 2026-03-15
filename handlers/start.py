# handlers/start.py
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    CallbackQuery
)
from config import Config
from database import db
from utils.force_join import check_force_join, force_join_message
from utils.auto_delete import schedule_auto_delete
from utils.helpers import (
    decode_data, decode_message_id, decode_batch_ids,
    format_file_size
)


async def start_command(client: Client, message: Message):
    """Handle /start command with optional deep link parameters."""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Register/update user in database
    await db.add_user(user_id, username, first_name)
    
    # Check if user is banned
    if await db.is_banned(user_id):
        await message.reply_text(
            "🚫 **You have been banned from using this bot.**\n"
            "Contact the admin if you think this is a mistake."
        )
        return
    
    # Extract deep link parameter
    command_parts = message.text.split(" ", 1)
    deep_link_param = command_parts[1] if len(command_parts) > 1 else None
    
    # ─── Force Join Verification ───
    is_member = await check_force_join(client, user_id)
    
    if not is_member:
        text, keyboard = force_join_message(deep_link_param)
        await message.reply_text(text, reply_markup=keyboard)
        return
    
    # ─── No Deep Link - Show Welcome Message ───
    if deep_link_param is None or deep_link_param == "verify":
        await send_welcome_message(client, message)
        return
    
    # ─── Handle File Deep Link ───
    try:
        decoded = decode_data(deep_link_param)
    except Exception:
        await message.reply_text("❌ **Invalid link!** Please use a valid episode link.")
        return
    
    # Single file request
    if decoded.startswith("file_"):
        message_id = decode_message_id(deep_link_param)
        if message_id:
            await send_single_file(client, message, message_id)
        else:
            await message.reply_text("❌ **Invalid file link!**")
        return
    
    # Batch file request
    if decoded.startswith("batch_"):
        start_id, end_id = decode_batch_ids(deep_link_param)
        if start_id and end_id:
            await send_batch_files(client, message, start_id, end_id)
        else:
            await message.reply_text("❌ **Invalid batch link!**")
        return
    
    # Episode code request (from database mapping)
    if decoded.startswith("ep_"):
        episode_code = decoded.replace("ep_", "")
        await send_episode_by_code(client, message, episode_code)
        return
    
    await message.reply_text("❌ **Unknown link format!**")


async def send_welcome_message(client: Client, message: Message):
    """Send the main welcome/start message."""
    user_name = message.from_user.first_name
    total_episodes = await db.get_total_episodes_count()
    total_users = await db.get_all_users_count()
    
    welcome_text = (
        f"🎌 **Welcome to Anime Space, {user_name}!**\n\n"
        f"I'm your anime episode delivery bot. I can send you "
        f"episodes directly in this chat!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Bot Statistics:**\n"
        f"👥 Total Users: `{total_users}`\n"
        f"📁 Total Episodes: `{total_episodes}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔹 Use episode links from our channel to get files\n"
        f"🔹 Files auto-delete after {Config.AUTO_DELETE_SECONDS // 60} minutes\n"
        f"🔹 Forward files to Saved Messages to keep them\n\n"
        f"📢 **Main Channel:** @{Config.FORCE_JOIN_CHANNEL}\n"
        f"🤖 **Bot:** @{Config.BOT_USERNAME}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 Main Channel",
                url=f"https://t.me/{Config.FORCE_JOIN_CHANNEL}"
            ),
            InlineKeyboardButton(
                "🔔 Updates",
                url=f"https://t.me/{Config.FORCE_JOIN_CHANNEL}"
            )
        ],
        [
            InlineKeyboardButton(
                "ℹ️ Help & Commands",
                callback_data="help_menu"
            ),
            InlineKeyboardButton(
                "📊 My Stats",
                callback_data="my_stats"
            )
        ],
        [
            InlineKeyboardButton(
                "👨‍💻 About Bot",
                callback_data="about_bot"
            )
        ]
    ])
    
    # Try to send with a photo/animation
    try:
        await message.reply_text(
            text=welcome_text,
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    except Exception as e:
        print(f"[ERROR] Welcome message failed: {e}")
        await message.reply_text(welcome_text)


async def send_single_file(client: Client, message: Message, message_id: int):
    """Retrieve and send a single file from the storage channel."""
    user_id = message.from_user.id
    
    # Send "processing" message
    processing_msg = await message.reply_text(
        "⏳ **Fetching your episode...**\n"
        "Please wait a moment."
    )
    
    try:
        # Copy the file from storage channel to user chat
        sent_message = await client.copy_message(
            chat_id=message.chat.id,
            from_chat_id=Config.STORAGE_CHANNEL_ID,
            message_id=message_id,
            caption=(
                f"🎬 **Here's your episode!**\n\n"
                f"⏰ This file will auto-delete in "
                f"**{Config.AUTO_DELETE_SECONDS // 60} minutes**.\n"
                f"💡 Forward to **Saved Messages** to keep it!\n\n"
                f"🤖 Powered by @{Config.BOT_USERNAME}"
            ),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📢 Main Channel",
                        url=f"https://t.me/{Config.FORCE_JOIN_CHANNEL}"
                    )
                ]
            ])
        )
        
        # Delete processing message
        await processing_msg.delete()
        
        # Log access
        await db.increment_files_received(user_id)
        await db.log_access(user_id, f"msg_{message_id}")
        
        # Schedule auto-deletion
        asyncio.create_task(
            schedule_auto_delete(client, sent_message, Config.AUTO_DELETE_SECONDS)
        )
    
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ **Failed to retrieve the file!**\n\n"
            f"The file may have been deleted from storage.\n"
            f"Please contact admin or try again later.\n\n"
            f"Error: `{str(e)[:100]}`"
        )
        print(f"[ERROR] File retrieval failed for msg_id {message_id}: {e}")


async def send_batch_files(client: Client, message: Message, 
                            start_id: int, end_id: int):
    """Send multiple files from a batch range."""
    user_id = message.from_user.id
    
    # Limit batch size to prevent abuse
    max_batch = 20
    total = end_id - start_id + 1
    
    if total > max_batch:
        await message.reply_text(
            f"⚠️ **Batch too large!** Maximum {max_batch} files at once.\n"
            f"Requested: {total} files."
        )
        return
    
    if total <= 0:
        await message.reply_text("❌ **Invalid batch range!**")
        return
    
    processing_msg = await message.reply_text(
        f"⏳ **Fetching {total} episodes...**\n"
        f"This may take a moment. Please wait."
    )
    
    sent_count = 0
    failed_count = 0
    sent_messages = []
    
    for msg_id in range(start_id, end_id + 1):
        try:
            sent = await client.copy_message(
                chat_id=message.chat.id,
                from_chat_id=Config.STORAGE_CHANNEL_ID,
                message_id=msg_id
            )
            sent_messages.append(sent)
            sent_count += 1
            
            # Small delay to avoid flood
            await asyncio.sleep(1)
        
        except Exception as e:
            failed_count += 1
            print(f"[BATCH] Failed to send msg_id {msg_id}: {e}")
            continue
    
    # Update processing message
    status_text = (
        f"✅ **Batch Complete!**\n\n"
        f"📁 Sent: {sent_count}/{total}\n"
    )
    if failed_count > 0:
        status_text += f"❌ Failed: {failed_count}\n"
    
    status_text += (
        f"\n⏰ All files will auto-delete in "
        f"**{Config.AUTO_DELETE_SECONDS // 60} minutes**.\n"
        f"💡 Forward to **Saved Messages** to keep them!"
    )
    
    await processing_msg.edit_text(status_text)
    
    # Log access
    await db.increment_files_received(user_id)
    await db.log_access(user_id, f"batch_{start_id}_{end_id}")
    
    # Schedule auto-deletion for all sent messages
    for sent_msg in sent_messages:
        asyncio.create_task(
            schedule_auto_delete(client, sent_msg, Config.AUTO_DELETE_SECONDS)
        )


async def send_episode_by_code(client: Client, message: Message, episode_code: str):
    """Send episode using database-mapped episode code."""
    episode = await db.get_episode(episode_code)
    
    if not episode:
        await message.reply_text(
            "❌ **Episode not found!**\n"
            "This episode may have been removed or the link is invalid."
        )
        return
    
    message_id = episode["message_id"]
    await db.increment_access_count(episode_code)
    await send_single_file(client, message, message_id)


def register_start_handlers(app: Client):
    """Register start-related handlers."""
    app.on_message(filters.command("start") & filters.private)(start_command)