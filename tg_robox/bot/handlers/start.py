# /handles/start.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from handlers.admin import is_admin, AdminStates
from sqlalchemy import func
from aiogram.types import Message, CallbackQuery
import sys
from pathlib import Path
from keyboards import inline as ikb
from db.models import User
from keyboards import reply as kb
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from db.models import Order, CardCode


router = Router()

# Добавляем корневую директорию в PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.config import Config
from config.logger import logger


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик команды /start"""
    # Проверяем, является ли пользователь администратором
    config = Config.load()
    is_admin = message.from_user.id in config.bot.admin_ids

    # Получаем или создаем пользователя
    user = await get_or_create_user(session, message.from_user)

    # Отправляем приветственное сообщение
    welcome_text = (
        f"👋 <b>Привіт, {message.from_user.first_name}!</b> 😊\n\n"
        f"Я — твій помічник для швидкої покупки Roblox-карток.\n"
        f"Тут ти можеш легко обрати потрібний номінал, оплатити й миттєво отримати код.👾\n"
        f"Готовий почати? Обери дію нижче! 👇\n\n"
    )

    if is_admin:
        welcome_text += (
            "<i>Ви адміністратор. Використовуйте спеціальну клавіатуру нижче:</i>"
        )
        # Используем клавиатуру для админа
        keyboard = kb.get_admin_keyboard()
    else:
        # welcome_text += "<i>Виберіть опцію з меню нижче:</i>"
        # Используем клавиатуру для обычного пользователя
        keyboard = kb.get_main_menu_keyboard()

    await message.answer(welcome_text, reply_markup=keyboard)

    # Сбрасываем состояние FSM
    await state.clear()


@router.callback_query(F.data == "admin_panel")
async def admin_panel_button(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки Адмін-панель"""
    # Проверяем, является ли пользователь администратором
    config = Config.load()
    if callback.from_user.id not in config.bot.admin_ids:
        await callback.answer(
            "⛔ У вас недостаточно прав для использования этой функции.",
            show_alert=True,
        )
        return

    # Показываем админ-панель
    await callback.message.edit_text(
        "🛠 <b>Адмін-панель</b>\n\n" "Виберіть дію:",
        reply_markup=ikb.get_admin_main_keyboard(),
    )
    await state.set_state(AdminStates.main_menu)
    await callback.answer()


@router.callback_query(F.data == "user_mode")
async def switch_to_user_mode(callback: CallbackQuery, state: FSMContext):
    """Переключение на режим пользователя для админа"""
    await callback.message.edit_text(
        "👤 <b>Режим користувача</b>\n\n"
        "Ви перейшли в режим звичайного користувача. "
        "Виберіть опцію з меню нижче:",
        reply_markup=ikb.get_main_menu_keyboard(),
    )
    await callback.answer("Ви перейшли в режим користувача")


@router.message(F.text == "ℹ️ Як це працює?")
async def how_it_works(message: Message):
    """Обработчик кнопки 'Як це працює?'"""
    await message.answer(
        "ℹ️ <b>Як це працює?:</b>\n\n"
        "❗Для активації коду через офіційний сайт гри, вам потрібно пам'ятати <b>нікнейм та пароль</b> від вашого Roblox акаунту.\n"
        "Активація можлива тільки для <b>українських</b> акаунтів або акаунтів <b>з валютою магазину долар.</b>❗\n\n"
        "1. Обираєш Roblox-картку\n"
        "Наприклад: 10$, 20$ чи 50$\n"
        "2. Оплачуєш покупку\n"
        "Через зручну систему або карткою\n"
        "3. Отримуєш код миттєво\n"
        "Бот надсилає тобі унікальний код та інструкцію прямо в чат\n"
        "<b>В комплекті до коду буде відео та текстова інструкція для успішної активації!</b>\n"
        "4. Активуєш на сайті. "
        "Переходиш на roblox.com/redeem (це офіційний сайт гри Roblox ), вводиш код — і отримуєш свої Robux!\n\n"
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


# Обработчик кнопки "Додати код" из клавиатуры
@router.message(F.text == "➕ Додати код")
async def add_code_button(message: Message, state: FSMContext):
    """Обработчик кнопки добавления кода"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "➕ <b>Додавання кодів</b>\n\n" "Виберіть спосіб додавання кодів:",
        reply_markup=ikb.get_admin_add_code_keyboard(),
    )
    await state.set_state(AdminStates.add_code_menu)


# Обработчик кнопки "Статистика" из клавиатуры
@router.message(F.text == "📊 Статистика")
async def stats_button(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик кнопки статистики"""
    if not is_admin(message.from_user.id):
        return

    # Считаем статистику
    orders_count = await session.scalar(select(func.count()).select_from(Order))
    users_count = await session.scalar(select(func.count()).select_from(User))
    cards_total = await session.scalar(select(func.count()).select_from(CardCode))
    cards_used = await session.scalar(
        select(func.count()).select_from(CardCode).where(CardCode.is_used == True)
    )

    # Расчет суммы всех платежей
    total_payments = await session.scalar(
        select(func.coalesce(func.sum(Order.price), 0)).where(
            Order.status == "completed"
        )
    )

    # Формируем сообщение со статистикой
    stats_message = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👤 Користувачів: {users_count}\n"
        f"🛍 Замовлень: {orders_count}\n"
        f"💵 Загальна сума оплат: {total_payments:.2f}₴\n\n"
        f"🎮 Картки:\n"
        f"➖ Всього: {cards_total}\n"
        f"➖ Використано: {cards_used}\n"
        f"➖ Доступно: {cards_total - cards_used}\n"
    )

    await message.answer(stats_message)


# Аналогично добавляем обработчики для других кнопок
@router.message(F.text == "👤 Користувачі")
async def users_button(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик кнопки пользователей"""
    if not is_admin(message.from_user.id):
        return

    # [код обработки как в callback_query]


@router.message(F.text == "🎁 Розіграш / Бонуси")
async def promos_button(message: Message, state: FSMContext):
    """Обработчик кнопки промо-акций"""
    if not is_admin(message.from_user.id):
        return

    # [код обработки как в callback_query]


# Обработчик переключения на режим пользователя
@router.message(F.text == "👨‍💻 Режим користувача")
async def user_mode_button(message: Message, state: FSMContext):
    """Переключение на режим пользователя"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "👤 <b>Режим звичайного користувача</b>\n\n"
        "Ви перейшли в режим звичайного користувача.",
        reply_markup=kb.get_main_menu_keyboard(),
    )
