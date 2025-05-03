# /handles/start.py
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from db.models import User
from keyboards import reply as kb
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик команды /start"""
    # Сбрасываем состояние FSM
    await state.clear()

    # Сохраняем или обновляем информацию о пользователе
    await get_or_create_user(session, message.from_user)

    await message.answer(
        "Привіт! 😊\n"
        "Я — твій помічник для швидкої покупки Roblox-карток.\n"
        "Тут ти можеш легко обрати потрібний номінал, оплатити й миттєво отримати код.🔥\n"
        "Готовий почати? Обери дію нижче! 👇",
        reply_markup=kb.get_start_keyboard(),
    )


@router.message(F.text == "ℹ️ Як це працює?")
async def how_it_works(message: Message):
    """Обработчик кнопки 'Як це працює?'"""
    await message.answer(
        "ℹ️ <b>Як це працює?:</b>\n\n"
        "1. Обираєш Roblox-картку\n"
        "— Наприклад: 10$, 25$ чи 50$\n"
        "2. Оплачуєш покупку\n"
        "— Через зручну систему або на банківську картку\n"
        "3. Отримуєш код миттєво\n"
        "— Бот надсилає тобі унікальний код прямо в чат\n"
        "4. Активуєш на сайті\n"
        "— Переходиш на roblox.com/redeem, вводиш код — і отримуєш свої Robux!\n\n"
        "Якщо у вас виникли запитання, зверніться до розділу Підтримка.",
        reply_markup=kb.get_main_menu_keyboard(),
    )


@router.message(F.text == "📋 Головне меню")
async def main_menu(message: Message):
    """Обработчик кнопки 'Головне меню'"""
    await message.answer(
        "📋 <b>Головне меню</b>\n\n" "Виберіть потрібний розділ:",
        reply_markup=kb.get_main_menu_keyboard(),
    )


async def get_or_create_user(session: AsyncSession, user_info):
    """Получение или создание пользователя в БД"""
    # Поиск пользователя в БД
    stmt = select(User).where(User.user_id == user_info.id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    now = datetime.now()

    if user:
        # Если пользователь уже есть, обновляем его данные
        user.username = user_info.username
        user.first_name = user_info.first_name
        user.last_name = user_info.last_name
        user.language_code = user_info.language_code
        user.last_activity = now
    else:
        # Если пользователя нет, создаем нового
        user = User(
            user_id=user_info.id,
            username=user_info.username,
            first_name=user_info.first_name,
            last_name=user_info.last_name,
            language_code=user_info.language_code,
            last_activity=now,
        )
        session.add(user)

    # Сохраняем изменения
    await session.commit()
    return user
