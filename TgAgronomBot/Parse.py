import telebot
from telethon.sync import TelegramClient, events
from telethon.sessions import SQLiteSession
from telethon.errors import SessionPasswordNeededError
from config import api_id, api_hash, TOKEN, CHANNEL_USERNAME
import asyncio
import os
from loguru import logger

current_directory = os.getcwd()
temp_directory = "temp"
temp_path = os.path.join(current_directory, temp_directory)
log_directory = os.path.join(temp_path, "log")

# Создание директорий для логов, если они не существуют
os.makedirs(log_directory, exist_ok=True)

# Настройка логирования
log_file_path = os.path.join(log_directory, "log_message.log")
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
    level="DEBUG",
    encoding="utf-8",
)

# Инициализация бота для работы с Telegram API
bot = telebot.TeleBot(TOKEN)


def read_keywords(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            keywords = [line.strip() for line in file if line.strip()]
        return keywords
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден.")
        return []


def read_list_from_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            items = [line.strip() for line in file if line.strip()]
        return items
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден.")
        return []


class TelegramParse:
    def __init__(
        self,
        products_file,
        regions_file,
        chat_id,
        process_buy=True,
        process_sell=True,
        groups_file="groups.txt",
        keywords_buy_file="keywords_buy.txt",
        keywords_sell_file="keywords_sell.txt",
        check_interval=10,  # интервал проверки файла (в секундах)
    ):
        # Инициализация класса, задаются продукты, регионы, ID чата, и флаги обработки сообщений
        self.products_file = products_file
        self.regions_file = regions_file
        self.groups_file = groups_file
        self.keywords_buy_file = keywords_buy_file
        self.keywords_sell_file = keywords_sell_file

        self.selected_products = [
            product.lower() for product in read_list_from_file(self.products_file)
        ]
        self.selected_regions = [
            region.lower() for region in read_list_from_file(self.regions_file)
        ]
        self.no_files = not self.selected_products and not self.selected_regions
        self.chat_id = chat_id
        self.group_ids = self.read_group_ids(self.groups_file)
        self.process_buy = process_buy
        self.process_sell = process_sell
        self.processed_messages = (
            set()
        )  # Набор для хранения обработанных сообщений, чтобы избежать дублирования
        self.bot = telebot.TeleBot(TOKEN)  # Инициализация бота для отправки сообщений
        self.keywords_buy = read_keywords(
            self.keywords_buy_file
        )  # Чтение ключевых слов для покупки
        self.keywords_sell = read_keywords(
            self.keywords_sell_file
        )  # Чтение ключевых слов для продажи
        self.check_interval = check_interval
        self.files_mtime = {
            self.groups_file: self.get_file_mtime(self.groups_file),
            self.keywords_buy_file: self.get_file_mtime(self.keywords_buy_file),
            self.keywords_sell_file: self.get_file_mtime(self.keywords_sell_file),
            self.products_file: self.get_file_mtime(self.products_file),
            self.regions_file: self.get_file_mtime(self.regions_file),
        }

    def read_group_ids(self, filename):
        # Чтение ID групп из файла
        try:
            with open(filename, "r", encoding="utf-8") as file:
                group_ids = [line.strip() for line in file if line.strip()]
            return group_ids
        except FileNotFoundError:
            logger.error(f"Файл {filename} не найден.")
            return []

    def get_file_mtime(self, filename):
        try:
            return os.path.getmtime(filename)
        except FileNotFoundError:
            return 0

    def message_contains_product_and_region(self, message_text):
        # Проверка, содержит ли сообщение указанные продукты и регионы
        if self.no_files:
            return True
        for product in self.selected_products:
            for region in self.selected_regions:
                if product in message_text and region in message_text:
                    return True
        return False

    async def monitor_files(self):
        while True:
            await asyncio.sleep(self.check_interval)
            for filename in self.files_mtime:
                current_mtime = self.get_file_mtime(filename)
                if current_mtime != self.files_mtime[filename]:
                    self.files_mtime[filename] = current_mtime
                    if filename == self.groups_file:
                        self.group_ids = self.read_group_ids(self.groups_file)
                        logger.info(
                            f"Файл {self.groups_file} обновлен. Перечитаны ID групп."
                        )
                    elif filename == self.keywords_buy_file:
                        self.keywords_buy = read_keywords(self.keywords_buy_file)
                        logger.info(
                            f"Файл {self.keywords_buy_file} обновлен. Перечитаны ключевые слова для покупки."
                        )
                    elif filename == self.keywords_sell_file:
                        self.keywords_sell = read_keywords(self.keywords_sell_file)
                        logger.info(
                            f"Файл {self.keywords_sell_file} обновлен. Перечитаны ключевые слова для продажи."
                        )
                    elif filename == self.products_file:
                        self.selected_products = [
                            product.lower()
                            for product in read_list_from_file(self.products_file)
                        ]
                        self.no_files = (
                            not self.selected_products and not self.selected_regions
                        )
                        logger.info(
                            f"Файл {self.products_file} обновлен. Перечитаны продукты."
                        )
                    elif filename == self.regions_file:
                        self.selected_regions = [
                            region.lower()
                            for region in read_list_from_file(self.regions_file)
                        ]
                        self.no_files = (
                            not self.selected_products and not self.selected_regions
                        )
                        logger.info(
                            f"Файл {self.regions_file} обновлен. Перечитаны регионы."
                        )

    async def start(self):
        # Запуск клиента Telegram
        async with TelegramClient(
            SQLiteSession("my_session"), api_id, api_hash
        ) as client:
            try:
                await client.start()  # Запуск клиента
            except SessionPasswordNeededError:
                # Если требуется двухфакторная аутентификация
                print("Введите пароль двухфакторной аутентификации: ")
                password = input()
                await client.start(password=password)

            asyncio.create_task(self.monitor_files())

            for group_id in self.group_ids:
                entity = await client.get_input_entity(
                    group_id
                )  # Получение сущности группы

                @client.on(events.NewMessage(chats=entity, incoming=True))
                async def handle_new_message(event):
                    # Обработка нового сообщения
                    message_text = event.message.message.lower().strip()
                    sender = await event.get_sender()
                    sender_id = sender.id
                    sender_name = (
                        sender.username
                        if sender.username
                        else f"{sender.first_name} {sender.last_name}"
                    )
                    sender_phone = sender.phone if sender.phone else "Не указан"

                    if message_text not in self.processed_messages:
                        self.processed_messages.add(
                            message_text
                        )  # Добавление сообщения в обработанные

                        if self.no_files or (
                            (
                                self.process_buy
                                and any(
                                    keyword in message_text
                                    for keyword in self.keywords_buy
                                )
                            )
                            or (
                                self.process_sell
                                and any(
                                    keyword in message_text
                                    for keyword in self.keywords_sell
                                )
                            )
                        ):
                            if self.message_contains_product_and_region(message_text):
                                self.log_message(
                                    message_text, sender_name, sender_id, sender_phone
                                )  # Вывод сообщения и информации об отправителе в консоль

            print("Парсер начал работу. Для остановки нажмите Ctrl+C.")
            await client.run_until_disconnected()  # Ожидание завершения работы клиента

    def log_message(self, message, sender_name, sender_id, sender_phone):
        # Логирование сообщения и информации об отправителе с использованием loguru
        logger.info(
            f"Получено сообщение от {sender_name} (ID: {sender_id}, Телефон: {sender_phone}): {message}"
        )


# Пример использования класса
products_file = "products.txt"
regions_file = "regions.txt"
chat_id = CHANNEL_USERNAME

parser = TelegramParse(products_file, regions_file, chat_id)


# Запуск асинхронного процесса
async def main():
    await parser.start()


if __name__ == "__main__":
    asyncio.run(main())
