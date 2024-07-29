import aiomysql
import asyncio
import logging
from configuration.config import DB_CONFIG

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_connection():
    return await aiomysql.connect(**DB_CONFIG)


async def drop_tables():
    # connection = await create_connection()
    async with connection.cursor() as cursor:
        try:
            # Сначала удаляем таблицы, ссылающиеся на другие таблицы
            logger.info("Dropping table: user_rates")
            await cursor.execute("DROP TABLE IF EXISTS user_rates")
            await connection.commit()

            # Затем удаляем основные таблицы
            logger.info("Dropping table: user_raw_materials")
            await cursor.execute("DROP TABLE IF EXISTS user_raw_materials")
            await connection.commit()

            logger.info("Dropping table: user_regions")
            await cursor.execute("DROP TABLE IF EXISTS user_regions")
            await connection.commit()

            logger.info("Dropping table: users_tg_bot")
            await cursor.execute("DROP TABLE IF EXISTS users_tg_bot")
            await connection.commit()

            logger.info("Tables dropped successfully")

        except aiomysql.Error as err:
            logger.error(f"Error: {err}")
        finally:
            connection.close()


if __name__ == "__main__":
    asyncio.run(drop_tables())
