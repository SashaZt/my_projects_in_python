from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для команды /start"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="ℹ️ Як це працює?"))
    builder.add(KeyboardButton(text="📋 Головне меню"))

    return builder.as_markup(resize_keyboard=True)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура главного меню"""
    builder = ReplyKeyboardBuilder()

    # Первый ряд - Купити картку
    builder.add(KeyboardButton(text="🛍 Купити картку"))

    # Второй ряд - FAQ и Бонусы
    builder.row(
        KeyboardButton(text="❓ Підтримка"),
        KeyboardButton(text="🎁 Розіграш / Бонуси"),
    )

    # Третий ряд - Мої покупки
    builder.add(KeyboardButton(text="🛍 Мої покупки"))

    return builder.as_markup(resize_keyboard=True)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура главного меню"""
    keyboard = [
        [KeyboardButton(text="🛍 Купити картку")],
        [KeyboardButton(text="🛍 Мої покупки"), KeyboardButton(text="ℹ️ Як це працює?")],
        [
            KeyboardButton(text="📞 Контактна інформація"),
            # KeyboardButton(text="❓ Часті питання"),
        ],
        # [KeyboardButton(text="🛡 Гарантії"), KeyboardButton(text="ℹ️ Про нас")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
