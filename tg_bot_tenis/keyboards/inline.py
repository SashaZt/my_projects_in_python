# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

class InlineKeyboards:
    @staticmethod
    def event_actions(event_id: int) -> InlineKeyboardMarkup:
        """Кнопки для действий с событием"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="✅ Записаться", callback_data=f"register_{event_id}"),
            InlineKeyboardButton(text="❌ Отменить запись", callback_data=f"cancel_{event_id}")
        )
        builder.adjust(2)
        return builder.as_markup()
    
    @staticmethod
    def back_to_events() -> InlineKeyboardMarkup:
        """Кнопка возврата к списку событий"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="◀️ К событиям", callback_data="user_events")
        )
        return builder.as_markup()
    
    @staticmethod
    def refresh_event(event_id: int) -> InlineKeyboardMarkup:
        """Кнопка обновления события"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_{event_id}"),
            InlineKeyboardButton(text="◀️ К событиям", callback_data="user_events")
        )
        builder.adjust(2)
        return builder.as_markup()