import aiohttp
import logging
from typing import Optional, Dict, BinaryIO, Callable, Awaitable
from urllib.parse import quote

logger = logging.getLogger(__name__)

async def get_best_server() -> Optional[str]:
    """
    Get the best available GoFile server
    
    Returns:
        str: Server name (e.g., "srv-store8") or None if failed
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.gofile.io/getServer") as response:
                data = await response.json()
                if data["status"] == "ok":
                    return data["data"]["server"]
                logger.error(f"Failed to get server: {data}")
                return None
    except Exception as e:
        logger.error(f"Error getting best server: {e}")
        return None

async def upload_file(
    file: BinaryIO,
    filename: str,
    server: str,
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None,
    file_size: Optional[int] = None,
    mime_type: str = "application/octet-stream"
) -> Optional[Dict]:
    """
    Upload a file to GoFile.io
    
    Args:
        file: File-like object to upload
        filename: Name of the file
        server: GoFile server to upload to
        progress_callback: Callback for upload progress
        file_size: Total size of the file (for progress tracking)
        mime_type: MIME type of the file
    
    Returns:
        dict: Upload response data or None if failed
    """
    url = f"https://{server}.gofile.io/uploadFile"
    
    try:
        data = aiohttp.FormData()
        data.add_field(
            "file",
            file,
            filename=quote(filename),
            content_type=mime_type
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                data=data,
                timeout=aiohttp.ClientTimeout(total=3600) as response:
                
                if response.status != 200:
                    logger.error(f"Upload failed with status {response.status}")
                    return None
                
                return await response.json()
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return None
