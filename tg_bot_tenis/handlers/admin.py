# handlers/admin.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services.user_service import UserService
from services.event_service import EventService
from services.booking_service import BookingService
from keyboards.admin import AdminKeyboards
from utils.formatters import MessageFormatter
from utils.validators import Validators
from config import ADMIN_IDS, LOCATIONS
from config.logger import logger

router = Router()

class CreateEventStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_location = State()

@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Админ панель"""
    user_id = message.from_user.id
    
    # Отладочная информация
    logger.info(f"DEBUG: Пользователь {user_id} пытается войти в админ панель")
    logger.info(f"DEBUG: ADMIN_IDS: {ADMIN_IDS}")
    logger.info(f"DEBUG: user_id в ADMIN_IDS: {user_id in ADMIN_IDS}")
    
    if user_id not in ADMIN_IDS:
        await message.answer(f"❌ У вас нет прав администратора\n\nВаш ID: {user_id}\nРазрешенные ID: {ADMIN_IDS}")
        return
    
    # Создаем или обновляем админа в БД
    await UserService.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        is_admin=True
    )
    
    text = f"""🔧 **Панель администратора**

Добро пожаловать, {message.from_user.first_name}!

Доступные действия:"""
    
    keyboard = AdminKeyboards.main_menu()
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")

@router.callback_query(F.data == "admin_create_event")
async def start_create_event(callback: CallbackQuery, state: FSMContext):
    """Начать создание события"""
    logger.info(f"DEBUG: admin_create_event вызван пользователем {callback.from_user.id}")
    
    await callback.answer()
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return
    
    await state.set_state(CreateEventStates.waiting_for_title)
    
    # Создаем кнопку отмены
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel"))
    
    try:
        await callback.message.edit_text(
            "➕ **Создание нового события**\n\n"
            "Введите название тренировки:\n"
            "Например: `Групповая тренировка`",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        logger.info("DEBUG: Сообщение успешно отредактировано")
    except Exception as e:
        logger.info(f"DEBUG: Ошибка при редактировании сообщения: {e}")


@router.callback_query(F.data == "admin_my_events")
async def show_admin_events(callback: CallbackQuery):
    """Показать события администратора"""
    logger.info(f"DEBUG: admin_my_events вызван пользователем {callback.from_user.id}")
    
    await callback.answer()
    
    user = await UserService.get_or_create_user(callback.from_user.id)
    events = await EventService.get_events_by_creator(user.id)
    
    if not events:
        try:
            await callback.message.edit_text(
                "📋 У вас нет созданных событий\n\n"
                "Используйте кнопку ➕ Создать событие",
                reply_markup=AdminKeyboards.main_menu()
            )
        except Exception as e:
            logger.info(f"DEBUG: Ошибка при редактировании: {e}")
            await callback.message.answer(
                "📋 У вас нет созданных событий\n\n"
                "Используйте кнопку ➕ Создать событие"
            )
        return
    
    message_text = MessageFormatter.format_admin_event_list(events)
    
    # Создаем кнопки для управления событиями
    builder = InlineKeyboardBuilder()
    for event in events[:10]:  # Ограничиваем до 10 событий
        booking_count = await BookingService.get_booking_count(event.id)
        builder.add(
            InlineKeyboardButton(
                text=f"🏋️‍♂️ {event.title} ({booking_count}/4)",
                callback_data=f"admin_event_{event.id}"
            )
        )
    builder.add(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_main")
    )
    builder.adjust(1)
    
    try:
        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.info(f"DEBUG: Ошибка при показе событий: {e}")

@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Статистика для админа"""
    logger.info(f"DEBUG: admin_stats вызван пользователем {callback.from_user.id}")
    
    await callback.answer()
    
    user = await UserService.get_or_create_user(callback.from_user.id)
    events = await EventService.get_events_by_creator(user.id)
    
    total_events = len(events)
    active_events = len([e for e in events if e.is_active])
    
    total_bookings = 0
    for event in events:
        bookings = await BookingService.get_booking_count(event.id)
        total_bookings += bookings
    
    stats_text = f"""📊 **Статистика**

📋 Всего событий: {total_events}
✅ Активных событий: {active_events}
👥 Всего записей: {total_bookings}

📈 **Детали по событиям:**"""

    for event in events[:5]:  # Показываем только первые 5
        booking_count = await BookingService.get_booking_count(event.id)
        status = "🟢" if event.is_active else "🔴"
        stats_text += f"\n{status} {event.title}: {booking_count}/4"
    
    keyboard = AdminKeyboards.main_menu()
    
    try:
        await callback.message.edit_text(
            stats_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.info(f"DEBUG: Ошибка при показе статистики: {e}")

@router.callback_query(F.data == "admin_main")
async def admin_main_menu(callback: CallbackQuery):
    """Возврат в главное меню админа"""
    await callback.answer()
    
    keyboard = AdminKeyboards.main_menu()
    
    try:
        await callback.message.edit_text(
            "🔧 **Панель администратора**\n\nВыберите действие:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.info(f"DEBUG: Ошибка в admin_main: {e}")

@router.callback_query(F.data.startswith("admin_event_"))
async def admin_event_detail(callback: CallbackQuery):
    """Детали события для админа с участниками"""
    logger.info(f"DEBUG: admin_event_ вызван пользователем {callback.from_user.id}")
    await callback.answer()
    
    event_id = int(callback.data.split("_")[2])
    event = await EventService.get_event_by_id(event_id)
    
    if not event:
        await callback.answer("❌ Событие не найдено", show_alert=True)
        return
    
    # Форматируем основное сообщение о событии
    message_text = await MessageFormatter.format_event_message(event)
    
    # Получаем участников
    bookings = await BookingService.get_event_bookings(event_id)
    
    if bookings:
        message_text += "\n\n👥 **Участники:**\n"
        
        for i, booking in enumerate(bookings, 1):
            user = await UserService.get_user_by_id(booking.user_id)
            if user:
                # Формируем имя участника
                name_parts = []
                
                if user.first_name:
                    # Экранируем специальные символы markdown
                    first_name = user.first_name.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
                    name_parts.append(first_name)
                if user.last_name:
                    # Экранируем специальные символы markdown
                    last_name = user.last_name.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
                    name_parts.append(last_name)
                
                display_name = " ".join(name_parts) if name_parts else "Без имени"
                
                # Добавляем username если есть (экранируем @)
                if user.username:
                    # username = user.username.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
                    username = user.username.replace('*', '\\*').replace('`', '\\`')
                    display_name += f" (@{username})"
                
                message_text += f"{i}. {display_name}\n"
            else:
                message_text += f"{i}\\. Пользователь ID: {booking.user_id}\n"
        
        # Добавляем общий доход
        total_income = len(bookings) * 90
        message_text += f"\n💰 **Общий доход: {total_income} злотых**"
    else:
        message_text += "\n\n👥 **Участники:** Пока никто не записался"
    

    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_{event_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_{event_id}"),
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_my_events")
    )
    builder.adjust(2, 1)
    
    try:
        await callback.message.edit_text(
            f"🔧 **Управление событием**\n\n{message_text}",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        logger.info("DEBUG: Сообщение успешно отправлено")
    except Exception as e:
        logger.info(f"DEBUG: Ошибка при показе деталей события: {e}")
        # Если проблема с markdown, отправляем без разметки
        try:
            # Убираем всю markdown разметку
            clean_text = message_text.replace('**', '').replace('*', '').replace('`', '')
            # clean_text = message_text.replace('**', '').replace('*', '').replace('_', '').replace('`', '')
            await callback.message.edit_text(
                f"🔧 Управление событием\n\n{clean_text}",
                reply_markup=builder.as_markup()
            )
            logger.info("DEBUG: Сообщение отправлено без markdown")
        except Exception as e2:
            logger.info(f"DEBUG: Критическая ошибка: {e2}")
            await callback.answer("❌ Произошла ошибка при отображении", show_alert=True)


@router.callback_query(F.data.startswith("admin_participants_"))
async def show_participants(callback: CallbackQuery):
    """Показать участников события"""
    logger.info(f"DEBUG: admin_participants_ вызван пользователем {callback.from_user.id}")
    await callback.answer()
    
    event_id = int(callback.data.split("_")[2])
    bookings = await BookingService.get_event_bookings(event_id)
    
    if not bookings:
        await callback.answer("👥 Пока никто не записался", show_alert=True)
        return
    
    # Получаем информацию о событии
    event = await EventService.get_event_by_id(event_id)
    event_title = event.title if event else f"Событие ID {event_id}"
    
    participants_text = f"👥 **Участники события: {event_title}**\n\n"
    
    for i, booking in enumerate(bookings, 1):
        user = await UserService.get_user_by_id(booking.user_id)
        if user:
            # Формируем имя участника
            name_parts = []
            
            if user.first_name:
                name_parts.append(user.first_name)
            if user.last_name:
                name_parts.append(user.last_name)
            
            display_name = " ".join(name_parts) if name_parts else "Без имени"
            
            # Добавляем username если есть
            if user.username:
                display_name += f" (@{user.username})"
            
            participants_text += f"{i}. {display_name}\n"
            participants_text += f"   📱 ID: {user.telegram_id}\n\n"
        else:
            participants_text += f"{i}. Пользователь ID: {booking.user_id}\n\n"
    
    participants_text += f"💰 **Общий доход: {len(bookings) * 90} злотых**"
    
    await callback.message.answer(participants_text, parse_mode="Markdown")
@router.callback_query(F.data.startswith("admin_delete_"))
async def confirm_delete_event(callback: CallbackQuery):
    """Подтверждение удаления события"""
    logger.info(f"DEBUG: admin_delete_ вызван пользователем {callback.from_user.id}")
    await callback.answer()
    
    event_id = int(callback.data.split("_")[2])
    event = await EventService.get_event_by_id(event_id)
    
    if not event:
        await callback.answer("❌ Событие не найдено", show_alert=True)
        return
    
    keyboard = AdminKeyboards.confirm_delete(event_id)
    try:
        await callback.message.edit_text(
            f"⚠️ **Подтверждение удаления**\n\n"
            f"Вы уверены, что хотите удалить событие:\n"
            f"**{event.title}**\n"
            f"📅 {event.event_date} в {event.event_time}?\n\n"
            f"❗️ Это действие нельзя отменить!",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.info(f"DEBUG: Ошибка при подтверждении удаления: {e}")

@router.callback_query(F.data.startswith("admin_confirm_delete_"))
async def delete_event(callback: CallbackQuery):
    """Удаление события"""
    logger.info(f"DEBUG: admin_confirm_delete_ вызван пользователем {callback.from_user.id}")
    await callback.answer()
    
    event_id = int(callback.data.split("_")[3])
    
    # Деактивируем событие
    await EventService.deactivate_event(event_id)
    
    try:
        await callback.message.edit_text(
            "✅ Событие успешно удалено",
            reply_markup=AdminKeyboards.main_menu()
        )
    except Exception as e:
        logger.info(f"DEBUG: Ошибка при удалении: {e}")
        await callback.message.answer("✅ Событие успешно удалено")

@router.callback_query(F.data.startswith("admin_edit_"))
async def edit_event(callback: CallbackQuery):
    """Редактирование события"""
    logger.info(f"DEBUG: admin_edit_ вызван пользователем {callback.from_user.id}")
    await callback.answer()
    
    event_id = int(callback.data.split("_")[2])
    event = await EventService.get_event_by_id(event_id)
    
    if not event:
        await callback.answer("❌ Событие не найдено", show_alert=True)
        return
    
    # Создаем меню редактирования
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📅 Изменить дату", callback_data=f"edit_date_{event_id}"),
        InlineKeyboardButton(text="🕐 Изменить время", callback_data=f"edit_time_{event_id}"),
        InlineKeyboardButton(text="📍 Изменить место", callback_data=f"edit_location_{event_id}"),
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin_event_{event_id}")
    )
    builder.adjust(1)
    
    try:
        await callback.message.edit_text(
            f"✏️ **Редактирование события**\n\n"
            f"**{event.title}**\n"
            f"📅 Дата: {event.event_date}\n"
            f"🕐 Время: {event.event_time}\n"
            f"📍 Место: {event.location}\n\n"
            f"Что хотите изменить?",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.info(f"DEBUG: Ошибка при редактировании: {e}")



@router.message(CreateEventStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Обработка названия события"""
    title = message.text.strip()
    
    if len(title) < 3:
        await message.answer("❌ Название должно содержать минимум 3 символа")
        return
    
    await state.update_data(title=title)
    await state.set_state(CreateEventStates.waiting_for_date)
    
    # Создаем кнопку отмены
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel"))
    
    await message.answer(
        "📅 **Дата тренировки**\n\n"
        "Введите дату в формате ДД.ММ.ГГГГ\n"
        "Например: `15.07.2025`",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.message(CreateEventStates.waiting_for_date)
async def process_date(message: Message, state: FSMContext):
    """Обработка даты события"""
    date_str = message.text.strip()
    
    if not Validators.validate_date(date_str):
        await message.answer(
            "❌ Неверный формат даты!\n"
            "Используйте формат ДД.ММ.ГГГГ\n"
            "Например: `15.07.2025`"
        )
        return
    
    await state.update_data(event_date=date_str)
    await state.set_state(CreateEventStates.waiting_for_time)
    
    # Создаем кнопку отмены
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel"))
    
    await message.answer(
        "🕐 **Время тренировки**\n\n"
        "Введите время в формате ЧЧ:ММ\n"
        "Например: `19:00`",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )


@router.message(CreateEventStates.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    """Обработка времени события"""
    time_str = message.text.strip()
    
    if not Validators.validate_time(time_str):
        await message.answer(
            "❌ Неверный формат времени!\n"
            "Используйте формат ЧЧ:ММ\n"
            "Например: `19:00`"
        )
        return
    
    # Проверяем что дата и время в будущем
    data = await state.get_data()
    event_date = data.get("event_date")
    
    if not Validators.validate_future_datetime(event_date, time_str):
        await message.answer(
            "❌ Дата и время должны быть в будущем!"
        )
        return
    
    await state.update_data(event_time=time_str)
    await state.set_state(CreateEventStates.waiting_for_location)
    
    keyboard = AdminKeyboards.location_menu()  # Эта клавиатура уже содержит кнопку отмены
    await message.answer(
        "📍 **Место проведения**\n\n"
        "Выберите место проведения тренировки:",
        reply_markup=keyboard
    )



@router.callback_query(F.data.startswith("location_"))
async def process_location(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора локации и создание события в топике"""
    await callback.answer()
    
    location_id = callback.data.split("_")[1]
    
    if location_id not in LOCATIONS:
        await callback.answer("❌ Неверная локация", show_alert=True)
        return
    
    location = LOCATIONS[location_id]
    data = await state.get_data()
    
    # Создаем событие
    user = await UserService.get_or_create_user(callback.from_user.id)
    event = await EventService.create_event(
        title=data["title"],
        event_date=data["event_date"],
        event_time=data["event_time"],
        location=location,
        created_by=user.id
    )
    
    await state.clear()
    
    # Определяем топик по дню недели
    from config import GROUP_ID, get_topic_id_for_date, get_weekday_name
    
    # Проверяем, детская ли это тренировка
    is_kids = "дет" in data["title"].lower() or "ребенок" in data["title"].lower()
    
    topic_id = get_topic_id_for_date(data["event_date"], is_kids=is_kids)
    weekday_name = get_weekday_name(data["event_date"])
    
    if is_kids:
        topic_name = "Тренировка для детей"
    else:
        topic_name = f"Тренировка {weekday_name}"
    
    logger.info(f"🎯 Событие {event.id} будет размещено в топике {topic_id} ({topic_name})")
    
    try:
        # Форматируем сообщение для группы
        from utils.group_formatters import GroupMessageFormatter
        
        group_message_text = await GroupMessageFormatter.format_group_event_message(event)
        group_keyboard = GroupMessageFormatter.create_group_keyboard(event.id)
        
        logger.info(f"📝 Отправляем сообщение в группу {GROUP_ID}, топик {topic_id}")
        logger.info(f"📄 Текст сообщения (первые 200 символов): {group_message_text[:200]}...")
        
        # Отправляем сообщение в соответствующий топик
        group_message = await callback.bot.send_message(
            chat_id=GROUP_ID,
            text=group_message_text,
            message_thread_id=topic_id,  # Это ключевой параметр для топика!
            reply_markup=group_keyboard,
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Сообщение отправлено! Message ID: {group_message.message_id}")
        
        # Сохраняем ID сообщения в БД
        await EventService.update_group_message_id(event.id, group_message.message_id)
        
        # Простое сообщение об успехе БЕЗ markdown
        success_message = f"""✅ Событие создано и опубликовано!

🎾 {event.title}
📅 {event.event_date} ({topic_name})
🕐 {event.event_time}
📍 {location}

📨 Размещено в топике: {topic_name}
🆔 ID события: {event.id}

Пользователи смогут записываться через кнопки в группе."""
        
        await callback.message.edit_text(success_message)
        
        logger.info(f"✅ Событие {event.id} успешно создано в топике {topic_id}")
        
    except Exception as e:
        logger.info(f"❌ Ошибка при создании события в топике: {e}")
        logger.info(f"❌ Тип ошибки: {type(e)}")
        
        # Максимально простое сообщение об ошибке
        simple_error = f"Ошибка при публикации события. ID: {event.id}"
        
        try:
            await callback.message.edit_text(simple_error)
        except Exception as e2:
            logger.info(f"❌ Даже простое сообщение не отправляется: {e2}")
            try:
                # Последняя попытка - новое сообщение без форматирования
                await callback.message.answer(f"Событие создано. ID: {event.id}")
            except Exception as e3:
                logger.info(f"❌ Критическая ошибка: {e3}")
                # Хотя бы ответим на callback
                await callback.answer(f"Событие создано! ID: {event.id}", show_alert=True)


@router.callback_query(F.data == "admin_cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отмена действия"""
    await callback.answer()
    await state.clear()
    
    keyboard = AdminKeyboards.main_menu()
    await callback.message.edit_text(
        "❌ Действие отменено\n\n"
        "🔧 **Панель администратора**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# DEBUG функция должна быть В САМОМ КОНЦЕ!
@router.callback_query()
async def debug_all_admin_callbacks(callback: CallbackQuery):
    """Отладка всех callback'ов которые не обработались"""
    logger.info(f"DEBUG: Необработанный callback от пользователя {callback.from_user.id}")
    logger.info(f"DEBUG: Данные callback: {callback.data}")
    logger.info(f"DEBUG: Пользователь админ: {callback.from_user.id in ADMIN_IDS}")
    
    await callback.answer("🐛 DEBUG: Callback получен но не обработан", show_alert=True)


@router.callback_query()
async def debug_admin_callbacks(callback: CallbackQuery):
    """Debug админских callback'ов"""
    logger.info(f"🔧 ADMIN DEBUG: callback от {callback.from_user.id}")
    logger.info(f"🔧 ADMIN Chat ID: {callback.message.chat.id}")
    logger.info(f"🔧 ADMIN callback.data: '{callback.data}'")