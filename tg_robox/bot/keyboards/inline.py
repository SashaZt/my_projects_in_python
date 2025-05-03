from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import RobloxProduct
from typing import List


def get_products_keyboard(products: List[RobloxProduct]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора продукта Roblox"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого продукта
    for product in products:
        builder.row(
            InlineKeyboardButton(
                text=f"{product.name} - {product.price_uah}₴",
                callback_data=f"product_{product.product_id}",
            )
        )

    # Кнопка "Назад"
    builder.row(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))

    return builder.as_markup()


def get_payment_keyboard(product_id: int, amount: float) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для подтверждения оплаты"""
    builder = InlineKeyboardBuilder()

    # Кнопка "Оплатить"
    builder.add(
        InlineKeyboardButton(
            text="💳 Оплатити", callback_data=f"pay_{product_id}_{amount}"
        )
    )

    # Кнопка "Назад"
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_products"))

    return builder.as_markup()


def get_payment_url_keyboard(url: str) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура с URL для оплаты"""
    builder = InlineKeyboardBuilder()

    # Кнопка с URL для перехода на страницу оплаты
    builder.add(InlineKeyboardButton(text="💳 Перейти до оплати", url=url))

    return builder.as_markup()


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура с кнопкой возврата в главное меню"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🔙 Головне меню", callback_data="back_to_menu")
    )
    return builder.as_markup()


def get_back_to_products_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура с кнопкой возврата к выбору продуктов"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🔙 Назад до списку", callback_data="back_to_products"
        )
    )
    return builder.as_markup()


def get_offer_agreement_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура с кнопкой для получения документа оферты"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="📄 Завантажити умови оферти", callback_data="get_offer_pdf"
        )
    )
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu"))
    return builder.as_markup()
