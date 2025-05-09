# keyboards/inline.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from db.models import RobloxProduct
from typing import List
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_products_keyboard(products: List[RobloxProduct]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для выбора продукта Roblox"""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки для каждого продукта
    for product in products:
        builder.row(
            InlineKeyboardButton(
                text=f"{product.name} | {product.price_uah}₴",
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


# Добавьте эти функции в ваш файл keyboards/inline.py


def get_admin_main_keyboard():
    """Клавиатура главного меню админ-панели"""
    buttons = [
        [InlineKeyboardButton(text="➕ Додати код", callback_data="admin_add_code")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👤 Користувачі", callback_data="admin_users")],
        [
            InlineKeyboardButton(
                text="🎁 Розіграш / Бонуси", callback_data="admin_promos"
            )
        ],
        [InlineKeyboardButton(text="🔙 На головну", callback_data="back_to_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_add_code_keyboard():
    """Клавиатура меню добавления кодов"""
    buttons = [
        [InlineKeyboardButton(text="✋ Вручну", callback_data="add_code_manually")],
        [InlineKeyboardButton(text="📁 З файлу", callback_data="add_code_file")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_admin_keyboard():
    """Клавиатура с кнопкой возврата в админ-панель"""
    buttons = [
        [
            InlineKeyboardButton(
                text="🔙 Назад до адмін-панелі", callback_data="admin_back"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_add_more_codes_keyboard():
    """Клавиатура после добавления кода вручную"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Так, додати ще", callback_data="add_code_manually"
            )
        ],
        [InlineKeyboardButton(text="🔙 Ні, повернутися", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_confirm_codes_keyboard():
    """Клавиатура подтверждения добавления кодов из файла"""
    buttons = [
        [
            InlineKeyboardButton(
                text="✅ Так, додати", callback_data="confirm_add_codes"
            )
        ],
        [InlineKeyboardButton(text="❌ Ні, скасувати", callback_data="admin_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_main_menu_keyboard(is_admin=False):
    """Клавиатура главного меню с опциональной кнопкой админ-панели"""
    buttons = [
        [InlineKeyboardButton(text="🛍 Купити картку", callback_data="buy_card")],
        [InlineKeyboardButton(text="❓ Підтримка / FAQ", callback_data="support")],
        [InlineKeyboardButton(text="🎁 Розіграш / Бонуси", callback_data="bonuses")],
        [InlineKeyboardButton(text="🛍 Мої покупки", callback_data="my_purchases")],
    ]

    # Добавляем кнопку админ-панели, если пользователь администратор
    if is_admin:
        buttons.append(
            [InlineKeyboardButton(text="🛠 Адмін-панель", callback_data="admin_panel")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_only_keyboard():
    """Клавиатура только для администраторов без пользовательских кнопок"""
    buttons = [
        [InlineKeyboardButton(text="🛠 Адмін-панель", callback_data="admin_panel")],
        [
            InlineKeyboardButton(
                text="👨‍💻 Режим користувача", callback_data="user_mode"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_review_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для оставления отзыва"""
    builder = InlineKeyboardBuilder()

    # Кнопка для оставления отзыва прямо в боте
    builder.add(
        InlineKeyboardButton(
            text="⭐ Залишити відгук", callback_data=f"review_{order_id}"
        )
    )

    return builder.as_markup()


def get_rating_keyboard() -> InlineKeyboardMarkup:
    """Инлайн-клавиатура для оценки сервиса"""
    builder = InlineKeyboardBuilder()

    # Кнопки от 1 до 5 звезд
    for rating in range(1, 6):
        stars = "⭐" * rating
        builder.add(InlineKeyboardButton(text=stars, callback_data=f"rating_{rating}"))

    # Размещаем кнопки в ряд
    builder.adjust(5)

    # Кнопка отмены
    builder.row(
        InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_review")
    )

    return builder.as_markup()
