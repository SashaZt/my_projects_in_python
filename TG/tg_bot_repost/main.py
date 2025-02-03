import asyncio

from bot import start_bot
from config import logger
from database import init_db


async def main():
    """Инициализация БД и запуск бота"""
    await init_db()
    await start_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
