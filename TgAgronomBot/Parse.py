import telebot
from telethon.sessions import SQLiteSession
from telethon.sync import TelegramClient, events
from telethon.errors import SessionPasswordNeededError
from config import api_id, api_hash, bot_token

bot = telebot.TeleBot(bot_token)

class TelegramParse:
    def __init__(self, selected_products, selected_regions, chat_id, process_buy=True, process_sell=True):
        self.selected_products = [product.lower() for product in selected_products]
        self.selected_regions = [region.lower() for region in selected_regions]
        self.chat_id = chat_id
        self.group_ids = self.read_group_ids("groups.txt")
        self.process_buy = process_buy
        self.process_sell = process_sell
        self.processed_messages = set()
        self.bot = telebot.TeleBot(bot_token)
        self.keywords_buy = [
            "покупаю", "куплю", "купити", "купуємо", "закупаємо", "купуємо",
            "придбаємо", "закуповуємо", "закуповує", "купую", "закупаем",
            "покупаем", 'закупівля'
        ]
        self.keywords_sell = [
            "продаю", "продам", "продати", "продаем", "продаж", "продаємо",
            "продаемо", "купленного"
        ]

    def read_group_ids(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                group_ids = [line.strip() for line in file if line.strip()]
            return group_ids
        except FileNotFoundError:
            print(f"Файл {filename} не найден.")
            return []

    def message_contains_product_and_region(self, message_text):
        for product in self.selected_products:
            for region in self.selected_regions:
                if product in message_text and region in message_text:
                    return True
        return False

    async def start(self):
        async with TelegramClient(SQLiteSession(), api_id, api_hash) as client:
            try:
                await client.start()
            except SessionPasswordNeededError:
                # password = input("Введите пароль двухфакторной аутентификации: ")
                # await client.start(password=password)
                pass
            for group_id in self.group_ids:
                entity = await client.get_input_entity(group_id)

                @client.on(events.NewMessage(chats=entity, incoming=True))
                async def handle_new_message(event):
                    message_text = event.message.message.lower().strip()

                    if message_text not in self.processed_messages:
                        self.processed_messages.add(message_text)

                        if self.process_buy and any(keyword in message_text for keyword in self.keywords_buy):
                            if self.message_contains_product_and_region(message_text):
                                await self.send_telebot_message(event.message.message)

                        if self.process_sell and any(keyword in message_text for keyword in self.keywords_sell):
                            if self.message_contains_product_and_region(message_text):
                                await self.send_telebot_message(event.message.message)

            print("Парсер начал работу. Для остановки нажмите Ctrl+C.")
            await client.run_until_disconnected()

    async def send_telebot_message(self, message):
        try:
            await bot.send_message(self.chat_id, message)
        except Exception as e:
            print(f"Ошибка отправки сообщения в telebot: {e}")

# async def start_parsing_for_users(user_configs):
#     tasks = []
#     for config in user_configs:
#         parser = TelegramParse(
#             selected_products=config['selected_products'],
#             selected_regions=config['selected_regions'],
#             chat_id=config['chat_id'],
#             process_buy=config.get('process_buy', True),
#             process_sell=config.get('process_sell', True)
#         )
#         tasks.append(parser.start())
#     await asyncio.gather(*tasks)
