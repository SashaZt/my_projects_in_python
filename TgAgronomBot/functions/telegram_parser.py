import telebot
from telethon.sync import TelegramClient, events
from telethon.sessions import SQLiteSession
from telethon.errors import SessionPasswordNeededError
import asyncio
from functions.helpers import read_keywords, read_list_from_file
from functions.parse_message import parse_message
from configuration.config import api_id, api_hash, TOKEN
from configuration.logger_setup import logger
import os
import json
from configuration.config import database  # Импортируйте объект базы данных
from databases import Database

current_directory = os.getcwd()
logging_directory = "logging"
logging_path = os.path.join(current_directory, logging_directory)
os.makedirs(logging_path, exist_ok=True)

messages_all_path = os.path.join(logging_path, "messages_all.txt")
messages_buy_path = os.path.join(logging_path, "messages_buy.txt")
messages_sell_path = os.path.join(logging_path, "messages_sell.txt")


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
        self.database = Database(database_url)
        self.products_file = os.path.join("keywords", products_file)
        self.regions_file = os.path.join("keywords", regions_file)
        self.groups_file = os.path.join("keywords", groups_file)
        self.keywords_buy_file = os.path.join("keywords", keywords_buy_file)
        self.keywords_sell_file = os.path.join("keywords", keywords_sell_file)
        self.keywords_products_file = os.path.join("keywords", keywords_products_file)
        self.keywords_regions_file = os.path.join("keywords", keywords_regions_file)

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

                    if sender is None:
                        logger.error("Sender is None, cannot process message.")
                        return

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
        logger.info("Entering save_message function")
        logger.info(
            f"Received message: {message}, sender_name: {sender_name}, sender_id: {sender_id}, sender_phone: {sender_phone}"
        )

        parsed_result = parse_message(
            message, self.product_keywords, self.region_keywords
        )
        # logger.info(f"Parsed result: {parsed_result}")

        message_record_template = {
            "sender_name": sender_name,
            "sender_id": sender_id,
            "sender_phone": sender_phone,
            "message": message,
        }

        # Запись всех сообщений
        with open(messages_all_path, "a", encoding="utf-8") as file_all:
            file_all.write(
                json.dumps(message_record_template, ensure_ascii=False) + "\n"
            )

        # Разделение на "купить" и "продать"
        is_buy = any(keyword in message for keyword in self.keywords_buy)
        is_sell = any(keyword in message for keyword in self.keywords_sell)

        # logger.info(f"is_buy: {is_buy}, is_sell: {is_sell}, message: {message}")

        if is_buy:
            # logger.info("Detected 'buy' message")
            await self.save_to_db(
                message, sender_name, sender_id, sender_phone, parsed_result, "buy"
            )
            self.save_to_file(
                message,
                sender_name,
                sender_id,
                sender_phone,
                parsed_result,
                messages_buy_path,
            )
        if is_sell:
            logger.info("Detected 'sell' message")
            await self.save_to_db(
                message, sender_name, sender_id, sender_phone, parsed_result, "sell"
            )
            self.save_to_file(
                message,
                sender_name,
                sender_id,
                sender_phone,
                parsed_result,
                messages_sell_path,
            )

    def save_to_file(
        self, message, sender_name, sender_id, sender_phone, parsed_result, filename
    ):
        raw_materials = (
            parsed_result["Raw Materials"].split(", ")
            if parsed_result["Raw Materials"]
            else []
        )
        regions = (
            parsed_result["Regions"].split(", ") if parsed_result["Regions"] else []
        )

        if not raw_materials:
            raw_materials = ["Unknown"]
        if not regions:
            regions = ["Unknown"]

        for raw_material in raw_materials:
            for region in regions:
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
        # logger.info("Entering save_to_db function")
        # logger.info(
        #     f"Received data: message={message}, sender_name={sender_name}, sender_id={sender_id}, sender_phone={sender_phone}, parsed_result={parsed_result}, trade_type={trade_type}"
        # )

        check_query = """
        SELECT COUNT(*) FROM corn.messages_tg 
        WHERE Messages = :Messages AND data_time >= NOW() - INTERVAL 15 MINUTE
        """

        insert_query = """
        INSERT INTO corn.messages_tg (sender_name, sender_id, sender_phone, Phones, Raw_Materials, Regions, Messages, trade, data_time)
        VALUES (:sender_name, :sender_id, :sender_phone, :Phones, :Raw_Materials, :Regions, :Messages, :trade, NOW())
        """

        raw_materials = (
            parsed_result["Raw Materials"].split(", ")
            if parsed_result["Raw Materials"]
            else ["Unknown"]
        )
        regions = (
            parsed_result["Regions"].split(", ")
            if parsed_result["Regions"]
            else ["Unknown"]
        )

        for raw_material in raw_materials:
            for region in regions:
                values = {
                    "sender_name": sender_name,
                    "sender_id": sender_id,
                    "sender_phone": sender_phone,
                    "Phones": parsed_result["Phones"],
                    "Raw_Materials": raw_material,
                    "Regions": region,
                    "Messages": parsed_result["Messages"],
                    "trade": trade_type,
                }
                try:
                    logger.info(
                        f"Preparing to check for duplicates with values: {values}"
                    )
                    duplicate_check_result = await self.database.fetch_one(
                        query=check_query,
                        values={"Messages": parsed_result["Messages"]},
                    )

                    if duplicate_check_result[0] == 0:
                        logger.info(
                            f"No duplicate found. Preparing to save to DB with values: {values}"
                        )
                        result = await self.database.execute(
                            query=insert_query, values=values
                        )
                        logger.info(f"Successfully saved to DB, result: {result}")
                    else:
                        logger.info(
                            f"Duplicate found. Skipping save to DB for values: {values}"
                        )
                except Exception as e:
                    logger.error(f"Error saving to DB: {e}")
                    logger.error(f"Failed values: {values}")
