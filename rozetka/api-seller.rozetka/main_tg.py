# main_tg.py
import asyncio
import sqlite3
import time
from pathlib import Path

from logger import logger
from main_alert import send_alert, send_alert_sync
from main_token import load_product_data
from telethon.errors import SessionPasswordNeededError
from telethon.sync import TelegramClient
from telethon.tl.functions.contacts import ImportContactsRequest
from telethon.tl.types import InputPhoneContact

# Настройка путей и директорий
current_directory = Path.cwd()
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
config_json_file = config_directory / "config.json"
# Данные для авторизации
config = load_product_data(config_json_file)
api_id = config["tg"]["api_id"]
api_hash = config["tg"]["api_hash"]
phone_number = config["tg"]["phone_number"]


# Имя файла сессии
session_file = f"my_telegram_session_{phone_number}"


async def send_message(user_phone, message, key_ids, order_id, codes):
    # Создаем клиент с сохранением сессии
    client = TelegramClient(session_file, api_id, api_hash)

    # Сначала подключаемся
    logger.info("Подключение к Telegram...")
    await client.connect()

    # Проверяем, авторизован ли клиент
    if not await client.is_user_authorized():
        logger.error(
            "Требуется авторизация. Пожалуйста, введите код из сообщения Telegram."
        )
        await client.send_code_request(phone_number)
        code = input("Введите полученный код: ")

        try:
            await client.sign_in(phone_number, code)
        except SessionPasswordNeededError:
            # Если требуется пароль
            password = input("Введите пароль двухфакторной аутентификации: ")
            await client.sign_in(password=password)

        logger.info("Авторизация выполнена успешно!")
    else:
        logger.info("Используем сохраненную сессию.")

    logger.info("Успешное подключение!")

    try:
        # Добавляем контакт
        contact = InputPhoneContact(
            client_id=0, phone=user_phone, first_name="User", last_name=""
        )
        result = await client(ImportContactsRequest([contact]))

        # Получаем информацию о пользователе
        users = result.users
        if users:
            logger.info(f"Пользователь найден: {users[0].id}")

            # Добавляем задержку перед отправкой сообщения, чтобы не превысить лимиты
            await asyncio.sleep(3)

            # Отправляем сообщение
            await client.send_message(users[0], message)
            logger.info("Сообщение отправлено!")

            # Важная задержка, чтобы избежать превышения лимитов
            await asyncio.sleep(5)

            # Отправляем уведомление напрямую, но с задержкой
            # ВАЖНО: напрямую ждем выполнения функции, не создавая отдельную задачу
            message_alert = f"Пользователь с номером телефона {user_phone} ключ/и {codes} отправлен."
            logger.info(f"Ожидание 30 секунд перед отправкой уведомления...")
            await asyncio.sleep(
                30
            )  # Более короткая пауза, но мы будем ждать результата
            await send_alert(message_alert)  # Важно: используем await!

        else:
            logger.warning(f"Пользователь с номером телефона {user_phone} не найден")

            # Важная задержка перед отправкой уведомления об ошибке
            await asyncio.sleep(10)

            # Отправляем уведомление об ошибке напрямую
            message_alert = f"Пользователь с номером телефона {user_phone} не найден. Его заказ {order_id}, ключ/и {codes}."
            logger.info(f"Ожидание 30 секунд перед отправкой уведомления об ошибке...")
            await asyncio.sleep(30)
            # Напрямую ждем выполнения
            await send_alert(message_alert)

    except Exception as e:
        logger.warning(f"Произошла ошибка при отправке сообщения: {e}")
        # Отправляем уведомление об ошибке
        try:
            error_message = f"Ошибка при отправке сообщения пользователю {user_phone} (заказ {order_id}): {e}"
            await asyncio.sleep(10)
            await send_alert(error_message)
        except Exception as alert_error:
            logger.error(f"Не удалось отправить уведомление об ошибке: {alert_error}")
    finally:
        # Отключаемся в любом случае
        await client.disconnect()
        logger.info("Отключено от Telegram")


async def send_message_review(user_phone, message):
    # Создаем клиент с сохранением сессии
    client = TelegramClient(session_file, api_id, api_hash)

    try:
        # Сначала подключаемся
        logger.info("Подключение к Telegram...")
        await client.connect()

        # Проверяем, авторизован ли клиент
        if not await client.is_user_authorized():
            logger.error(
                "Требуется авторизация. Запустите скрипт в интерактивном режиме для ввода кода."
            )
            return False

        logger.info("Успешное подключение!")

        # Добавляем контакт
        contact = InputPhoneContact(
            client_id=0, phone=user_phone, first_name="User", last_name=""
        )
        result = await client(ImportContactsRequest([contact]))

        # Получаем информацию о пользователе
        users = result.users
        if users:
            logger.info(f"Пользователь найден: {users[0].id}")
            await asyncio.sleep(1)  # Небольшая задержка

            # Отправляем сообщение
            await client.send_message(users[0], message)
            logger.info("Сообщение с запросом отзыва отправлено!")
            return True
        else:
            logger.warning(f"Пользователь с номером телефона {user_phone} не найден")
            await send_alert(
                f"Не удалось отправить запрос на отзыв пользователю {user_phone} - пользователь не найден"
            )
            return False

    except Exception as e:
        error_message = (
            f"Ошибка при отправке запроса на отзыв пользователю {user_phone}: {e}"
        )
        logger.error(error_message)
        await send_alert(error_message)
        return False
    finally:
        # Отключаемся в любом случае
        await client.disconnect()
        logger.info("Отключено от Telegram")
