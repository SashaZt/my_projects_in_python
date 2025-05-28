# handlers / __init__.py
from aiogram import Dispatcher

from . import admin, buy, info, payments, reviews, start, support, user_purchases


def register_all_handlers(dp: Dispatcher, config):
    """Регистрация всех обработчиков"""
    # Добавляем все роутеры
    dp.include_router(start.router)      # Команды /start
    dp.include_router(support.router)    # Команды /help, /menu и поддержка
    dp.include_router(buy.router)
    dp.include_router(user_purchases.router)
    dp.include_router(info.router)
    dp.include_router(payments.router)
    dp.include_router(admin.router)
    dp.include_router(reviews.router)
