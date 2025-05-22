import asyncio
import importlib

import keyboards.inline
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config.logger import logger
from db.database import create_async_engine, get_session_maker, init_models
from handlers import register_all_handlers
from middlewares import setup_middlewares
from scheduled_tasks import publish_approved_reviews

from config.config import Config

# Перезагрузка модуля клавиатур
importlib.reload(keyboards.inline)


# Команды бота для меню
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Підтримка / FAQ"),
        BotCommand(command="menu", description="Головне меню"),
    ]
    await bot.set_my_commands(commands)


async def main():
    # Загрузка конфигурации
    config = Config.load()

    # Проверка конфигурации
    if not config.bot.token:
        logger.error("Токен бота не указан в конфигурации!")
        return

    # Инициализация бота и диспетчера
    bot = Bot(
        token=config.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Настройка базы данных
    engine = create_async_engine(config.db)
    session_maker = get_session_maker(engine)

    # Инициализация моделей
    await init_models(engine)

    # # Инициализация планировщика
    # scheduler = AsyncIOScheduler()
    # # Добавление задачи по расписанию (например, каждый час)
    # scheduler.add_job(publish_approved_reviews, "interval", hours=1, args=[bot])

    # # Запуск планировщика
    # scheduler.start()

    # Настройка middlewares
    setup_middlewares(dp, session_maker, config)

    register_all_handlers(dp, config)

    # Установка команд бота
    await set_commands(bot)

    # Запуск бота
    try:
        if config.monobank.webhook_url:
            # Настройка веб-сервера для приема вебхуков
            from aiohttp import web
            from handlers.webhook import monobank_webhook_handler

            # Создаем приложение aiohttp
            app = web.Application()

            # Добавляем маршрут для вебхука Monobank
            # Предположим, что webhook_url имеет вид https://yourdomain.com/webhooks/monobank
            # В этом случае путь будет "/webhooks/monobank"
            webhook_path = config.monobank.webhook_url.split("/")[-1]
            app.router.add_post(f"/{webhook_path}", monobank_webhook_handler)

            # Запускаем веб-сервер в отдельном таске
            runner = web.AppRunner(app)
            await runner.setup()

            # Извлекаем порт из конфигурации или используем порт по умолчанию
            webhook_port = (
                config.monobank.webhook_port
                if hasattr(config.monobank, "webhook_port")
                else 8080
            )
            site = web.TCPSite(runner, "0.0.0.0", webhook_port)

            # Запускаем сайт
            await site.start()
            logger.info(f"Веб-сервер для вебхуков запущен на порту {webhook_port}")
        logger.info(
            f"Бот запущен (Проект: {config.project_name}, "
            f"Версия: {config.version}, Окружение: {config.environment})"
        )

        # Вывод информации о конфигурации
        logger.info(f"Часовой пояс: {config.timezone}")
        logger.info(
            f"URL базы данных: postgresql://{config.db.user}:****@{config.db.host}:{config.db.port}/{config.db.database}"
        )

        # Вывод списка админов, если они есть
        if config.bot.admin_ids:
            admin_ids_str = ", ".join(
                str(admin_id) for admin_id in config.bot.admin_ids
            )
            logger.info(f"Администраторы: {admin_ids_str}")
        else:
            logger.warning("Не задан ни один администратор!")

        # Удаление ожидающих обновлений и запуск поллинга
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка при запуске бота: {e}")
    finally:
        # Закрытие соединений
        if hasattr(bot, "session") and bot.session:
            await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен по команде пользователя")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        import traceback

        logger.critical(traceback.format_exc())
