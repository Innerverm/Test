from functools import wraps
from typing import Callable, Awaitable, Any
from pyrogram import Client
from pyrogram.types import Message
import logging

logger = logging.getLogger(__name__)

def handle_errors(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """
    Decorator to handle errors in Telegram bot handlers
    
    Args:
        func: The async function to wrap
    
    Returns:
        The wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(client: Client, message: Message, *args, **kwargs):
        try:
            return await func(client, message, *args, **kwargs)
        except TimeoutError:
            await message.reply_text("⌛ Operation timed out. Please try again.")
            logger.error("Timeout in handler", exc_info=True)
        except ConnectionError:
            await message.reply_text("🔌 Connection error. Please check your internet connection.")
            logger.error("Connection error in handler", exc_info=True)
        except Exception as e:
            await message.reply_text(f"❌ An error occurred: {str(e)}")
            logger.error("Error in handler", exc_info=True)
    
    return wrapper
