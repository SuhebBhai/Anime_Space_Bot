# utils/helpers.py
import base64
import struct
import string
import random
from typing import List


def generate_episode_code(length: int = 8) -> str:
    """Generate a random episode code for deep linking."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def encode_data(data: str) -> str:
    """Encode data for use in Telegram deep links (base64 URL-safe)."""
    encoded = base64.urlsafe_b64encode(data.encode()).decode()
    # Remove padding '=' as Telegram doesn't handle them well
    return encoded.rstrip('=')


def decode_data(encoded: str) -> str:
    """Decode data from Telegram deep links."""
    # Add back padding
    padding = 4 - len(encoded) % 4
    if padding != 4:
        encoded += '=' * padding
    return base64.urlsafe_b64decode(encoded.encode()).decode()


def encode_message_id(message_id: int) -> str:
    """Encode a single message ID for deep linking."""
    return encode_data(f"file_{message_id}")


def decode_message_id(code: str) -> int:
    """Decode a message ID from deep link."""
    try:
        decoded = decode_data(code)
        if decoded.startswith("file_"):
            return int(decoded.replace("file_", ""))
    except Exception:
        pass
    return None


def encode_batch_ids(start_id: int, end_id: int) -> str:
    """Encode a batch range for deep linking."""
    return encode_data(f"batch_{start_id}_{end_id}")


def decode_batch_ids(code: str) -> tuple:
    """Decode batch range from deep link."""
    try:
        decoded = decode_data(code)
        if decoded.startswith("batch_"):
            parts = decoded.split("_")
            return int(parts[1]), int(parts[2])
    except Exception:
        pass
    return None, None


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human-readable file size."""
    if size_bytes is None:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: int) -> str:
    """Convert seconds to human-readable duration."""
    if seconds is None:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"