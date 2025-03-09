# main.py
import asyncio
from src.db import async_session
from src.services import import_products_from_json
from loguru import logger
from pathlib import Path
import sys
current_directory = Path.cwd()
log_directory = current_directory / "log"
json_directory = current_directory / "src" / "json"
log_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"


logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

async def main():
    json_file_path = current_directory / "product.json"
    async with async_session() as db:
        await import_products_from_json(db, json_file_path)

if __name__ == "__main__":
    asyncio.run(main())