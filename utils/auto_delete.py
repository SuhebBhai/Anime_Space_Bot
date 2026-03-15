# utils/auto_delete.py
import asyncio
from pyrogram import Client
from pyrogram.types import Message
from config import Config


async def schedule_auto_delete(client: Client, message: Message, 
                                seconds: int = None, notification_msg: Message = None):
    """
    Schedule a message for automatic deletion after a specified time.
    Also sends a countdown warning to the user.
    """
    if seconds is None:
        seconds = Config.AUTO_DELETE_SECONDS
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    # Send auto-delete warning
    if notification_msg is None:
        time_str = f"{minutes}m {remaining_seconds}s" if remaining_seconds else f"{minutes} minutes"
        warning = await client.send_message(
            chat_id=message.chat.id,
            text=(
                f"⏰ **Auto-Delete Notice**\n\n"
                f"This file will be automatically deleted in **{time_str}**.\n"
                f"Please download or save it before the timer expires!\n\n"
                f"💡 **Tip:** Forward this file to your Saved Messages to keep it permanently."
            ),
            reply_to_message_id=message.id
        )
    else:
        warning = notification_msg
    
    # Wait for the specified duration
    await asyncio.sleep(seconds)
    
    # Delete the file message
    try:
        await message.delete()
    except Exception as e:
        print(f"[AUTO-DELETE] Failed to delete file message: {e}")
    
    # Delete the warning message
    try:
        await warning.delete()
    except Exception as e:
        print(f"[AUTO-DELETE] Failed to delete warning message: {e}")
    
    # Send confirmation that file was deleted
    try:
        deleted_notice = await client.send_message(
            chat_id=message.chat.id,
            text=(
                "🗑️ **File Auto-Deleted**\n\n"
                "The episode file has been automatically removed.\n"
                "You can request it again anytime using the same link!\n\n"
                f"🤖 @{Config.BOT_USERNAME}"
            )
        )
        # Auto-delete the notice itself after 60 seconds
        await asyncio.sleep(60)
        await deleted_notice.delete()
    except Exception:
        pass