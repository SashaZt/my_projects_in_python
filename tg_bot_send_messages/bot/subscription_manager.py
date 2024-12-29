import random

from bot.authorization import authorize
from config.config import API_HASH, API_ID, PAUSE_MAX, PAUSE_MIN, SESSION_NAME
from config.logger_setup import logger
from database import get_connection
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest


async def subscribe_to_groups(group_links: list):
    """
    Подписаться на указанные группы.
    """
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        client = await authorize()  # Авторизация через Telethon
        if not client:
            logger.error("Не удалось авторизоваться через Telethon.")
            return

        conn = get_connection()
        cursor = conn.cursor()

        for link in group_links:
            try:
                # Проверяем статус подписки
                cursor.execute(
                    "SELECT subscription_status FROM groups WHERE group_link = ?",
                    (link,),
                )
                result = cursor.fetchone()
                logger.info(result)

                if result and result[0]:  # Если статус подписки True
                    logger.info(f"Группа {link} уже подписана. Пропускаем.")
                    continue

                # Подписываемся на группу
                await client(JoinChannelRequest(link))
                logger.info(f"Успешно подписались на группу: {link}")
                # Рандомная пауза с диапазоном из конфига
                pause_duration = random.uniform(PAUSE_MIN, PAUSE_MAX)
                logger.info(
                    f"Ожидание {pause_duration:.2f} секунд перед следующей отправкой."
                )

                # Обновляем статус подписки
                cursor.execute(
                    """
                    INSERT INTO groups (group_link, subscription_status)
                    VALUES (?, ?)
                    ON CONFLICT(group_link) DO UPDATE SET subscription_status = 1
                """,
                    (link, True),
                )
                conn.commit()

            except Exception as e:
                logger.error(f"Ошибка при подписке на группу {link}: {e}")

        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при запуске Telethon клиента: {e}")

    finally:
        await client.disconnect()
        logger.info("Клиент Telethon остановлен.")
