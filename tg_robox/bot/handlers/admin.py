# Стандартная библиотека Python
import csv
from datetime import datetime

# SQLAlchemy
from sqlalchemy import func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

# Aiogram
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# Локальные модули
from config.config import Config
from config.logger import logger
from db.models import CardCode, Order, User, Review
from keyboards import inline as ikb
router = Router()


# Определяем состояния для FSM
class AdminStates(StatesGroup):
    main_menu = State()
    add_code_menu = State()
    add_code_manually = State()
    add_code_value = State()
    add_code_file = State()
    add_code_confirm = State()
    reviews_menu = State()


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    config = Config.load()
    # Добавим отладочный вывод
    print(f"Admin check: user_id={user_id}, admin_ids={config.bot.admin_ids}")
    return user_id in config.bot.admin_ids


# Стартовый обработчик админ-панели
@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    """Обработчик команды /admin"""
    if not is_admin(message.from_user.id):
        # Пользователь не администратор
        await message.answer(
            "⛔ У вас недостаточно прав для использования этой команды."
        )
        return

    # Пользователь - администратор, показываем админ-панель
    await message.answer(
        "🛠 <b>Адмін-панель</b>\n\n" "Виберіть дію:",
        reply_markup=ikb.get_admin_main_keyboard(),
    )
    await state.set_state(AdminStates.main_menu)


# Обработчик кнопки "Додати код"
@router.callback_query(AdminStates.main_menu, F.data == "admin_add_code")
async def add_code_menu(callback: CallbackQuery, state: FSMContext):
    """Меню добавления кодов"""
    await callback.message.edit_text(
        "➕ <b>Додавання кодів</b>\n\n" "Виберіть спосіб додавання кодів:",
        reply_markup=ikb.get_admin_add_code_keyboard(),
    )
    await state.set_state(AdminStates.add_code_menu)


# Обработчик добавления кода вручную
@router.callback_query(AdminStates.add_code_menu, F.data == "add_code_manually")
async def add_code_manually(callback: CallbackQuery, state: FSMContext):
    """Начало процесса добавления кода вручную"""
    # Сначала запрашиваем номинал карты
    await callback.message.edit_text(
        "💵 <b>Введіть номінал картки</b>\n\n"
        "Введіть номінал картки в доларах ($), наприклад: 10, 25, 50",
        reply_markup=ikb.get_back_to_admin_keyboard(),
    )
    await state.set_state(AdminStates.add_code_value)


# Обработчик ввода номинала карты
@router.message(AdminStates.add_code_value)
async def process_code_value(message: Message, state: FSMContext):
    """Обработка введенного номинала"""
    try:
        # Пытаемся преобразовать введенный текст в число
        value = float(message.text.strip().replace("$", ""))

        # Проверяем, что номинал положительный
        if value <= 0:
            await message.answer(
                "❌ Номінал картки повинен бути позитивним числом.\n"
                "Будь ласка, введіть коректний номінал:",
                reply_markup=ikb.get_back_to_admin_keyboard(),
            )
            return

        # Сохраняем номинал в состоянии
        await state.update_data(card_value=value)

        # Запрашиваем код карты
        await message.answer(
            f"🔑 <b>Введіть код картки номіналом ${value}</b>\n\n"
            f"Введіть код картки у форматі XXX-XXX-XXX:",
            reply_markup=ikb.get_back_to_admin_keyboard(),
        )
        await state.set_state(AdminStates.add_code_manually)

    except ValueError:
        await message.answer(
            "❌ Невірний формат номіналу. Введіть число, наприклад: 10, 25, 50",
            reply_markup=ikb.get_back_to_admin_keyboard(),
        )


# Обработчик ввода кода карты
@router.message(AdminStates.add_code_manually)
async def process_code_manually(
    message: Message, state: FSMContext, session: AsyncSession
):
    """Обработка введенного кода карты"""
    # Получаем данные из состояния
    data = await state.get_data()
    card_value = data.get("card_value")

    # Получаем и нормализуем код карты
    card_code = message.text.strip()

    # Проверяем, что код не пустой
    if not card_code:
        await message.answer(
            "❌ Введіть код картки.", reply_markup=ikb.get_back_to_admin_keyboard()
        )
        return

    # Проверяем, не существует ли уже такого кода
    stmt = select(CardCode).where(CardCode.code == card_code)
    result = await session.execute(stmt)
    existing_code = result.scalar_one_or_none()

    if existing_code:
        await message.answer(
            "❌ Такий код вже існує в базі даних.",
            reply_markup=ikb.get_back_to_admin_keyboard(),
        )
        return

    # Добавляем код в базу данных
    new_code = CardCode(
        card_value=card_value,
        code=card_code,
        is_used=False,
        added_by=message.from_user.id,
        added_at=datetime.now(),
    )

    session.add(new_code)
    await session.commit()

    # Отправляем сообщение об успешном добавлении
    await message.answer(
        f"✅ Код картки номіналом ${card_value} успішно доданий!\n\n"
        f"Бажаєте додати ще один код?",
        reply_markup=ikb.get_admin_add_more_codes_keyboard(),
    )

    # Возвращаемся в меню добавления кодов
    await state.set_state(AdminStates.add_code_menu)


# Обработчик для загрузки кодов из файла
@router.callback_query(AdminStates.add_code_menu, F.data == "add_code_file")
async def upload_code_file(callback: CallbackQuery, state: FSMContext):
    """Запрос на загрузку файла с кодами"""
    await callback.message.edit_text(
        "📁 <b>Завантаження кодів з файлу</b>\n\n"
        "Надішліть CSV-файл з кодами у форматі:\n"
        "<code>card_value,code</code>\n\n"
        "Приклад вмісту файлу:\n"
        "<code>10,ABC-DEF-GHI\n"
        "10,JKL-MNO-PQR\n"
        "25,STU-VWX-YZ1</code>",
        reply_markup=ikb.get_back_to_admin_keyboard(),
    )
    await state.set_state(AdminStates.add_code_file)


# Обработчик загруженного файла с кодами
@router.message(AdminStates.add_code_file, F.document)
async def process_code_file(message: Message, state: FSMContext):
    """Обработка загруженного файла с кодами"""
    # Проверяем, что файл имеет расширение CSV
    file_name = message.document.file_name
    if not file_name.lower().endswith(".csv"):
        await message.answer(
            "❌ Файл повинен бути у форматі CSV.",
            reply_markup=ikb.get_back_to_admin_keyboard(),
        )
        return

    try:
        # Скачиваем файл как байтовый поток
        file_bytes = await message.bot.download(message.document)

        # Декодируем байты в строку
        file_content = file_bytes.read().decode("utf-8")

        # Парсим CSV из строки
        codes_data = []
        csv_reader = csv.reader(file_content.splitlines())
        for row in csv_reader:
            if len(row) >= 2:  # Проверяем, что в строке есть минимум 2 значения
                try:
                    card_value = float(row[0].strip())
                    code = row[1].strip()
                    codes_data.append((card_value, code))
                except ValueError:
                    continue  # Пропускаем строки с некорректным номиналом

        # Сохраняем данные в состоянии
        await state.update_data(codes_data=codes_data)

        # Показываем сводку и запрашиваем подтверждение
        await message.answer(
            f"📊 <b>Знайдено {len(codes_data)} кодів в файлі</b>\n\n"
            f"Номінали карт:\n"
            + "\n".join(
                [
                    f"${value}: {sum(1 for v, _ in codes_data if v == value)} шт."
                    for value in set(value for value, _ in codes_data)
                ]
            )
            + "\n\nБажаєте додати ці коди в базу даних?",
            reply_markup=ikb.get_admin_confirm_codes_keyboard(),
        )
        await state.set_state(AdminStates.add_code_confirm)

    except Exception as e:
        logger.error(f"Ошибка при обработке файла с кодами: {e}")
        await message.answer(
            f"❌ Помилка при обробці файлу: {str(e)}. Перевірте формат файлу і спробуйте ще раз.",
            reply_markup=ikb.get_back_to_admin_keyboard(),
        )


# Обработчик подтверждения добавления кодов из файла
@router.callback_query(AdminStates.add_code_confirm, F.data == "confirm_add_codes")
async def confirm_add_codes(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Подтверждение добавления кодов из файла"""
    # Получаем данные из состояния
    data = await state.get_data()
    codes_data = data.get("codes_data", [])

    if not codes_data:
        await callback.message.edit_text(
            "❌ Немає кодів для додавання.",
            reply_markup=ikb.get_back_to_admin_keyboard(),
        )
        return

    # Счетчики для статистики
    added_count = 0
    duplicates_count = 0

    # Добавляем коды в базу данных
    for card_value, code in codes_data:
        # Проверяем, не существует ли уже такого кода
        stmt = select(CardCode).where(CardCode.code == code)
        result = await session.execute(stmt)
        existing_code = result.scalar_one_or_none()

        if existing_code:
            duplicates_count += 1
            continue

        # Добавляем новый код
        new_code = CardCode(
            card_value=card_value,
            code=code,
            is_used=False,
            added_by=callback.from_user.id,
            added_at=datetime.now(),
        )

        session.add(new_code)
        added_count += 1

    # Сохраняем изменения в базе данных
    await session.commit()

    # Отправляем сообщение с результатами
    await callback.message.edit_text(
        f"✅ <b>Результати додавання кодів</b>\n\n"
        f"✅ Успішно додано: {added_count} кодів\n"
        f"⚠️ Пропущено дублікатів: {duplicates_count} кодів\n\n"
        f"Бажаєте повернутися до адмін-панелі?",
        reply_markup=ikb.get_back_to_admin_keyboard(),
    )

    # Возвращаемся в главное меню админки
    await state.set_state(AdminStates.main_menu)


# Обработчик отмены добавления кодов
@router.callback_query(F.data == "admin_back")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню администратора"""
    await callback.message.edit_text(
        "🛠 <b>Адмін-панель</b>\n\n" "Виберіть дію:",
        reply_markup=ikb.get_admin_main_keyboard(),
    )
    await state.set_state(AdminStates.main_menu)


# Добавьте эти обработчики в файл /handlers/admin.py


# Исправленные обработчики для админ-панели


# Обработчик кнопки "Статистика"
@router.callback_query(F.data == "admin_stats")
async def admin_stats(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Обработчик кнопки Статистика"""
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

    await callback.message.edit_text(
        stats_message, reply_markup=ikb.get_back_to_admin_keyboard()
    )
    await state.set_state(AdminStates.main_menu)
    await callback.answer()


@router.message(F.text == "🗝 Залишок ключів")
async def rest_keys_button(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик кнопки остатков ключей из reply клавиатуры"""
    if not is_admin(message.from_user.id):
        return
    
    # Получаем все доступные коды, сгруппированные по номиналам
    stmt = (
        select(CardCode)
        .where(CardCode.is_used == False)  # Только неиспользованные
        .order_by(CardCode.card_value, CardCode.added_at.desc())
    )
    
    result = await session.execute(stmt)
    available_codes = result.scalars().all()
    
    # Группируем коды по номиналам
    codes_by_value = {}
    for code in available_codes:
        value = float(code.card_value)
        if value not in codes_by_value:
            codes_by_value[value] = []
        codes_by_value[value].append(code)
    
    # Формируем сообщение
    message_text = "🗝 <b>Залишок ключів</b>\n\n"
    
    if codes_by_value:
        total_available = 0
        
        # Сортируем по номиналам
        for card_value in sorted(codes_by_value.keys()):
            codes_list = codes_by_value[card_value]
            total_available += len(codes_list)
            
            message_text += f"💵 <b>${card_value:.0f}</b>: <b>{len(codes_list)}</b> доступно\n"
            
            # Добавляем сами коды
            for code in codes_list:
                message_text += f"<code>{code.code}</code>\n"
            
            message_text += "\n"  # Пустая строка между номиналами
        
        message_text += f"📊 <b>Загалом доступно: {total_available} ключів</b>\n"
    else:
        message_text += "❌ Ключів в базі немає\n"
    
    # Проверяем длину сообщения (лимит Telegram ~4096 символов)
    if len(message_text) > 4000:
        # Если сообщение слишком длинное, отправляем по частям
        await send_long_message(message, message_text)
    else:
        await message.answer(message_text)


    
    # Создаем клавиатуру с дополнительными опциями
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔄 Оновити дані", 
                callback_data="rest_keys"  # Исправляем callback_data
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Детальний звіт ключів", 
                callback_data="admin_keys_detail"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад", 
                callback_data="admin_back"
            )
        ]
    ]
    
    await callback.message.edit_text(
        message_text, 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await state.set_state(AdminStates.main_menu)
    await callback.answer()

## Также исправляем callback в детальном отчете
@router.callback_query(F.data == "admin_keys_detail")
async def admin_keys_detail(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Детальный отчет по ключам с показом самих кодов"""
    
    # Получаем доступные ключи по номиналам (показываем только первые 3 для каждого номинала)
    stmt = (
        select(CardCode)
        .where(CardCode.is_used == False)
        .order_by(CardCode.card_value, CardCode.added_at.desc())
    )
    
    result = await session.execute(stmt)
    available_codes = result.scalars().all()
    
    # Группируем по номиналам
    codes_by_value = {}
    for code in available_codes:
        value = float(code.card_value)
        if value not in codes_by_value:
            codes_by_value[value] = []
        codes_by_value[value].append(code)
    
    # Формируем детальное сообщение
    message_text = "🗝 <b>Детальний звіт по ключах</b>\n\n"
    
    if codes_by_value:
        for card_value in sorted(codes_by_value.keys()):
            codes_list = codes_by_value[card_value]
            message_text += f"💵 <b>${card_value:.0f} ({len(codes_list)} шт.):</b>\n"
            
            # Показываем первые 3 кода для каждого номинала
            for i, code in enumerate(codes_list[:3]):
                added_date = code.added_at.strftime("%d.%m") if code.added_at else "Невідомо"
                message_text += f"  🔑 <code>{code.code}</code> ({added_date})\n"
            
            # Если кодов больше 3, показываем количество остальных
            if len(codes_list) > 3:
                message_text += f"  ... та ще {len(codes_list) - 3} кодів\n"
            
            message_text += "\n"
    else:
        message_text += "❌ Доступних ключів немає\n\n"
    
    # Добавляем информацию о последних использованных ключах
    stmt_used = (
        select(CardCode)
        .where(CardCode.is_used == True)
        .order_by(CardCode.used_at.desc())
        .limit(5)
    )
    
    result_used = await session.execute(stmt_used)
    used_codes = result_used.scalars().all()
    
    if used_codes:
        message_text += "📋 <b>Останні використані ключі:</b>\n"
        for code in used_codes:
            used_date = code.used_at.strftime("%d.%m %H:%M") if code.used_at else "Невідомо"
            order_info = f" (#{code.order_id})" if code.order_id else ""
            message_text += f"  🔑 ${code.card_value} - {used_date}{order_info}\n"
    
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔙 Назад до ключів", 
                callback_data="rest_keys"  # Исправляем callback_data
            )
        ]
    ]
    
    await callback.message.edit_text(
        message_text, 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


# Также обновляем обработчик кнопки из reply клавиатуры
@router.message(F.text == "🗝 Залишок ключів")
async def users_button(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик кнопки пользователей из reply клавиатуры"""
    if not is_admin(message.from_user.id):
        return
    
    # Используем ту же логику, что и в callback обработчике
    await rest_keys(
        # Создаем фиктивный callback для совместимости
        type('MockCallback', (), {
            'message': message,
            'answer': lambda: None
        })(),
        state,
        session
    )


# Обработчик кнопки "Розіграш / Бонуси"
@router.callback_query(F.data == "admin_promos")
async def admin_promos(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки Розіграш / Бонуси"""
    await callback.message.edit_text(
        "🎁 <b>Розіграш / Бонуси</b>\n\n"
        "Цей розділ знаходиться в розробці.\n"
        "Скоро тут з'явиться можливість створювати промокоди та акції.",
        reply_markup=ikb.get_back_to_admin_keyboard(),
    )
    await state.set_state(AdminStates.main_menu)
    await callback.answer()


# Добавьте кнопку для просмотра отзывов в get_admin_main_keyboard
def get_admin_main_keyboard():
    """Клавиатура главного меню админ-панели"""
    buttons = [
        [InlineKeyboardButton(text="➕ Додати код", callback_data="admin_add_code")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🗝 Залишок ключів", callback_data="rest_keys")],
        [
            InlineKeyboardButton(
                text="🎁 Розіграш / Бонуси", callback_data="admin_promos"
            )
        ],
        [
            InlineKeyboardButton(text="📝 Відгуки", callback_data="admin_reviews")
        ],  # Новая кнопка
        [InlineKeyboardButton(text="🔙 На головну", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.callback_query(AdminStates.main_menu, F.data == "admin_reviews")
async def admin_reviews_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления отзывами"""

    keyboard = [
        [
            InlineKeyboardButton(
                text="📝 Останні відгуки", callback_data="admin_last_reviews"
            )
        ],
        [
            InlineKeyboardButton(
                text="⏳ Очікують модерації", callback_data="admin_pending_reviews"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Схвалені відгуки", callback_data="admin_approved_reviews"
            )
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ]

    await callback.message.edit_text(
        "📝 <b>Управління відгуками</b>\n\n" "Виберіть дію:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


@router.callback_query(F.data == "admin_pending_reviews")
async def admin_pending_reviews(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
):
    """Просмотр отзывов, ожидающих модерации"""
    # Получаем отзывы, ожидающие модерации
    stmt = (
        select(Review)
        .options(joinedload(Review.user), joinedload(Review.order))
        .where(Review.is_approved == False)
        .order_by(Review.created_at.desc())
        .limit(5)
    )
    result = await session.execute(stmt)
    reviews = result.scalars().all()

    if not reviews:
        await callback.message.edit_text(
            "⏳ <b>Відгуки, що очікують модерації</b>\n\n"
            "Немає відгуків для модерації.",
            reply_markup=ikb.get_back_to_admin_keyboard(),
        )
        return

    # Сохраняем смещение для пагинации
    await state.update_data(offset=0, total_reviews=len(reviews))

    # Показываем первый отзыв
    review = reviews[0]

    # Формируем кнопки для действий
    approve_button = InlineKeyboardButton(
        text="✅ Схвалити", callback_data=f"approve_review_{review.review_id}"
    )
    reject_button = InlineKeyboardButton(
        text="❌ Відхилити", callback_data=f"reject_review_{review.review_id}"
    )
    next_button = InlineKeyboardButton(text="➡️ Наступний", callback_data="next_review")
    back_button = InlineKeyboardButton(text="🔙 Назад", callback_data="admin_reviews")

    keyboard = [[approve_button, reject_button], [next_button], [back_button]]

    # Показываем отзыв
    user_name = review.user.first_name or "Користувач"
    review_text = (
        f"⏳ <b>Відгук #{review.review_id} на модерації</b>\n\n"
        f"👤 <b>Користувач:</b> {user_name} (ID: {review.user_id})\n"
        f"🛍 <b>Замовлення:</b> #{review.order_id}\n"
        f"⭐ <b>Оцінка:</b> {'⭐' * review.rating}\n"
        f"📅 <b>Дата:</b> {review.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"💬 <b>Коментар:</b>\n{review.comment}"
    )

    await callback.message.edit_text(
        review_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("reject_review_"))
async def reject_review(callback: CallbackQuery, session: AsyncSession):
    """Отклонение отзыва администратором"""
    review_id = int(callback.data.split("_")[2])

    # Получаем отзыв из БД
    stmt = select(Review).where(Review.review_id == review_id)
    result = await session.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        await callback.answer("Відгук не знайдено!", show_alert=True)
        return

    # Удаляем отзыв
    await session.delete(review)
    await session.commit()

    # Уведомляем админа
    await callback.answer("Відгук відхилено і видалено!", show_alert=True)

    # Возвращаемся к списку отзывов
    await admin_pending_reviews(callback, session, await callback.bot.get_current())


# Обработчик для просмотра последних отзывов
@router.callback_query(F.data == "admin_last_reviews")
async def admin_last_reviews(callback: CallbackQuery, session: AsyncSession):
    """Просмотр последних отзывов"""
    # Получаем последние 10 отзывов
    stmt = (
        select(Review)
        .options(joinedload(Review.user))
        .order_by(Review.created_at.desc())
        .limit(10)
    )
    result = await session.execute(stmt)
    reviews = result.scalars().all()

    if not reviews:
        await callback.message.edit_text(
            "📝 <b>Останні відгуки</b>\n\n" "Відгуків поки немає.",
            reply_markup=ikb.get_back_to_admin_keyboard(),
        )
        return

    # Формируем сообщение с отзывами
    reviews_text = "📝 <b>Останні відгуки</b>\n\n"

    for review in reviews:
        user_name = review.user.first_name or "Користувач"
        reviews_text += (
            f"👤 {user_name} (ID: {review.user_id})\n"
            f"⭐ {'⭐' * review.rating}\n"
            f"💬 {review.comment}\n"
            f"📅 {review.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )

    await callback.message.edit_text(
        reviews_text, reply_markup=ikb.get_back_to_admin_keyboard()
    )


# Обработчик для просмотра отзывов по оценкам
@router.callback_query(F.data == "admin_rating_reviews")
async def admin_rating_reviews(callback: CallbackQuery, session: AsyncSession):
    """Статистика отзывов по оценкам"""
    # Получаем статистику по оценкам
    stats = []
    for rating in range(1, 6):
        count = await session.scalar(
            select(func.count()).select_from(Review).where(Review.rating == rating)
        )
        stats.append((rating, count))

    # Формируем сообщение со статистикой
    stats_text = "⭐ <b>Відгуки за оцінками</b>\n\n"

    for rating, count in stats:
        stats_text += f"{'⭐' * rating}: {count} відгуків\n"

    await callback.message.edit_text(
        stats_text, reply_markup=ikb.get_back_to_admin_keyboard()
    )
