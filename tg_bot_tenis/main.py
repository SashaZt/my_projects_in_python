# main.py - с инициализацией loguru
import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from config.logger import setup_logging, logger
from database.connection import init_database

# Импортируем только нужные обработчики
from handlers import user, admin, group

async def main():
    """Основная функция запуска бота"""
    
    # Настройка логирования ПЕРВЫМ ДЕЛОМ
    setup_logging()
    logger.info("=== Запуск бота ===")
    
    # Создаем директорию для базы данных
    os.makedirs("data", exist_ok=True)
    
    # Инициализируем базу данных
    await init_database()
    
    # Инициализируем бота и диспетчер
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()
    
    # Порядок роутеров:
    dp.include_router(group.router)     # Кнопки в группе (join_event_, leave_event_)
    dp.include_router(admin.router)     # Админская панель (личные сообщения)
    dp.include_router(user.router)      # Справка (личные сообщения)
    
    logger.info("Роутеры подключены, бот запускается...")
    
    # Запускаем бота
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
    finally:
        await bot.session.close()
        logger.info("=== Бот остановлен ===")

if __name__ == "__main__":
    asyncio.run(main())