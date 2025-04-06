# main_tg.py
import asyncio
from pathlib import Path

from logger import logger
from main_db import mark_keys_as_sent
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


def get_telegram_client():
    """Создает и возвращает клиент Telegram."""
    client = TelegramClient(session_file, api_id, api_hash)
    return client


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
            # message = "Привет! Это тестовое сообщение."
            # Отправляем сообщение
            await client.send_message(users[0], message)
            logger.info("Сообщение отправлено!")

            message_alert = f"Пользовател. с номером телефона {user_phone} ключ/и {codes} отправлен."
            await send_message_alert(client, message_alert)

            mark_keys_as_sent(order_id, key_ids)

        else:
            message_alert = f"Пользователь с номером телефона {user_phone} не найден. Его заказ {order_id}, ключ/и {codes}."
            await send_message_alert(client, message_alert)

            logger.warning(f"Пользователь с номером телефона {user_phone} не найден")
    except Exception as e:
        logger.warning(f"Произошла ошибка: {e}")
    finally:
        # Отключаемся в любом случае
        await client.disconnect()
        logger.info("Отключено от Telegram")


async def send_message_alert(client_or_func, message):
    """Отправляет сообщение-уведомление администратору.

    Args:
        client_or_func: Телеграм-клиент или функция, возвращающая клиент
        message: Текст сообщения
    """
    # Проверяем, что передано - клиент или функция
    if callable(client_or_func) and client_or_func.__name__ == "get_telegram_client":
        # Это функция get_telegram_client - создаем новый клиент напрямую
        client = TelegramClient(session_file, api_id, api_hash)
        need_connect = True
    else:
        # Это уже клиент
        client = client_or_func
        need_connect = False

    user_phone = "+380737372554"

    try:
        if need_connect:
            # Подключаемся, если нужно
            await client.connect()
            if not await client.is_user_authorized():
                logger.error("Клиент не авторизован для отправки уведомления")
                return

        contact = InputPhoneContact(
            client_id=0, phone=user_phone, first_name="User", last_name=""
        )
        result = await client(ImportContactsRequest([contact]))
        users = result.users
        if users:
            await client.send_message(users[0], message)
            logger.info(f"Отправлено уведомление: {message}")
        else:
            logger.warning("Пользователь для алерта не найден")
    except Exception as e:
        logger.warning(f"Ошибка при отправке алерта: {e}")
    finally:
        # Отключаемся только если мы сами подключились
        if need_connect:
            await client.disconnect()
