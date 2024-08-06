from telethon import TelegramClient
import asyncio
import aiosqlite
from configuration.logger_setup import logger
import os

# Ваши данные Telegram
api_id = "29672931"
api_hash = "91335e92be641e03aca068501705a503"
phone_number = "+380501963867"  # Номер телефона вашего аккаунта

# Создание клиента Telethon с именем сессии
client = TelegramClient("session_name", api_id, api_hash)
# Получение текущей директории и создание пути для базы данных
current_directory = os.getcwd()
database_path = os.path.join(current_directory, "database")

# Создание директории для базы данных, если она не существует
os.makedirs(database_path, exist_ok=True)
DATABASE = os.path.join(database_path, "bot_data.db")


async def send_message_to_groups(message_text):
    # Подключение к базе данных и извлечение списка group_id
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT group_id FROM groups") as cursor:
            groups = await cursor.fetchall()
            group_ids = [group_id[0] for group_id in groups]

    # Отправка сообщений в группы
    for group_id in group_ids:
        try:
            await client.send_message(group_id, message_text)
            logger.info(
                f"Сообщение '{message_text}' отправлено в группу с ID {group_id}"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в группу с ID {group_id}: {e}")


async def main():
    # Асинхронный старт клиента
    await client.start(phone_number)
    logger.info("Клиент Telethon запущен")

    # Запросить ввод сообщения от пользователя
    message_text = input("Введите сообщение для отправки в группы: ")
    await send_message_to_groups(message_text)

    # Завершение работы клиента
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
