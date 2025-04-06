# main_alert.py
import asyncio
import time
from pathlib import Path

from logger import logger
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
admin_phone = "+380737372554"  # Номер телефона администратора для уведомлений

# Имя файла сессии для уведомлений
alert_session_file = f"alert_telegram_session_{phone_number}"

# НЕ создаем глобальный клиент - это вызывает проблемы с циклами событий asyncio


async def init_alert_client():
    """Инициализирует клиент для уведомлений и проверяет его авторизацию."""
    client = TelegramClient(alert_session_file, api_id, api_hash)

    # Подключаемся
    await client.connect()

    # Проверяем, авторизован ли клиент
    if not await client.is_user_authorized():
        logger.info("Клиент для уведомлений не авторизован, выполняется авторизация...")
        try:
            await client.send_code_request(phone_number)
            code = input("Введите код из сообщения Telegram для клиента уведомлений: ")
            try:
                await client.sign_in(phone_number, code)
            except SessionPasswordNeededError:
                password = input("Введите пароль двухфакторной аутентификации: ")
                await client.sign_in(password=password)
            logger.info("Клиент для уведомлений успешно авторизован!")
        except Exception as e:
            logger.error(f"Ошибка при авторизации клиента для уведомлений: {e}")
            return False
    else:
        logger.info("Клиент для уведомлений уже авторизован.")

    await client.disconnect()
    return True


async def send_alert(message):
    """Отправляет уведомление администратору."""
    # Создаем новый клиент каждый раз
    client = TelegramClient(alert_session_file, api_id, api_hash)
    max_retries = 5  # Увеличиваем количество попыток
    retry_count = 0

    while retry_count < max_retries:
        try:
            # Подключаемся
            await client.connect()

            # Увеличиваем экспоненциально паузу между попытками
            # Первая попытка: 30 секунд, вторая: 60 секунд, третья: 120 секунд и т.д.
            delay = 30 * (2**retry_count)
            logger.info(
                f"Пауза {delay} секунд перед отправкой уведомления... (попытка {retry_count+1}/{max_retries})"
            )
            await asyncio.sleep(delay)

            # Проверяем авторизацию
            if not await client.is_user_authorized():
                logger.error(
                    "Клиент для уведомлений не авторизован, запустите init_alert_client()."
                )
                await client.disconnect()
                return False

            # Добавляем контакт администратора
            contact = InputPhoneContact(
                client_id=0, phone=admin_phone, first_name="Admin", last_name=""
            )
            result = await client(ImportContactsRequest([contact]))

            # Отправляем сообщение
            users = result.users
            if users:
                await client.send_message(users[0], message)
                logger.info(f"Отправлено уведомление: {message}")
                await client.disconnect()
                return True
            else:
                logger.error(f"Администратор с номером {admin_phone} не найден")
                await client.disconnect()
                return False
        except Exception as e:
            retry_count += 1
            if "Too many requests" in str(e):
                logger.warning(
                    f"Превышен лимит запросов Telegram (попытка {retry_count}/{max_retries}): {e}"
                )
            else:
                logger.warning(
                    f"Ошибка при отправке уведомления (попытка {retry_count}/{max_retries}): {e}"
                )

            try:
                await client.disconnect()
            except:
                pass

            # Не выполняем паузу после последней попытки
            if retry_count < max_retries:
                continue

    logger.error(f"Не удалось отправить уведомление после {max_retries} попыток")
    return False


def send_alert_sync(message):
    """Синхронная обертка для отправки уведомления.

    Args:
        message (str): Текст сообщения

    Returns:
        bool: True если уведомление успешно отправлено, иначе False
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_alert(message))
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Ошибка при синхронной отправке уведомления: {e}")
        return False


def init_alert_client_sync():
    """Синхронная обертка для инициализации клиента уведомлений."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(init_alert_client())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"Ошибка при инициализации клиента уведомлений: {e}")
        return False


# Если файл запускается напрямую - инициализируем клиент
if __name__ == "__main__":
    init_alert_client_sync()
    if send_alert_sync("Тестовое уведомление"):
        logger.info("Тестовое уведомление успешно отправлено")
    else:
        logger.error("Не удалось отправить тестовое уведомление")
