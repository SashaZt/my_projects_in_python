from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Последние 7 дней", callback_data="last_7_days"
                )
            ],
            [InlineKeyboardButton(text="Вчера", callback_data="yesterday")],
            [InlineKeyboardButton(text="Выбрать даты", callback_data="custom_date")],
        ]
    )
