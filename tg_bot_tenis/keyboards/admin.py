# keyboards/admin.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import LOCATIONS

class AdminKeyboards:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню администратора"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="➕ Создать событие", callback_data="admin_create_event"),
            InlineKeyboardButton(text="📋 Мои события", callback_data="admin_my_events"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def location_menu() -> InlineKeyboardMarkup:
        """Меню выбора локации"""
        builder = InlineKeyboardBuilder()
        for location_id, location_name in LOCATIONS.items():
            builder.add(
                InlineKeyboardButton(
                    text=f"📍 {location_name}",
                    callback_data=f"location_{location_id}"
                )
            )
        builder.add(
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel")
        )
        builder.adjust(1)
        return builder.as_markup()
    
    @staticmethod
    def event_management(event_id: int) -> InlineKeyboardMarkup:
        """Управление событием с редактированием"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_{event_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_delete_{event_id}"),
            InlineKeyboardButton(text="◀️ Назад", callback_data="admin_my_events")
        )
        builder.adjust(2, 1)
        return builder.as_markup()
    
    @staticmethod
    def confirm_delete(event_id: int) -> InlineKeyboardMarkup:
        """Подтверждение удаления события"""
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"admin_confirm_delete_{event_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_event_{event_id}")
        )
        builder.adjust(2)
        return builder.as_markup()