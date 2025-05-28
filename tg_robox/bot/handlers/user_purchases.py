
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
import os
import sys
from pathlib import Path
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import reply as kb
from keyboards import inline as ikb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from sqlalchemy.orm import joinedload
from db.models import Order, Payment, CardCode, RobloxProduct
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Добавляем корневую директорию в PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.logger import logger

router = Router()


class PurchasesStates(StatesGroup):
    viewing = State()


@router.message(F.text == "🛍 Мої покупки")
async def my_purchases(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик кнопки 'Мої покупки'"""
    # Определяем путь к фото
    photo_path = "assets/images/Мої покупки.png"
    
    user_id = message.from_user.id
    per_page = 5

    # Получаем общее количество ЗАВЕРШЕННЫХ заказов пользователя
    total_orders = await session.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.user_id == user_id, Order.status == "completed")
    )

    if total_orders == 0:
        caption = (
            "🛍 <b>Ваші покупки</b>\n\n"
            "У вас поки немає завершених покупок.\n\n"
            "Щоб здійснити покупку, поверніться в головне меню і виберіть 'Купити картку'."
        )
        
        try:
            # Проверяем существование файла фото
            if os.path.exists(photo_path):
                # Отправляем фото с подписью даже если покупок нет
                photo = FSInputFile(photo_path)
                await message.answer_photo(
                    photo=photo,
                    caption=caption,
                    reply_markup=kb.get_main_menu_keyboard(),
                )
            else:
                # Если фото не найдено, отправляем только текст
                logger.warning(f"Изображение не найдено: {photo_path}")
                await message.answer(
                    caption,
                    reply_markup=kb.get_main_menu_keyboard(),
                )
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            # В случае ошибки отправляем только текст
            await message.answer(
                caption,
                reply_markup=kb.get_main_menu_keyboard(),
            )
        return
    # Если есть покупки, показываем первую страницу с фото
    await show_purchases_page(message, session, state, 0, with_photo=True)
    await state.set_state(PurchasesStates.viewing)

@router.callback_query(PurchasesStates.viewing, F.data.startswith("purchases_page_"))
async def process_purchases_page(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
):
    """Обработчик пагинации для покупок"""
    # Получаем номер страницы из callback_data
    page = int(callback.data.split("_")[-1])

    await show_purchases_page(callback.message, session, state, page, is_callback=True)
    await callback.answer()


async def show_purchases_page(
    message,
    session: AsyncSession,
    state: FSMContext,
    page: int,
    is_callback: bool = False,
    with_photo: bool = False,
):
    """Показывает страницу с завершенными покупками пользователя"""
    user_id = message.chat.id if is_callback else message.from_user.id
    per_page = 5  # Количество покупок на странице

    # Получаем общее количество ЗАВЕРШЕННЫХ заказов пользователя
    total_orders = await session.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.user_id == user_id, Order.status == "completed")
    )

    # Вычисляем максимальную страницу
    max_page = (total_orders - 1) // per_page

    # Проверяем, что страница в допустимых пределах
    if page < 0:
        page = 0
    elif page > max_page:
        page = max_page

    # Сохраняем текущую страницу в состоянии
    await state.update_data(current_page=page)

    # Получаем ЗАВЕРШЕННЫЕ заказы пользователя для текущей страницы
    stmt = (
        select(Order)
        .options(
            joinedload(Order.product),
            joinedload(Order.payment),
            joinedload(Order.card_codes),
        )
        .where(
            Order.user_id == user_id,
            Order.status == "completed",
        )
        .order_by(Order.created_at.desc())
        .limit(per_page)
        .offset(page * per_page)
    )

    result = await session.execute(stmt)
    orders = result.unique().scalars().all()

    # Формируем сообщение с покупками
    purchases_text = (
        f"🛍 <b>Ваші завершені покупки</b> (сторінка {page+1}/{max_page+1})\n\n"
    )

    for order in orders:
        # Форматируем дату в читаемый вид
        date_str = order.created_at.strftime("%d.%m.%Y %H:%M")

        # Добавляем основную информацию о заказе
        purchases_text += f"✅ <b>Замовлення #{order.order_id}</b>\n" f"📅 {date_str}\n"

        # Добавляем информацию о продукте, если она есть
        if order.product:
            purchases_text += (
                f"🎮 {order.product.name}\n"
                f"💰 Robux: {order.product.robux_amount}\n"
                f"💵 Ціна: {order.total_price}₴\n"
            )

        # Добавляем коды карт (для завершенных заказов они всегда должны быть)
        if order.card_codes:
            purchases_text += f"🔑 Коди карток:\n"
            for code in order.card_codes:
                purchases_text += f"<code>{code.code}</code>\n"

        purchases_text += "\n"

    # Создаем клавиатуру пагинации
    keyboard = []

    # Кнопки навигации
    nav_buttons = []

    # Кнопка "назад", если это не первая страница
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад", callback_data=f"purchases_page_{page-1}"
            )
        )

    # Кнопка "вперед", если это не последняя страница
    if page < max_page:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶️", callback_data=f"purchases_page_{page+1}"
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Кнопка возврата в главное меню
    keyboard.append(
        [InlineKeyboardButton(text="🔙 Головне меню", callback_data="back_to_menu")]
    )

    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Если это первая страница и нужно отправить с фото
    if with_photo and page == 0:
        photo_path = "assets/images/Мої покупки.png"
        
        try:
            if os.path.exists(photo_path):
                photo = FSInputFile(photo_path)
                await message.answer_photo(
                    photo=photo,
                    caption=purchases_text,
                    reply_markup=reply_markup,
                )
            else:
                logger.warning(f"Изображение не найдено: {photo_path}")
                await message.answer(purchases_text, reply_markup=reply_markup)
        except Exception as e:
            logger.error(f"Ошибка при отправке изображения: {e}")
            await message.answer(purchases_text, reply_markup=reply_markup)
    else:
        # Для остальных страниц или callback'ов отправляем обычный текст
        if is_callback:
            try:
                await message.edit_text(purchases_text, reply_markup=reply_markup)
            except Exception as e:
                # Если сообщение слишком длинное, отправляем новое
                await message.answer(purchases_text, reply_markup=reply_markup)
        else:
            await message.answer(purchases_text, reply_markup=reply_markup)

# Добавьте обработчик для возврата в главное меню, если у вас его еще нет
@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки возврата в главное меню"""
    await callback.message.edit_text(
        "📋 <b>Головне меню</b>\n\n" "Виберіть потрібний розділ:",
        reply_markup=kb.get_main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer()
