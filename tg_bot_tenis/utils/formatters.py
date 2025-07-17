# utils/formatters.py
from datetime import datetime
from typing import List
from database.models import Event, Booking
from services.booking_service import BookingService
from config import PRICE, CURRENCY, CONDITIONS_TEXT


class MessageFormatter:
    @staticmethod
    async def format_event_message(event: Event) -> str:
        """Форматирует сообщение о событии"""
        # Получаем количество записей
        booking_count = await BookingService.get_booking_count(event.id)
        
        # Создаем визуализацию мест
        places_visual = ""
        for i in range(4):  # MAX_PARTICIPANTS = 4
            if i < booking_count:
                places_visual += "🟩"
            else:
                places_visual += "⬜️"
        
        message = f"""**{event.title}**

📅 Дата: {event.event_date}
🕐 Время: {event.event_time}
📍 Место: {event.location}
👥 Количество мест: {places_visual} ({booking_count}/4)
💰 Стоимость: {PRICE} {CURRENCY}

{CONDITIONS_TEXT}"""
        
        return message
    
    @staticmethod
    def format_admin_event_list(events: List[Event]) -> str:
        """Форматирует список событий для админа"""
        if not events:
            return "📋 Нет активных событий"
        
        message = "📋 **Ваши события:**\n\n"
        for event in events:
            message += f"🏋️‍♂️ **{event.title}**\n"
            message += f"📅 {event.event_date} в {event.event_time}\n"
            message += f"📍 {event.location}\n"
            message += f"ID: `{event.id}`\n\n"
        
        return message
    
    @staticmethod
    def format_user_bookings(bookings: List[tuple]) -> str:
        """Форматирует список записей пользователя"""
        if not bookings:
            return "📋 У вас нет активных записей"
        
        message = "📋 **Ваши записи:**\n\n"
        for booking, title, event_date, event_time in bookings:
            message += f"🏋️‍♂️ **{title}**\n"
            message += f"📅 {event_date} в {event_time}\n"
            message += f"ID события: `{booking.event_id}`\n\n"
        
        return message