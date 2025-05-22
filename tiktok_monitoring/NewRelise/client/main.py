# client/main.py
import asyncio
import os
import signal

from client import TikTokMonitor
from logger import logger

from db import Database

# Настройки API ключа для TikTokLive
TIKTOK_API_KEY = (
    "ODBkM2NlYTU2NWIxYTdkYjM1M2NiMzA5MTM1MmVmOTk4M2E4MDM4YzYzZTIzZTBkN2RkODU5"
)

# Настройки подключения к PostgreSQL
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "postgres"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER", "user_bd"),
    "password": os.getenv("POSTGRES_PASSWORD", "Pqm36q1kmcAlsVMIp2glEdfwNnj69X"),
    "database": os.getenv("POSTGRES_DB", "tiktok_monitoring"),
}


async def main():
    # Инициализируем соединение с базой данных
    db = Database(DB_CONFIG)
    db_ready = await db.connect()

    if not db_ready:
        logger.error("Failed to connect to database. Exiting.")
        return

    # Создаем монитор TikTok
    monitor = TikTokMonitor(db, api_key=TIKTOK_API_KEY)

    # Синхронизируем подарки со стримерами
    await monitor.sync_gift_streamers()

    # Настраиваем обработчик сигналов для graceful shutdown
    loop = asyncio.get_running_loop()

    async def shutdown_handler():
        await monitor.stop()
        await db.close()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown_handler()))

    # Запускаем монитор
    try:
        await monitor.start()
    except asyncio.CancelledError:
        logger.info("Monitor cancelled")
    finally:
        await shutdown_handler()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
