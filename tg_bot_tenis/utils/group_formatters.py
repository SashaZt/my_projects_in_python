import re
from typing import List
from database.models import Event
from config import PRICE, CURRENCY, CONDITIONS_TEXT
from config.logger import logger

class GroupMessageFormatter:
    @staticmethod
    async def format_group_event_message(event: Event) -> str:
        """Форматирует сообщение о событии для группы с MarkdownV2"""
        from services.booking_service import BookingService
        
        try:
            booking_count = await BookingService.get_booking_count(event.id)
            
            # Создаем визуализацию мест
            places_visual = ""
            for i in range(4):
                if i < booking_count:
                    places_visual += "🟩"
                else:
                    places_visual += "⬜️"
            
            # Экранируем для MarkdownV2
            safe_title = escape_markdown_v2(event.title)
            safe_location = escape_markdown_v2(event.location)
            safe_conditions = escape_markdown_v2(CONDITIONS_TEXT)
            
            # Форматируем дату и время без дополнительного экранирования
            safe_date = escape_markdown_v2(str(event.event_date))
            safe_time = escape_markdown_v2(str(event.event_time))
            
            message = f"""🎾 *{safe_title}*

📅 Дата: {safe_date}
🕐 Время: {safe_time}
📍 Место: {safe_location}
👥 Количество мест: {places_visual} \\({booking_count}/4\\)
💰 Стоимость: {PRICE} {CURRENCY}

{safe_conditions}"""
            
            # Добавляем участников
            bookings = await BookingService.get_event_bookings(event.id)
            if bookings:
                message += f"\n\n📋 *Список участников:*\n"
                
                from services.user_service import UserService
                for i, booking in enumerate(bookings, 1):
                    user = await UserService.get_user_by_id(booking.user_id)
                    if user:
                        if user.username:
                            # Экранируем username для MarkdownV2
                            display_name = escape_markdown_v2(f"@{user.username}")
                        else:
                            name_parts = []
                            if user.first_name:
                                name_parts.append(escape_markdown_v2(user.first_name))
                            if user.last_name:
                                name_parts.append(escape_markdown_v2(user.last_name))
                            display_name = " ".join(name_parts) if name_parts else f"ID:{user.telegram_id}"
                        
                        message += f"{i}\\. {display_name}\n"
                    else:
                        message += f"{i}\\. Пользователь ID: {booking.user_id}\n"
            
            logger.info(f"Форматированное сообщение:\n{message}")
            return message
            
        except Exception as e:
            logger.error(f"❌ Ошибка при форматировании: {e}")
            return await GroupMessageFormatter.create_simple_message(event)
    
    @staticmethod
    def create_group_keyboard(event_id: int):
        """Создает клавиатуру для сообщения в группе"""
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from aiogram.types import InlineKeyboardButton
        
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text="✅ Записаться", 
                callback_data=f"join_event_{event_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отменить запись", 
                callback_data=f"leave_event_{event_id}"
            )
        )
        builder.adjust(2)  # 2 кнопки в ряд
        return builder.as_markup()

class AdminMessageFormatter:
    @staticmethod
    async def format_event_created_message(event: Event, topic_id: int, weekday_name: str) -> str:
        """Форматирует сообщение о созданном событии для админа"""
        
        from services.booking_service import BookingService
        booking_count = await BookingService.get_booking_count(event.id)
        
        message = f"""✅ Событие создано и опубликовано!

🎾 {event.title}
📅 {event.event_date} ({weekday_name})
🕐 {event.event_time}
📍 {event.location}
👥 Записано: {booking_count}/4

📨 Опубликовано в топике: {weekday_name} (ID: {topic_id})
🆔 ID события: {event.id}

🎯 Что дальше:
• Пользователи увидят событие в соответствующем топике группы
• Они смогут записываться через кнопки "✅ Записаться"
• Список участников будет обновляться автоматически
• Вы можете отслеживать записи через "📋 Мои события"

💡 Событие автоматически размещено в правильном топике форума."""
        
        return message

def escape_markdown_v2(text: str) -> str:
    """Экранирование текста для MarkdownV2, корректно обрабатывая специальные символы"""
    if not text:
        return ""
    
    # Список специальных символов MarkdownV2
    escape_chars = r'([_*[\]()~`>#+-=|{}.!\\])'
    
    # Экранируем специальные символы
    text = re.sub(escape_chars, r'\\\1', text)
    
    # Обрабатываем тройное подчеркивание
    text = text.replace('___', '__\\r_')
    
    return text