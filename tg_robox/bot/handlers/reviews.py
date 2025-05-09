# handlers/reviews.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import Review, Order
from keyboards import inline as ikb
from keyboards import reply as kb
from utils.states import ReviewStates
from config.logger import logger
from aiogram.types import InlineKeyboardButton
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy import func
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


class ReviewsStates(StatesGroup):
    viewing = State()


@router.callback_query(F.data.startswith("review_"))
async def start_review(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Начало процесса оставления отзыва"""
    # Получаем ID заказа из callback_data
    order_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    # Проверяем, не оставлял ли пользователь уже отзыв для этого заказа
    stmt = select(Review).where(Review.order_id == order_id, Review.user_id == user_id)
    result = await session.execute(stmt)
    existing_review = result.scalar_one_or_none()

    if existing_review:
        await callback.answer(
            "Ви вже залишили відгук для цього замовлення!", show_alert=True
        )
        return

    # Сохраняем ID заказа в состоянии
    await state.update_data(order_id=order_id)

    # Отправляем запрос на оценку
    await callback.message.answer(
        "⭐ <b>Оцініть наш сервіс</b>\n\n"
        "Будь ласка, оцініть якість нашого сервісу від 1 до 5 зірок:",
        reply_markup=ikb.get_rating_keyboard(),
    )

    # Устанавливаем состояние ожидания оценки
    await state.set_state(ReviewStates.waiting_rating)
    await callback.answer()


# Обработчик выбора оценки
@router.callback_query(ReviewStates.waiting_rating, F.data.startswith("rating_"))
async def process_rating(callback: CallbackQuery, state: FSMContext):
    """Обработка выбранной оценки"""
    # Получаем оценку из callback_data
    rating = int(callback.data.split("_")[1])

    # Сохраняем оценку в состоянии
    await state.update_data(rating=rating)

    # Запрашиваем комментарий
    await callback.message.answer(
        f"Дякуємо за оцінку! {'⭐' * rating}\n\n"
        "Будь ласка, напишіть короткий коментар або враження про наш сервіс.\n"
        "Це допоможе нам стати кращими!"
    )

    # Устанавливаем состояние ожидания комментария
    await state.set_state(ReviewStates.waiting_comment)
    await callback.answer()


@router.message(ReviewStates.waiting_comment)
async def process_comment(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка комментария и публикация отзыва"""
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        order_id = data.get("order_id")
        rating = data.get("rating")

        logger.info(
            f"Получены данные отзыва: user_id={message.from_user.id}, order_id={order_id}, rating={rating}, comment={message.text}"
        )

        # Получаем комментарий из сообщения
        comment = message.text

        # Получаем информацию о заказе
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            logger.error(f"Заказ не найден: order_id={order_id}")
            await message.answer(
                "❌ На жаль, сталася помилка при збереженні відгуку - замовлення не знайдено.",
                reply_markup=kb.get_main_menu_keyboard(),
            )
            await state.clear()
            return

        try:
            # Создаем новый отзыв
            review = Review(
                order_id=order_id,
                user_id=message.from_user.id,
                rating=rating,
                comment=comment,
                is_approved=True,
                is_published=True,  # Изначально не опубликован
                created_at=datetime.now(),  # Явно задаем дату создания
            )

            logger.info(f"Создан объект отзыва: {review.__dict__}")

            # Добавляем отзыв в БД
            session.add(review)
            await session.flush()  # Сначала flush для получения ID

            logger.info(f"Отзыв получил ID: {review.review_id}")

            # Фиксируем изменения в БД
            await session.commit()

            logger.info(f"Отзыв успешно сохранен в БД")
        except Exception as db_error:
            logger.error(f"Ошибка при сохранении в БД: {db_error}", exc_info=True)
            await message.answer(
                "❌ На жаль, сталася помилка при збереженні відгуку в базу даних.",
                reply_markup=kb.get_main_menu_keyboard(),
            )
            await state.clear()
            return

        # Публикуем отзыв в группу напрямую
        try:
            group_id = "-4763327238"  # ID группы с отзывами
            user_name = message.from_user.first_name or "Користувач"
            if message.from_user.last_name:
                user_name += f" {message.from_user.last_name}"

            review_text = (
                f"📝 <b>Новий відгук від клієнта</b>\n\n"
                f"👤 {user_name}\n"
                f"⭐ {'⭐' * int(rating)}\n\n"
                f"💬 {comment}\n\n"
                f"📅 {review.created_at.strftime('%d.%m.%Y')}"
            )

            logger.info(f"Попытка отправки отзыва в группу {group_id}")

            # Отправляем отзыв в группу
            sent_message = await message.bot.send_message(
                chat_id=group_id, text=review_text, parse_mode="HTML"
            )

            logger.info(
                f"Отзыв успешно отправлен в группу, message_id={sent_message.message_id}"
            )

            # Отмечаем отзыв как опубликованный
            review.is_published = True
            await session.commit()
            logger.info(f"Отзыв отмечен как опубликованный")

        except Exception as publish_error:
            logger.error(
                f"Ошибка при публикации отзыва в группе: {publish_error}", exc_info=True
            )
            # Продолжаем выполнение, так как отзыв уже сохранен в БД

        # Благодарим пользователя
        await message.answer(
            f"✅ <b>Дякуємо за ваш відгук!</b>\n\n"
            f"Ваша оцінка: {'⭐' * rating}\n\n"
            f"Ми цінуємо ваш час та допомогу у вдосконаленні нашого сервісу. "
            f"Сподіваємося бачити вас знову!",
            reply_markup=kb.get_main_menu_keyboard(),
        )

        # Очищаем состояние
        await state.clear()

    except Exception as e:
        logger.error(f"Общая ошибка при обработке отзыва: {e}", exc_info=True)
        await message.answer(
            "❌ На жаль, сталася помилка при збереженні відгуку. Спробуйте пізніше.",
            reply_markup=kb.get_main_menu_keyboard(),
        )
        await state.clear()


# Обработчик отмены отзыва
@router.callback_query(F.data == "cancel_review")
async def cancel_review(callback: CallbackQuery, state: FSMContext):
    """Отмена оставления отзыва"""
    await callback.message.answer(
        "✅ Ви можете залишити відгук пізніше через наш бот або групу.",
        reply_markup=kb.get_main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer()


# @router.message(F.text == "📊 Відгуки")
# async def view_reviews(message: Message, session: AsyncSession):
#     """Просмотр отзывов"""
#     # Получаем последние 5 отзывов
#     stmt = (
#         select(Review)
#         .options(joinedload(Review.user))
#         .order_by(Review.created_at.desc())
#         .limit(5)
#     )
#     result = await session.execute(stmt)
#     reviews = result.scalars().all()

#     if not reviews:
#         await message.answer(
#             "📊 <b>Відгуки користувачів</b>\n\n"
#             "У нас поки немає відгуків. Будьте першим, хто залишить свою думку!",
#             reply_markup=kb.get_main_menu_keyboard(),
#         )
#         return

#     # Формируем сообщение с отзывами
#     reviews_text = "📊 <b>Відгуки користувачів</b>\n\n"

#     for review in reviews:
#         user_name = review.user.first_name or "Користувач"
#         reviews_text += (
#             f"👤 {user_name}\n"
#             f"{'⭐️' * review.rating}\n"
#             f"💬 {review.comment}\n"
#             f"📅 {review.created_at.strftime('%d.%m.%Y')}\n\n"
#         )


#     await message.answer(reviews_text, reply_markup=kb.get_main_menu_keyboard())
@router.message(F.text == "📊 Відгуки")
async def view_reviews(message: Message, session: AsyncSession, state: FSMContext):
    """Просмотр отзывов с пагинацией"""
    # Начинаем с первой страницы
    await show_reviews_page(message, session, state, 0)
    await state.set_state(ReviewsStates.viewing)


@router.callback_query(ReviewsStates.viewing, F.data.startswith("reviews_page_"))
async def process_reviews_page(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
):
    """Обработчик пагинации отзывов"""
    # Получаем номер страницы из callback_data
    page = int(callback.data.split("_")[-1])

    await show_reviews_page(callback.message, session, state, page, is_callback=True)
    await callback.answer()


async def show_reviews_page(
    message,
    session: AsyncSession,
    state: FSMContext,
    page: int,
    is_callback: bool = False,
):
    """Показывает страницу с отзывами пользователей"""
    per_page = 5  # Количество отзывов на странице

    # Получаем общее количество отзывов
    total_reviews = await session.scalar(
        select(func.count()).select_from(Review).where(Review.is_approved == True)
    )

    if total_reviews == 0:
        text = (
            "📊 <b>Відгуки користувачів</b>\n\n"
            "У нас поки немає відгуків. Будьте першим, хто залишить свою думку!"
        )

        if is_callback:
            await message.edit_text(text, reply_markup=kb.get_main_menu_keyboard())
        else:
            await message.answer(text, reply_markup=kb.get_main_menu_keyboard())
        return

    # Вычисляем максимальную страницу
    max_page = (total_reviews - 1) // per_page

    # Проверяем, что страница в допустимых пределах
    if page < 0:
        page = 0
    elif page > max_page:
        page = max_page

    # Сохраняем текущую страницу в состоянии
    await state.update_data(current_page=page)

    # Получаем отзывы для текущей страницы
    stmt = (
        select(Review)
        .options(joinedload(Review.user))
        .where(Review.is_approved == True)
        .order_by(Review.created_at.desc())
        .limit(per_page)
        .offset(page * per_page)
    )

    result = await session.execute(stmt)
    reviews = result.scalars().all()

    # Формируем сообщение с отзывами
    reviews_text = (
        f"📊 <b>Відгуки користувачів</b> (сторінка {page+1}/{max_page+1})\n\n"
    )

    for review in reviews:
        user_name = review.user.first_name or "Користувач"
        reviews_text += (
            f"👤 {user_name}\n"
            f"{'⭐️' * review.rating}\n"
            f"💬 {review.comment}\n"
            f"📅 {review.created_at.strftime('%d.%m.%Y')}\n\n"
        )

    # Создаем клавиатуру пагинации
    keyboard = []

    # Кнопки навигации
    nav_buttons = []

    # Кнопка "назад", если это не первая страница
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(text="◀️ Назад", callback_data=f"reviews_page_{page-1}")
        )

    # Кнопка "вперед", если это не последняя страница
    if page < max_page:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶️", callback_data=f"reviews_page_{page+1}"
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
                reviews_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            )
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения: {str(e)}")
            # В случае ошибки отправляем новое сообщение
            await message.answer(
                reviews_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            )
    else:
        await message.answer(
            reviews_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )


# Обработчик для возврата в главное меню, если у вас его еще нет
@router.callback_query(F.data == "back_to_menu")
async def back_to_reviews_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки возврата в главное меню"""
    await callback.message.edit_text(
        "📋 <b>Головне меню</b>\n\n" "Виберіть потрібний розділ:",
        reply_markup=kb.get_main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer()
