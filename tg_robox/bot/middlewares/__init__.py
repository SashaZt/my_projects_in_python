# bot/middlewares/__init__.py
# Сначала импортируем модуль путей
from utils.paths import setup_paths
from config.logger import logger

# setup_paths()

# # Теперь можем использовать абсолютные импорты
# from logger import logger


from aiogram import Dispatcher
from .database import DatabaseMiddleware
from .throttling import ThrottlingMiddleware


def setup_middlewares(dp: Dispatcher, session_pool, config):
    """Настройка всех middlewares"""
    dp.update.middleware(DatabaseMiddleware(session_pool))
    dp.message.middleware(ThrottlingMiddleware(rate_limit=0.5))
    logger.info("Middlewares successfully configured")
