import telebot
from telethon.sync import TelegramClient, events
from telethon.sessions import SQLiteSession
from telethon.errors import SessionPasswordNeededError
import asyncio
from functions.helpers import read_keywords, read_list_from_file
from functions.parse_message import parse_message
from config import api_id, api_hash, TOKEN
from loguru import logger
import os
import json
from databases import Database

# Настройки базы данных
db_type = "mysql"
username = "python_mysql"
password = "python_mysql"
host = "45.137.155.18"  # или "localhost"
port = "3306"
db_name = "corn"
database_url = f"{db_type}://{username}:{password}@{host}:{port}/{db_name}"

# Инициализация базы данных
database = Database(database_url)


class TelegramParse:
    def __init__(
        self,
        database_url,
        products_file,
        regions_file,
        chat_id,
        process_buy=True,
        process_sell=True,
        groups_file="groups.txt",
        keywords_buy_file="keywords_buy.txt",
        keywords_sell_file="keywords_sell.txt",
        keywords_products_file="keywords_products.json",
        keywords_regions_file="keywords_regions.json",
        check_interval=10,  # интервал проверки файла (в секундах)
    ):
        self.database = databases.Database(database_url)
        self.products_file = products_file
        self.regions_file = regions_file
        self.groups_file = groups_file
        self.keywords_buy_file = keywords_buy_file
        self.keywords_sell_file = keywords_sell_file
        self.keywords_products_file = keywords_products_file
        self.keywords_regions_file = keywords_regions_file

        self.selected_products = [
            product.lower() for product in read_list_from_file(self.products_file)
        ]
        self.selected_regions = [
            region.lower() for region in read_list_from_file(self.regions_file)
        ]
        self.product_keywords = self.read_product_keywords(self.keywords_products_file)
        self.region_keywords = self.read_region_keywords(self.keywords_regions_file)
        self.no_files = not self.selected_products and not self.selected_regions
        self.chat_id = chat_id
        self.group_ids = self.read_group_ids(self.groups_file)
        self.process_buy = process_buy
        self.process_sell = process_sell
        self.processed_messages = set()
        self.bot = telebot.TeleBot(TOKEN)
        self.keywords_buy = read_keywords(self.keywords_buy_file)
        self.keywords_sell = read_keywords(self.keywords_sell_file)
        self.check_interval = check_interval
        self.files_mtime = {
            self.groups_file: self.get_file_mtime(self.groups_file),
            self.keywords_buy_file: self.get_file_mtime(self.keywords_buy_file),
            self.keywords_sell_file: self.get_file_mtime(self.keywords_sell_file),
            self.products_file: self.get_file_mtime(self.products_file),
            self.regions_file: self.get_file_mtime(self.regions_file),
            self.keywords_products_file: self.get_file_mtime(
                self.keywords_products_file
            ),
            self.keywords_regions_file: self.get_file_mtime(self.keywords_regions_file),
        }

    def read_product_keywords(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                raw_keywords = json.load(file)
                product_keywords = {}
                for entry in raw_keywords:
                    for material, keywords in entry.items():
                        product_keywords[material] = keywords
                return product_keywords
        except FileNotFoundError:
            logger.error(f"Файл {filename} не найден.")
            return {}

    def read_region_keywords(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as file:
                raw_keywords = json.load(file)
                region_keywords = {}
                for entry in raw_keywords:
                    for region, keywords in entry.items():
                        region_keywords[region] = keywords
                return region_keywords
        except FileNotFoundError:
            logger.error(f"Файл {filename} не найден.")
            return {}

    def read_group_ids(self, filename):
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
                    elif filename == self.keywords_products_file:
                        self.product_keywords = self.read_product_keywords(
                            self.keywords_products_file
                        )
                        logger.info(
                            f"Файл {self.keywords_products_file} обновлен. Перечитаны ключевые слова для продуктов."
                        )
                    elif filename == self.keywords_regions_file:
                        self.region_keywords = self.read_region_keywords(
                            self.keywords_regions_file
                        )
                        logger.info(
                            f"Файл {self.keywords_regions_file} обновлен. Перечитаны ключевые слова для регионов."
                        )

    async def start(self):
        await self.database.connect()
        async with TelegramClient(
            SQLiteSession("my_session"), api_id, api_hash
        ) as client:
            try:
                await client.start()
            except SessionPasswordNeededError:
                print("Введите пароль двухфакторной аутентификации: ")
                password = input()
                await client.start(password=password)

            asyncio.create_task(self.monitor_files())

            for group_id in self.group_ids:
                entity = await client.get_input_entity(group_id)

                @client.on(events.NewMessage(chats=entity, incoming=True))
                async def handle_new_message(event):
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
                        self.processed_messages.add(message_text)

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
                                )
                                await self.save_message(
                                    message_text, sender_name, sender_id, sender_phone
                                )

            print("Парсер начал работу. Для остановки нажмите Ctrl+C.")
            await client.run_until_disconnected()
        await self.database.disconnect()

    def log_message(self, message, sender_name, sender_id, sender_phone):
        logger.info(
            f"Получено сообщение от {sender_name} (ID: {sender_id}, Телефон: {sender_phone}): {message}"
        )
        parsed_result = parse_message(
            message, self.product_keywords, self.region_keywords
        )
        print(parsed_result)

    async def save_message(self, message, sender_name, sender_id, sender_phone):
        parsed_result = parse_message(
            message, self.product_keywords, self.region_keywords
        )
        message_record_template = {
            "sender_name": sender_name,
            "sender_id": sender_id,
            "sender_phone": sender_phone,
            "message": message,
        }

        # Запись всех сообщений
        with open("messages_all.txt", "a", encoding="utf-8") as file_all:
            file_all.write(
                json.dumps(message_record_template, ensure_ascii=False) + "\n"
            )

        # Разделение на "купить" и "продать"
        is_buy = any(keyword in message for keyword in self.keywords_buy)
        is_sell = any(keyword in message for keyword in self.keywords_sell)

        if is_buy:
            await self.save_to_db(
                message, sender_name, sender_id, sender_phone, parsed_result, "buy"
            )
            self.save_to_file(
                message,
                sender_name,
                sender_id,
                sender_phone,
                parsed_result,
                "messages_buy.txt",
            )
        if is_sell:
            await self.save_to_db(
                message, sender_name, sender_id, sender_phone, parsed_result, "sell"
            )
            self.save_to_file(
                message,
                sender_name,
                sender_id,
                sender_phone,
                parsed_result,
                "messages_sell.txt",
            )

    def save_to_file(
        self, message, sender_name, sender_id, sender_phone, parsed_result, filename
    ):
        # Дублирование сообщений для каждого ключевого слова продукта и региона
        for raw_material in parsed_result["Raw Materials"]:
            for region in parsed_result["Regions"]:
                message_record = {
                    "sender_name": sender_name,
                    "sender_id": sender_id,
                    "sender_phone": sender_phone,
                    "parsed_result": {
                        "Phones": parsed_result["Phones"],
                        "Raw Materials": [raw_material],
                        "Regions": [region],
                        "Messages": parsed_result["Messages"],
                    },
                }
                with open(filename, "a", encoding="utf-8") as file:
                    file.write(json.dumps(message_record, ensure_ascii=False) + "\n")

    async def save_to_db(
        self, message, sender_name, sender_id, sender_phone, parsed_result, trade_type
    ):
        query = """
        INSERT INTO corn.messages_tg (sender_name, sender_id, sender_phone, Phones, Raw_Materials, Regions, Messages, trade, data_time)
        VALUES (:sender_name, :sender_id, :sender_phone, :Phones, :Raw_Materials, :Regions, :Messages, :trade, NOW())
        """
        for raw_material in parsed_result["Raw Materials"]:
            for region in parsed_result["Regions"]:
                values = {
                    "sender_name": sender_name,
                    "sender_id": sender_id,
                    "sender_phone": sender_phone,
                    "Phones": json.dumps(parsed_result["Phones"], ensure_ascii=False),
                    "Raw_Materials": json.dumps([raw_material], ensure_ascii=False),
                    "Regions": json.dumps([region], ensure_ascii=False),
                    "Messages": json.dumps(
                        parsed_result["Messages"], ensure_ascii=False
                    ),
                    "trade": trade_type,
                }
                await self.database.execute(query=query, values=values)
