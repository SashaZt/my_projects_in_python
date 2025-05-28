# В файле обработчика поддержки

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards import reply as kb
from keyboards import inline as ikb  # Добавить импорт inline клавиатур
from config.logger import logger
from config.config import Config
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import User
from sqlalchemy.future import select
from datetime import datetime
import os

router = Router()

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    config = Config.load()
    return user_id in config.bot.admin_ids

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

@router.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help - перенаправляет на FAQ"""
    # Вызываем функцию FAQ/Поддержка
    await faq_support(message)

@router.message(Command("menu"))
async def menu_command(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик команды /menu - работает как /start"""
    
    # Получаем или создаем пользователя (как в start.py)
    user = await get_or_create_user(session, message.from_user)
    
    # Проверяем права администратора
    user_is_admin = is_admin(message.from_user.id)

    # Отправляем приветственное сообщение (как в /start)
    welcome_text = (
        f"👋 <b>Привіт, {message.from_user.first_name}!</b> 😊\n\n"
        f"Я — твій помічник для швидкої покупки Roblox-карток.\n"
        f"Тут ти можеш легко обрати потрібний номінал, оплатити й миттєво отримати код.👾\n"
        f"Готовий почати? Обери дію нижче! 👇\n\n"
    )

    if user_is_admin:
        welcome_text += (
            "<i>Ви адміністратор. Використовуйте спеціальну клавіатуру нижче:</i>"
        )
        # Используем клавиатуру для админа
        keyboard = kb.get_admin_keyboard()
    else:
        # Используем клавиатуру для обычного пользователя
        keyboard = kb.get_main_menu_keyboard()

    await message.answer(welcome_text, reply_markup=keyboard)

    # Сбрасываем состояние FSM
    await state.clear()

@router.message(F.text == "🛟 Підтримка / FAQ")
async def faq_support(message: Message):
    # Определяем путь к фото
    photo_path = "assets/images/Підтримка.png"
    
    # Текст подписи к фото
    caption = (
        "<b>Підтримка</b>\n\n"
        "Маєш питання чи щось не працює? Ми на зв'язку❗\n"
        "Напиши нам у підтримку: @gamersq_q\n\n"
        "Перед зверненням переглянь поширені запитання нижче — можливо, відповідь уже тут:\n\n"
        "<b>Часті питання (FAQ):</b>\n"
        "1. <b>Як отримати код після оплати?</b>\n"
        "Після підтвердження оплати бот автоматично надішле код у чат.\n\n"
        "2. <b>Як активувати код Roblox?</b>\n"
        "Перейди на roblox.com/redeem, увійди до свого акаунту, введи код та натисни Redeem.\n\n"
        "Ти також можеш переглянути відео інструкцію https://youtu.be/6r9qPBOOzHk\n\n"
        "3. <b>Я не пам'ятаю пароль від акаунту Roblox що робити</b> ???\n"
        "Ти можеш відновити його за допомогою електронної пошти. Додавши її до свого акаунту.\n"
        "Переглянь відео інструкцію  https://youtu.be/KL53OvuBx9Y\n\n"
        "4. <b>Що робити, якщо код не працює?</b>\n"
        "Переконайся, що ти не припустився помилки. Якщо код все одно не працює — звернись у підтримку.\n\n"
        "5. <b>Скільки часу чекати код після оплати?</b>\n"
        "Зазвичай код приходить миттєво. Якщо затримка — напиши в підтримку."
    )
    
    try:
        # Проверяем существование файла фото
        if os.path.exists(photo_path):
            # Отправляем фото с подписью и клавиатурой
            photo = FSInputFile(photo_path)
            await message.answer_photo(
                photo=photo,
                caption=caption,
                parse_mode="HTML",
                reply_markup=ikb.get_offer_agreement_keyboard(),
            )
        else:
            # Если фото не найдено, отправляем только текст
            logger.warning(f"Изображение не найдено: {photo_path}")
            await message.answer(
                caption,
                parse_mode="HTML",
                reply_markup=ikb.get_offer_agreement_keyboard(),
            )
            
    except Exception as e:
        logger.error(f"Ошибка при отправке изображения: {e}")
        # В случае ошибки отправляем только текст
        await message.answer(
            caption,
            parse_mode="HTML",
            reply_markup=ikb.get_offer_agreement_keyboard(),
        )

# Обработчик callback для возврата в главное меню
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu_from_support(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' к главному меню"""
    # Определяем, является ли пользователь админом
    user_is_admin = is_admin(callback.from_user.id)
    
    await callback.message.edit_text(
        "📋 <b>Головне меню</b>\n\n" 
        "Виберіть потрібний розділ:",
        reply_markup=ikb.get_main_menu_keyboard(is_admin=user_is_admin),
        parse_mode="HTML"
    )
    await callback.answer()

# Обработчик callback для поддержки (если нужен)
@router.callback_query(F.data == "support")
async def support_callback(callback: CallbackQuery):
    """Обработчик inline кнопки поддержки"""
    await callback.message.edit_text(
        "<b>Підтримка</b>\n\n"
        "Маєш питання чи щось не працює? Ми на зв'язку❗\n"
        "Напиши нам у підтримку: @gamersq_q\n\n"
        "Перед зверненням переглянь поширені запитання нижче — можливо, відповідь уже тут:\n\n"
        "<b>Часті питання (FAQ):</b>\n"
        "1. <b>Як отримати код після оплати?</b>\n"
        "Після підтвердження оплати бот автоматично надішле код у чат.\n\n"
        "2. <b>Як активувати код Roblox?</b>\n"
        "Перейди на roblox.com/redeem, увійди до свого акаунту, введи код та натисни Redeem.\n\n"
        "Ти також можеш переглянути відео інструкцію https://youtu.be/6r9qPBOOzHk\n\n"
        "3. <b>Я не пам'ятаю пароль від акаунту Roblox що робити</b> ???\n"
        "Ти можеш відновити його за допомогою електронної пошти. Додавши її до свого акаунту.\n"
        "Переглянь відео інструкцію  https://youtu.be/KL53OvuBx9Y\n\n"
        "4. <b>Що робити, якщо код не працює?</b>\n"
        "Переконайся, що ти не припустився помилки. Якщо код все одно не працює — звернись у підтримку.\n\n"
        "5. <b>Скільки часу чекати код після оплати?</b>\n"
        "Зазвичай код приходить миттєво. Якщо затримка — напиши в підтримку.",
        parse_mode="HTML",
        reply_markup=ikb.get_offer_agreement_keyboard(),
    )
    await callback.answer()

@router.callback_query(F.data == "get_offer_pdf")
async def send_offer_agreement(callback: CallbackQuery):
    """Обработчик кнопки для отправки PDF с офертой"""
    pdf_path = "assets/documents/offer_agreement.pdf"

    try:
        if os.path.exists(pdf_path):
            await callback.message.answer_document(
                document=FSInputFile(pdf_path),
                caption="📄 Оферта публічного договору на продаж карт поповнення Roblox.",
            )
            await callback.answer("Документ відправлено!")
        else:
            logger.error(f"Файл не найден: {pdf_path}")
            await callback.answer("На жаль, файл оферти не знайдено.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при отправке PDF: {e}")
        await callback.answer("На жаль, сталася помилка при відправці документу.", show_alert=True)