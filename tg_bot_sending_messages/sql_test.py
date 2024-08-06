import aiomysql
import asyncio
from loguru import logger

DB_CONFIG = {
    "user": "python_mysql",
    "password": "python_mysql",
    "host": "45.137.155.18",
    "port": 3306,
    "db": "corn",
}


async def test_direct_connection():
    try:
        conn = await aiomysql.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset="utf8mb4",
        )
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            print(await cur.fetchone())
        logger.info("Успешное прямое подключение к базе данных")
    except Exception as e:
        logger.error(f"Ошибка при прямом подключении к базе данных: {e}")


# Используйте эту функцию для тестирования
asyncio.run(test_direct_connection())
