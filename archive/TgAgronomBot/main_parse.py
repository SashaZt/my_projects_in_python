import asyncio
from functions.telegram_parser import TelegramParse
from configuration.config import CHANNEL_USERNAME, database_url


def main():
    products_file = "products.txt"
    regions_file = "regions.txt"
    chat_id = CHANNEL_USERNAME

    parser = TelegramParse(database_url, products_file, regions_file, chat_id)

    async def start_parser():
        await parser.start()

    asyncio.run(start_parser())


if __name__ == "__main__":
    main()
