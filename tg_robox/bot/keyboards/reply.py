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
    keyboard = [
        [KeyboardButton(text="🛍 Купити картку")],
        [KeyboardButton(text="🛍 Мої покупки"), KeyboardButton(text="ℹ️ Як це працює?")],
        [
            KeyboardButton(text="📞 Контактна інформація"),
            KeyboardButton(text="🛟 Підтримка / FAQ"),
        ],
        [KeyboardButton(text="📊 Відгуки")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для администратора"""
    builder = ReplyKeyboardBuilder()

    # Первый ряд - Админские кнопки
    builder.row(
        KeyboardButton(text="➕ Додати код"), KeyboardButton(text="📊 Статистика")
    )

    # Второй ряд
    builder.row(
        KeyboardButton(text="👤 Користувачі"),
        KeyboardButton(text="🎁 Розіграш / Бонуси"),
    )

    # Третий ряд
    builder.add(KeyboardButton(text="👨‍💻 Режим користувача"))

    return builder.as_markup(resize_keyboard=True)
