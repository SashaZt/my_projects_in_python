import asyncio

from aiogram import Bot

BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"
CHANNEL_LINK = "https://t.me/+eYaEfrdLoC42N2Qy"


async def get_channel_id():
    bot = Bot(token=BOT_TOKEN)
    try:
        chat = await bot.get_chat(CHANNEL_LINK)
        print(f"Channel ID: {chat.id}")
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(get_channel_id())
