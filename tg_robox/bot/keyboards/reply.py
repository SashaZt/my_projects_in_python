# keyboards/reply.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case
from db.models import CardCode
from config.config import Config

# Создаем router для обработчиков в этом файле
router = Router()

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    config = Config.load()
    return user_id in config.bot.admin_ids


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
            KeyboardButton(text="📊 Відгуки"),        # Перемещено сюда вместо "Контактна інформація"
            KeyboardButton(text="🛟 Підтримка / FAQ"),
        ],
        # Убрана отдельная строка с "📊 Відгуки"
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для администратора"""
    builder = ReplyKeyboardBuilder()

    # Первый ряд - Админские кнопки
    builder.row(
        KeyboardButton(text="➕ Додати код"), 
        KeyboardButton(text="📊 Статистика")
    )

    # Второй ряд
    builder.row(
        KeyboardButton(text="🗝 Залишок ключів"),  # Обновленная кнопка
        KeyboardButton(text="🎁 Розіграш / Бонуси"),
    )

    # Третий ряд
    builder.add(KeyboardButton(text="👨‍💻 Режим користувача"))

    return builder.as_markup(resize_keyboard=True)


# ОБРАБОТЧИК КНОПКИ - ПЕРЕНЕСЕН В ПРАВИЛЬНОЕ МЕСТО
@router.message(F.text == "🗝 Залишок ключів")
async def rest_keys_button(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик кнопки остатков ключей из reply клавиатуры"""
    if not is_admin(message.from_user.id):
        return
    
    # Получаем информацию об остатках ключей по номиналам
    stmt = (
        select(
            CardCode.card_value,
            func.count(CardCode.code_id).label('total_count'),
            func.sum(case((CardCode.is_used == False, 1), else_=0)).label('available_count'),
            func.sum(case((CardCode.is_used == True, 1), else_=0)).label('used_count')
        )
        .group_by(CardCode.card_value)
        .order_by(CardCode.card_value)
    )
    
    result = await session.execute(stmt)
    card_stats = result.fetchall()
    
    # Формируем сообщение
    message_text = "🗝 <b>Залишок ключів за номіналами</b>\n\n"
    
    if card_stats:
        total_available = 0
        total_used = 0
        total_all = 0
        
        for stat in card_stats:
            card_value = float(stat.card_value)
            total_count = stat.total_count or 0
            available_count = stat.available_count or 0
            used_count = stat.used_count or 0
            
            total_available += available_count
            total_used += used_count
            total_all += total_count
            
            message_text += (
                f"💵 <b>${card_value:.0f}</b>: "
                f"<b>{available_count}</b> доступно / {total_count} всього\n"
            )
        
        message_text += f"\n📊 <b>Загальна статистика ключів:</b>\n"
        message_text += f"✅ Доступно: <b>{total_available}</b>\n"
        message_text += f"❌ Використано: {total_used}\n"
        message_text += f"📦 Всього: {total_all}\n"
    else:
        message_text += "❌ Ключів в базі немає\n"
    
    await message.answer(message_text)