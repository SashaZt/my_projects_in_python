import random
import asyncio

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

                max_retries = 5  # Максимальное количество попыток
                retry_count = 0

                while retry_count < max_retries:
                    try:
                        # Подписываемся на группу
                        await client(JoinChannelRequest(link))
                        logger.info(f"Успешно подписались на группу: {link}")

                        # Рандомная пауза с диапазоном из конфига
                        pause_duration = random.uniform(PAUSE_MIN, PAUSE_MAX)
                        logger.info(
                            f"Ожидание {pause_duration:.2f} секунд перед следующей отправкой."
                        )
                        await asyncio.sleep(pause_duration)

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
                        break  # Успех, выходим из цикла повторных попыток

                    except Exception as e:
                        error_message = str(e)

                        # Обрабатываем ошибку "No user has ..."
                        if "No user has" in error_message:
                            logger.warning(f"Группа {link} пропущена: {error_message}")
                            break  # Прерываем цикл, пропуская эту группу

                        # Обрабатываем ошибку ожидания
                        if "A wait of" in error_message:
                            wait_time = int(
                                "".join(filter(str.isdigit, error_message.split("A wait of")[1]))
                            )
                            wait_time += 60  # Добавляем 60 секунд
                            logger.warning(
                                f"Подписка на группу {link} требует ожидания {wait_time} секунд. Попробуем снова."
                            )
                            await asyncio.sleep(wait_time)
                            retry_count += 1
                        else:
                            raise  # Если ошибка не обработана, пробрасываем её дальше

                if retry_count >= max_retries:
                    logger.error(f"Не удалось подписаться на группу {link} после {max_retries} попыток.")
            except Exception as e:
                logger.error(f"Ошибка при подписке на группу {link}: {e}")

        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при запуске Telethon клиента: {e}")

    finally:
        await client.disconnect()
        logger.info("Клиент Telethon остановлен.")
