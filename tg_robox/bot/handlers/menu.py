# bot/handlers/menu.py
from aiogram import Router, F
from aiogram.types import Message
from keyboards import reply as kb

router = Router()


@router.message(F.text == "📋 Головне меню")
async def main_menu(message: Message):
    """Обработчик кнопки 'Головне меню'"""
    await message.answer(
        "📋 <b>Головне меню</b>\n\n" "Виберіть потрібний розділ:",
        reply_markup=kb.get_main_menu_keyboard(),
    )


@router.message(F.text == "🎁 Розіграш / Бонуси")
async def bonuses(message: Message):
    """Обработчик кнопки 'Розіграш / Бонуси'"""
    await message.answer(
        "🎁 <b>Розіграш / Бонуси</b>\n\n"
        "В данный момент активных акций нет.\n"
        "Следите за обновлениями в нашем канале: @channel_name",
        reply_markup=kb.get_main_menu_keyboard(),
    )
