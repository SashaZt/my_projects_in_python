from aiogram import Router, F
from aiogram.types import Message
from keyboards import reply as kb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from db.models import Order, Payment, CardCode, RobloxProduct

router = Router()


@router.message(F.text == "🛍 Мої покупки")
async def my_purchases(message: Message, session: AsyncSession):
    """Обработчик кнопки 'Мої покупки'"""
    user_id = message.from_user.id

    # Получаем заказы пользователя
    stmt = (
        select(Order)
        .options(
            joinedload(Order.product),
            joinedload(Order.payment),
            joinedload(Order.card_codes),
        )
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
    )

    result = await session.execute(stmt)
    orders = result.scalars().all()

    if not orders:
        await message.answer(
            "🛍 <b>Ваші покупки</b>\n\n"
            "У вас поки немає покупок.\n\n"
            "Щоб здійснити покупку, поверніться в головне меню і виберіть 'Купити картку'.",
            reply_markup=kb.get_main_menu_keyboard(),
        )
        return

    # Формируем сообщение с покупками
    purchases_text = "🛍 <b>Ваші покупки</b>\n\n"

    for order in orders:
        status_emoji = {
            "created": "🕒",
            "paid": "✅",
            "completed": "✅",
            "canceled": "❌",
        }.get(order.status, "❓")

        # Форматируем дату в читаемый вид
        date_str = order.created_at.strftime("%d.%m.%Y %H:%M")

        # Добавляем основную информацию о заказе
        purchases_text += (
            f"{status_emoji} <b>Замовлення #{order.order_id}</b>\n" f"📅 {date_str}\n"
        )

        # Добавляем информацию о продукте, если она есть
        if order.product:
            purchases_text += (
                f"🎮 {order.product.name}\n"
                f"💰 Robux: {order.product.robux_amount}\n"
                f"💵 Ціна: {order.total_price}₴\n"
            )

        # Добавляем статус заказа
        purchases_text += f"📊 Статус: {get_status_text(order.status)}\n"

        # Если заказ оплачен или завершен, показываем коды карт
        if order.status in ["paid", "completed"] and order.card_codes:
            purchases_text += f"🔑 Коди карток:\n"
            for code in order.card_codes:
                purchases_text += f"<code>{code.code}</code>\n"

        purchases_text += "\n"

    await message.answer(purchases_text, reply_markup=kb.get_main_menu_keyboard())


def get_status_text(status: str) -> str:
    """Возвращает текст статуса на украинском языке"""
    status_texts = {
        "created": "Створено",
        "paid": "Оплачено",
        "completed": "Завершено",
        "canceled": "Скасовано",
    }
    return status_texts.get(status, status)
