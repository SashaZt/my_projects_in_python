import asyncio
import os

from aiogram import Bot
from dotenv import load_dotenv


async def check_channel(bot: Bot, channel_id: int):
    try:
        chat = await bot.get_chat(channel_id)
        print(f"✅ Канал найден: {chat.title}")
        print(f"ID: {chat.id}")
        print(f"Тип: {chat.type}")
        return True
    except Exception as e:
        print(f"❌ Ошибка для канала {channel_id}: {e}")
        return False


async def main():
    load_dotenv("configuration/.env")
    bot_token = os.getenv("BOT_TOKEN_REPOST")

    # Пробуем разные форматы ID
    channel_id = int(os.getenv("CHANNEL_ID_MODELS_PRO"))
    test_ids = [channel_id, -channel_id, int(f"-100{abs(channel_id)}")]

    bot = Bot(token=bot_token)
    try:
        print("Проверяем разные форматы ID...")
        for test_id in test_ids:
            print(f"\nПроверка ID: {test_id}")
            await check_channel(bot, test_id)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
