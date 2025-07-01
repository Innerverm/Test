import os
import atexit
from typing import List

_temp_files: List[str] = []

async def register_temp_file(path: str) -> None:
    """Register a temporary file for cleanup"""
    _temp_files.append(path)

async def cleanup_temp_files() -> None:
    """Clean up all registered temporary files"""
    for path in _temp_files:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            pass  # Don't fail if cleanup fails
    _temp_files.clear()

# Register cleanup at exit
atexit.register(lambda: asyncio.run(cleanup_temp_files()))
