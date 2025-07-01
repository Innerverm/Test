import os
import zipfile
import aiofiles
from typing import List
from pyrogram import Client
from pyrogram.types import Message
from io import BytesIO
from tqdm.asyncio import tqdm

from utils.gofile import get_best_server, upload_file
from utils.progress import TelegramProgress
from utils.cleanup import register_temp_file

async def handle_zip_upload(client: Client, message: Message) -> None:
    """
    Handle ZIP compression and upload of multiple files
    
    Args:
        client: Pyrogram client instance
        message: The message containing files to compress and upload
    """
    reply = message.reply_to_message
    if not reply:
        await message.reply_text("Please reply to messages containing files")
        return
    
    # Collect all files from the replied message(s)
    files_to_zip = []
    current_message = reply
    
    while current_message:
        file_type = next(
            (media for media in [
                "document", "video", "audio", "photo", "voice", "video_note"
            ] if getattr(current_message, media, None)),
            None
        )
        
        if file_type:
            media = getattr(current_message, file_type)
            if file_type == "photo":
                file_name = f"photo_{current_message.message_id}.jpg"
            else:
                file_name = getattr(media, "file_name", None) or f"{file_type}_{current_message.message_id}"
            
            files_to_zip.append((current_message, file_type, file_name))
        
        current_message = current_message.reply_to_message
    
    if not files_to_zip:
        await message.reply_text("No supported files found in the replied messages")
        return
    
    # Create ZIP file in memory
    zip_filename = f"archive_{message.message_id}.zip"
    zip_path = f"temp_{zip_filename}"
    await register_temp_file(zip_path)
    
    total_size = 0
    zip_progress = TelegramProgress(
        client, message.chat.id, message.message_id,
        "🗜 Creating ZIP archive"
    )
    
    # Create the ZIP file
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for msg, file_type, file_name in files_to_zip:
            media = getattr(msg, file_type)
            
            # Download each file and add to ZIP
            temp_path = f"temp_{msg.message_id}_{file_name}"
            await register_temp_file(temp_path)
            
            await client.download_media(
                message=msg,
                file_name=temp_path
            )
            
            # Add to ZIP and remove temp file
            zipf.write(temp_path, file_name)
            os.remove(temp_path)
            total_size += os.path.getsize(temp_path)
    
    # Get ZIP file size
    zip_size = os.path.getsize(zip_path)
    
    # Get best server
    server = await get_best_server()
    if not server:
        await message.reply_text("❌ Failed to get GoFile server")
        return
    
    # Upload progress
    upload_progress = TelegramProgress(
        client, message.chat.id, message.message_id,
        f"⬆️ Uploading ZIP archive to GoFile"
    )
    
    # Upload the ZIP file
    async with aiofiles.open(zip_path, "rb") as file:
        result = await upload_file(
            file=file,
            filename=zip_filename,
            server=server,
            progress_callback=upload_progress.update_progress,
            file_size=zip_size,
            mime_type="application/zip"
        )
    
    if result and "downloadPage" in result:
        await message.reply_text(
            f"✅ ZIP upload complete!\n"
            f"📦 Filename: {zip_filename}\n"
            f"🔗 Download URL: {result['downloadPage']}\n"
            f"📦 Direct Link: {result['directLink']}\n"
            f"📝 Contains {len(files_to_zip)} files"
        )
    else:
        await message.reply_text("❌ ZIP upload failed")
    
    # Clean up
    try:
        os.remove(zip_path)
    except Exception as e:
        logger.error(f"Error cleaning up ZIP file: {e}")
