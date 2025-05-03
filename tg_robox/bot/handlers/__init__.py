from aiogram import Dispatcher
from . import start, buy, support, user_purchases, info


def register_all_handlers(dp: Dispatcher, config):
    """Регистрация всех обработчиков"""
    # Добавляем все роутеры
    dp.include_router(start.router)
    dp.include_router(buy.router)
    dp.include_router(support.router)
    dp.include_router(user_purchases.router)
    dp.include_router(info.router)
