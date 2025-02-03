import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN_REPOST, logger

# 🔹 Создаем экземпляр бота
bot = Bot(token=BOT_TOKEN_REPOST)
dp = Dispatcher()


# 🔹 Функция запуска бота
async def start_bot():
    logger.info("✅ Бот запущен!")
    await bot.set_my_commands(
        [
            BotCommand(command="/start", description="Запустить бота"),
        ]
    )
    await dp.start_polling(bot)
