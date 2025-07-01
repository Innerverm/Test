import os
import aiofiles
from typing import Optional
from pyrogram import Client
from pyrogram.types import Message
from tqdm.asyncio import tqdm

from utils.gofile import get_best_server, upload_file
from utils.progress import TelegramProgress
from utils.cleanup import register_temp_file

async def handle_file_upload(
    client: Client,
    message: Message,
    custom_name: Optional[str] = None
) -> None:
    """
    Handle the file upload process from Telegram to GoFile.io
    
    Args:
        client: Pyrogram client instance
        message: The message containing the file to upload
        custom_name: Optional custom filename for the upload
    """
    # Get the file from the replied message
    reply = message.reply_to_message
    file_type = next(
        (media for media in [
            "document", "video", "audio", "photo", "voice", "video_note", "sticker"
        ] if getattr(reply, media, None)),
        None
    )
    
    if not file_type:
        await message.reply_text("❌ Unsupported file type")
        return
    
    media = getattr(reply, file_type)
    if file_type == "photo":
        file_size = media.file_size
        file_name = f"photo_{message.message_id}.jpg"
        mime_type = "image/jpeg"
    else:
        file_size = media.file_size
        file_name = getattr(media, "file_name", None) or f"{file_type}_{message.message_id}"
        mime_type = getattr(media, "mime_type", None) or "application/octet-stream"
    
    # Use custom name if provided
    if custom_name:
        file_name = custom_name
    
    # Check file size limit (GoFile has 20GB limit for free accounts)
    if file_size > 20 * 1024 * 1024 * 1024:
        await message.reply_text("❌ File size exceeds 20GB limit")
        return
    
    # Download progress
    download_progress = TelegramProgress(
        client, message.chat.id, message.message_id,
        f"⬇️ Downloading {file_name}"
    )
    
    # Download the file
    temp_path = f"temp_{message.message_id}_{file_name}"
    await register_temp_file(temp_path)
    
    await client.download_media(
        message=reply,
        file_name=temp_path,
        progress=download_progress.update_progress,
        progress_args=(file_size,)
    )
    
    # Get best server
    server = await get_best_server()
    if not server:
        await message.reply_text("❌ Failed to get GoFile server")
        return
    
    # Upload progress
    upload_progress = TelegramProgress(
        client, message.chat.id, message.message_id,
        f"⬆️ Uploading to GoFile: {file_name}"
    )
    
    # Upload the file
    async with aiofiles.open(temp_path, "rb") as file:
        result = await upload_file(
            file=file,
            filename=file_name,
            server=server,
            progress_callback=upload_progress.update_progress,
            file_size=file_size,
            mime_type=mime_type
        )
    
    if result and "downloadPage" in result:
        await message.reply_text(
            f"✅ Upload complete!\n"
            f"📁 Filename: {file_name}\n"
            f"🔗 Download URL: {result['downloadPage']}\n"
            f"📦 Direct Link: {result['directLink']}"
        )
    else:
        await message.reply_text("❌ Upload failed")
    
    # Clean up
    try:
        os.remove(temp_path)
    except Exception as e:
        logger.error(f"Error cleaning up temp file: {e}")
