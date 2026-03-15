# utils/force_join.py
from pyrogram import Client
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config


async def check_force_join(client: Client, user_id: int) -> bool:
    """
    Check if a user has joined the required force-join channel/group.
    Returns True if the user is a member, False otherwise.
    """
    try:
        member = await client.get_chat_member(
            chat_id=Config.FORCE_JOIN_CHANNEL_ID,
            user_id=user_id
        )
        # Check if user is not kicked/banned/left
        if member.status in ["kicked", "banned", "left"]:
            return False
        return True
    
    except UserNotParticipant:
        return False
    
    except ChatAdminRequired:
        # Bot is not admin in the force-join channel - skip check
        print("[WARNING] Bot is not admin in force-join channel. Skipping verification.")
        return True
    
    except PeerIdInvalid:
        print("[ERROR] Invalid force-join channel ID.")
        return True
    
    except Exception as e:
        print(f"[ERROR] Force join check failed: {e}")
        return True


def force_join_message(deep_link_param: str = None) -> tuple:
    """
    Returns the text and inline keyboard for force-join prompt.
    """
    text = (
        "🚫 **Access Denied!**\n\n"
        "You must join our main channel first before using this bot.\n\n"
        "📢 **Step 1:** Join the channel below\n"
        "✅ **Step 2:** Click 'Verify' after joining\n\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    
    # Build the verify button URL
    if deep_link_param:
        verify_url = f"https://t.me/{Config.BOT_USERNAME}?start={deep_link_param}"
    else:
        verify_url = f"https://t.me/{Config.BOT_USERNAME}?start=verify"
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📢 Join Channel",
                url=f"https://t.me/{Config.FORCE_JOIN_CHANNEL}"
            )
        ],
        [
            InlineKeyboardButton(
                "✅ Verify Membership",
                url=verify_url
            )
        ]
    ])
    
    return text, keyboard