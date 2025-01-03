import asyncio
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode, urlparse

from configuration.logger_setup import logger
from dotenv import dotenv_values, load_dotenv
from telethon import TelegramClient, events

# Укажите свои API ID и API Hash, которые вы можете получить на https://my.telegram.org
# api_id = "20270186"
# api_hash = "1f58c726fd918821b4fb08a00e919b13"


def get_env():
    env_path = os.path.join(os.getcwd(), "configuration", ".env")

    if os.path.isfile(env_path):  # Проверяем, существует ли файл
        # Удаляем ранее загруженные переменные
        for key in dotenv_values(env_path).keys():
            if key in os.environ:
                del os.environ[key]

        # Перезагружаем .env
        load_dotenv(env_path)

        # Читаем переменные
        api_id = int(os.getenv("api_id", "50"))
        api_hash = os.getenv("api_hash")

        logger.info("Файл .env загружен успешно.")
        return (
            api_id,
            api_hash,
        )
    else:
        logger.error(f"Файл {env_path} не найден!")
        return None


# Укажите имя сессии
session_name = "client_session"

api_id, api_hash = get_env()
# Создаем клиента
client = TelegramClient(session_name, api_id, api_hash)

# Словарь для хранения входящих сообщений, разделенных по пользователям/группам
incoming_messages = {}


@client.on(events.NewMessage)
async def handle_message(event):
    # Информация об отправителе
    sender = await event.get_sender()

    sender_username = f"@{sender.username}" if sender.username else "Нет username"
    sender_name = f"{sender.first_name or ''} {sender.last_name or ''}".strip()
    sender_id = sender.id
    sender_phone = sender.phone if hasattr(sender, "phone") else "Нет телефона"

    # Определяем категорию отправителя
    if sender.bot:
        sender_type = "Бот"
    elif sender_id < 0:  # Группы и каналы имеют отрицательные ID
        if sender.is_channel:
            sender_type = "Канал"
        else:
            sender_type = "Группа"
    else:
        sender_type = "Человек"

    # Информация о вашей учетной записи (получатель сообщения)
    me = await client.get_me()
    me_username = f"@{me.username}" if me.username else "Нет username"
    me_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
    me_id = me.id
    me_phone = me.phone if hasattr(me, "phone") else "Нет телефона"
    me_is_bot = "Да" if me.bot else "Нет"

    # Сохраняем сообщение в словарь
    if sender_id not in incoming_messages:
        incoming_messages[sender_id] = []
    incoming_messages[sender_id].append(event.text)

    # Выводим все данные об отправителе и назначении
    print(
        f"Источник:\n"
        f"  Имя: {sender_name}\n"
        f"  Username: {sender_username}\n"
        f"  ID: {sender_id}\n"
        f"  Телефон: {sender_phone}\n"
        f"  Тип: {sender_type}\n"
        f"Назначение:\n"
        f"  Имя: {me_name}\n"
        f"  Username: {me_username}\n"
        f"  ID: {me_id}\n"
        f"  Телефон: {me_phone}\n"
        f"  Это бот: {me_is_bot}\n"
        f"Сообщение: {event.text}\n"
    )

    # Сохраняем в файл
    with open("messages_log.txt", "a", encoding="utf-8") as file:
        file.write(
            f"Источник:\n"
            f"  Имя: {sender_name}\n"
            f"  Username: {sender_username}\n"
            f"  ID: {sender_id}\n"
            f"  Телефон: {sender_phone}\n"
            f"  Тип: {sender_type}\n"
            f"Назначение:\n"
            f"  Имя: {me_name}\n"
            f"  Username: {me_username}\n"
            f"  ID: {me_id}\n"
            f"  Телефон: {me_phone}\n"
            f"  Это бот: {me_is_bot}\n"
            f"Сообщение: {event.text}\n\n"
        )


# Запускаем клиента для получения сообщений
async def main():
    print("Клиент запускается. Авторизуйтесь в Telegram...")
    await client.start()
    print("Клиент запущен. Ожидаем сообщения...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
