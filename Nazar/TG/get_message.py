import asyncio
from pathlib import Path

import httpx  # Асинхронная библиотека для HTTP-запросов
from configuration.config import API_HASH, API_ID, API_URL, SESSION_PATH
from configuration.logger_setup import logger
from telethon import TelegramClient, events

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
session_directory = current_directory / SESSION_PATH
session_directory.mkdir(parents=True, exist_ok=True)

logger.info(API_HASH)
logger.info(API_ID)


# Функция для запроса номера телефона и создания имени сессии
def get_session_name():
    phone_number = input("Введите номер телефона (в формате +1234567890): ").strip()
    session_name = session_directory / f"{phone_number}.session"
    return phone_number, session_name


# Получаем номер телефона и имя сессии
phone_number, session_name = get_session_name()

# Создаем клиента
client = TelegramClient(str(session_name), API_ID, API_HASH)

# Словарь для хранения входящих сообщений, разделенных по пользователям/группам
incoming_messages = {}


# Функция для определения категории источника
def get_sender_type(sender):
    """
    Определяет категорию отправителя.
    :param sender: объект отправителя из Telethon
    :return: строка с типом отправителя
    """
    if sender.bot:
        return "bot"
    elif sender.id < 0:  # Отрицательные ID используются для групп и каналов
        if sender.is_channel:
            return "channel"
        elif sender.is_group:
            return "group"
    else:
        return "user"


async def send_to_api(data):
    """
    Отправляет данные на API, игнорируя проверку SSL.
    :param data: словарь с данными
    """
    async with httpx.AsyncClient(verify=False) as client:  # Отключаем проверку SSL
        try:
            response = await client.post(API_URL, json=data)
            response.raise_for_status()  # Проверяем статус ответа
            logger.info(f"Данные успешно отправлены: {response.json()}")
        except httpx.HTTPError as e:
            logger.error(f"Ошибка при отправке данных на API: {e}")


@client.on(events.NewMessage)
async def handle_message(event):
    # Информация об отправителе
    sender = await event.get_sender()

    sender_username = f"@{sender.username}" if sender.username else None
    sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
    sender_id = sender.id
    sender_phone = sender.phone if hasattr(sender, "phone") else None

    # Определяем категорию отправителя
    sender_type = get_sender_type(sender)

    # Информация о вашей учетной записи (получатель сообщения)
    recipient = await client.get_me()
    recipient_username = f"@{recipient.username}" if recipient.username else None
    recipient_name = f"{recipient.first_name or ''} {recipient.last_name or ''}".strip()
    recipient_id = recipient.id
    recipient_phone = recipient.phone if hasattr(recipient, "phone") else None

    # Формируем данные для отправки
    all_data = {
        "sender_name": sender_name,
        "sender_username": sender_username,
        "sender_id": sender_id,
        "sender_phone": sender_phone,
        "sender_type": sender_type,
        "recipient_name": recipient_name,
        "recipient_username": recipient_username,
        "recipient_id": recipient_id,
        "recipient_phone": recipient_phone,
        "message": event.text,
    }

    logger.info(f"Отправляем данные: {all_data}")
    await send_to_api(all_data)


# Запускаем клиента для получения сообщений
async def main():
    logger.info("Клиент запускается. Авторизуйтесь в Telegram...")
    await client.start(
        phone=lambda: phone_number
    )  # Используем введенный номер телефона
    logger.info(f"Клиент запущен. Сессия сохранена в файле: {session_name}")
    logger.info("Ожидаем сообщения...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
