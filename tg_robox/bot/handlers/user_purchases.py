# from aiogram import Router, F
# from aiogram.types import Message
# from keyboards import reply as kb
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from sqlalchemy.orm import joinedload
# from db.models import Order, Payment, CardCode, RobloxProduct

# router = Router()


# @router.message(F.text == "🛍 Мої покупки")
# async def my_purchases(message: Message, session: AsyncSession):
#     """Обработчик кнопки 'Мої покупки'"""
#     user_id = message.from_user.id

#     # Получаем заказы пользователя
#     stmt = (
#         select(Order)
#         .options(
#             joinedload(Order.product),
#             joinedload(Order.payment),
#             joinedload(Order.card_codes),
#         )
#         .where(Order.user_id == user_id)
#         .order_by(Order.created_at.desc())
#     )

#     result = await session.execute(stmt)
#     orders = result.unique().scalars().all()

#     if not orders:
#         await message.answer(
#             "🛍 <b>Ваші покупки</b>\n\n"
#             "У вас поки немає покупок.\n\n"
#             "Щоб здійснити покупку, поверніться в головне меню і виберіть 'Купити картку'.",
#             reply_markup=kb.get_main_menu_keyboard(),
#         )
#         return

#     # Формируем сообщение с покупками
#     purchases_text = "🛍 <b>Ваші покупки</b>\n\n"

#     for order in orders:
#         status_emoji = {
#             "created": "🕒",
#             "paid": "✅",
#             "completed": "✅",
#             "canceled": "❌",
#         }.get(order.status, "❓")

#         # Форматируем дату в читаемый вид
#         date_str = order.created_at.strftime("%d.%m.%Y %H:%M")

#         # Добавляем основную информацию о заказе
#         purchases_text += (
#             f"{status_emoji} <b>Замовлення #{order.order_id}</b>\n" f"📅 {date_str}\n"
#         )

#         # Добавляем информацию о продукте, если она есть
#         if order.product:
#             purchases_text += (
#                 f"🎮 {order.product.name}\n"
#                 f"💰 Robux: {order.product.robux_amount}\n"
#                 f"💵 Ціна: {order.total_price}₴\n"
#             )

#         # Добавляем статус заказа
#         purchases_text += f"📊 Статус: {get_status_text(order.status)}\n"

#         # Если заказ оплачен или завершен, показываем коды карт
#         if order.status in ["paid", "completed"] and order.card_codes:
#             purchases_text += f"🔑 Коди карток:\n"
#             for code in order.card_codes:
#                 purchases_text += f"<code>{code.code}</code>\n"

#         purchases_text += "\n"

#     await message.answer(purchases_text, reply_markup=kb.get_main_menu_keyboard())


# def get_status_text(status: str) -> str:
#     """Возвращает текст статуса на украинском языке"""
#     status_texts = {
#         "created": "Створено",
#         "paid": "Оплачено",
#         "completed": "Завершено",
#         "canceled": "Скасовано",
#     }
#     return status_texts.get(status, status)
# В handlers/user_purchases.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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

router = Router()


class PurchasesStates(StatesGroup):
    viewing = State()


@router.message(F.text == "🛍 Мої покупки")
async def my_purchases(message: Message, session: AsyncSession, state: FSMContext):
    """Обработчик кнопки 'Мої покупки'"""
    # Начинаем с первой страницы
    await show_purchases_page(message, session, state, 0)
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
):
    """Показывает страницу с завершенными покупками пользователя"""
    user_id = message.chat.id if is_callback else message.from_user.id
    per_page = 5  # Количество покупок на странице

    # Получаем общее количество ЗАВЕРШЕННЫХ заказов пользователя
    # Получаем общее количество ЗАВЕРШЕННЫХ заказов пользователя
    total_orders = await session.scalar(
        select(func.count())
        .select_from(Order)
        .where(Order.user_id == user_id, Order.status == "completed")
    )

    if total_orders == 0:
        text = (
            "🛍 <b>Ваші покупки</b>\n\n"
            "У вас поки немає завершених покупок.\n\n"
            "Щоб здійснити покупку, поверніться в головне меню і виберіть 'Купити картку'."
        )

        if is_callback:
            await message.edit_text(text, reply_markup=kb.get_main_menu_keyboard())
        else:
            await message.answer(text, reply_markup=kb.get_main_menu_keyboard())
        return

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
            Order.status == "completed",  # Фильтр только по завершенным заказам
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

    # Создаем и отправляем сообщение с пагинацией
    if is_callback:
        try:
            await message.edit_text(
                purchases_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            )
        except Exception as e:
            # Если сообщение слишком длинное, отправляем новое
            await message.answer(
                purchases_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            )
    else:
        await message.answer(
            purchases_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )


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
