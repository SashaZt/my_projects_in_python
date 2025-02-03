from aiogram import F, types
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from config import logger
from database import fetch_pending_messages
from main import dp
from messages import get_and_forward_messages


# 🔹 Главное меню
async def main_menu():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📩 Переслать Materials Pro → Free",
                    callback_data="send_materials",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📩 Переслать Models Pro → Free", callback_data="send_models"
                )
            ],
        ]
    )
    return keyboard


# 🔹 Обработчик команды /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("⏳ Обновляем список сообщений...")
    await fetch_and_save_messages()  # Обновляем список ID
    keyboard = await main_menu()
    await message.answer(
        "✅ Данные обновлены! Выберите действие:", reply_markup=keyboard
    )


# 🔹 Запрос количества сообщений перед пересылкой
@dp.callback_query(F.data.in_(["send_materials", "send_models"]))
async def ask_for_limit(callback_query: CallbackQuery):
    """Запрашивает у пользователя количество сообщений для пересылки."""
    await callback_query.answer()
    category = (
        "materials_pro" if callback_query.data == "send_materials" else "models_pro"
    )
    await callback_query.message.answer(
        f"📩 Сколько сообщений переслать из {category.replace('_', ' ')}? (Введите число)"
    )
    dp.callback_query_data = {"category": category}


# 🔹 Обработчик ввода количества сообщений
@dp.message(F.text.regexp(r"^\d+$"))  # Разрешаем ввод только чисел
async def process_limit_input(message: types.Message):
    """Принимает число от пользователя и запускает пересылку сообщений."""
    limit = int(message.text)

    if limit <= 0:
        await message.answer("❌ Введите число больше 0.")
        return

    category = dp.callback_query_data.get("category", "materials_pro")
    await message.answer(
        f"⏳ Начинаем пересылку {limit} сообщений из {category.replace('_', ' ')}..."
    )

    # Запускаем пересылку сообщений
    await get_and_forward_messages(category, limit)

    await message.answer(f"✅ Переслано {limit} сообщений!")
