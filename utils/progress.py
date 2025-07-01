from typing import Optional, Callable, Awaitable
from pyrogram import Client
from tqdm import tqdm

class TelegramProgress:
    """
    Progress tracker that updates Telegram messages with progress
    
    Args:
        client: Pyrogram client
        chat_id: Chat ID to send progress to
        reply_to: Message ID to reply to
        initial_text: Initial progress text
    """
    def __init__(
        self,
        client: Client,
        chat_id: int,
        reply_to: int,
        initial_text: str
    ):
        self.client = client
        self.chat_id = chat_id
        self.reply_to = reply_to
        self.message = None
        self.initial_text = initial_text
        self.last_update = 0
    
    async def ensure_message(self) -> None:
        """Ensure we have a progress message to update"""
        if not self.message:
            self.message = await self.client.send_message(
                self.chat_id,
                self.initial_text,
                reply_to_message_id=self.reply_to
            )
    
    async def update_progress(
        self,
        current: int,
        total: int
    ) -> None:
        """
        Update the progress message
        
        Args:
            current: Bytes transferred so far
            total: Total bytes to transfer
        """
        await self.ensure_message()
        
        # Only update if significant progress has been made
        if total == 0:
            return
        
        progress = current / total
        percent = progress * 100
        
        # Update message at most once per second
        if percent - self.last_update >= 1 or current == total:
            try:
                await self.message.edit_text(
                    f"{self.initial_text}\n"
                    f"Progress: {percent:.1f}% ({current/1024/1024:.1f}MB / {total/1024/1024:.1f}MB)"
                )
                self.last_update = percent
            except Exception as e:
                # Don't fail the whole operation if progress update fails
                pass
