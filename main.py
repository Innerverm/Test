import asyncio
import logging
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import Message
from typing import Optional

# Local imports
from handlers.upload import handle_file_upload
from handlers.compression import handle_zip_upload
from handlers.errors import handle_errors
from utils.cleanup import cleanup_temp_files

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize the bot
app = Client(
    "gofile_bot",
    bot_token=os.getenv("BOT_TOKEN"),
    api_id=int(os.getenv("API_ID")),
    api_hash=os.getenv("API_HASH")
)

@app.on_message(filters.command(["start", "help"]))
async def start_command(client: Client, message: Message):
    """Handle the /start and /help commands"""
    help_text = (
        "📤 GoFile Uploader Bot\n\n"
        "Commands:\n"
        "/upload - Upload a replied file\n"
        "/upload_custom <filename> - Upload with custom filename\n"
        "/zip - Compress multiple files (reply to them)\n\n"
        "The bot automatically handles:\n"
        "- Large files (chunked uploads)\n"
        "- Progress tracking\n"
        "- Temporary file cleanup"
    )
    await message.reply_text(help_text)

@app.on_message(filters.command("upload") & filters.reply)
@handle_errors
async def upload_command(client: Client, message: Message):
    """Handle file upload command"""
    await handle_file_upload(client, message)

@app.on_message(filters.command("upload_custom") & filters.reply)
@handle_errors
async def upload_custom_command(client: Client, message: Message):
    """Handle custom filename upload"""
    custom_name = " ".join(message.command[1:])
    if not custom_name:
        await message.reply_text("Please provide a custom filename after the command.")
        return
    
    await handle_file_upload(client, message, custom_name=custom_name)

@app.on_message(filters.command("zip") & filters.reply)
@handle_errors
async def zip_command(client: Client, message: Message):
    """Handle ZIP compression command"""
    await handle_zip_upload(client, message)

@app.on_message(filters.document | filters.video | filters.audio | filters.photo)
@handle_errors
async def auto_upload(client: Client, message: Message):
    """Auto-upload any media file sent to the bot"""
    await handle_file_upload(client, message)

async def main():
    """Main function to start the bot"""
    await cleanup_temp_files()  # Cleanup any leftover temp files
    await app.start()
    logger.info("Bot started successfully")
    await asyncio.Event().wait()  # Run indefinitely

if __name__ == "__main__":
    asyncio.run(main())
