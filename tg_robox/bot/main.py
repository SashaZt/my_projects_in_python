import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from config.config import Config
from config.logger import logger
from db.database import create_async_engine, get_session_maker, init_models
from middlewares import setup_middlewares
from aiogram.client.default import DefaultBotProperties
from handlers import register_all_handlers


# Команды бота для меню
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Підтримка"),
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

    # Настройка middlewares
    setup_middlewares(dp, session_maker, config)

    register_all_handlers(dp, config)

    # Установка команд бота
    await set_commands(bot)

    # Запуск бота
    try:
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
