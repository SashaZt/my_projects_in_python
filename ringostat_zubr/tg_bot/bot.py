import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import register_handlers

# Логирование
logging.basicConfig(level=logging.INFO)

# Создаем бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регистрируем хэндлеры
register_handlers(dp)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
