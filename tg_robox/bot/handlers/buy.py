from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from keyboards import reply as kb
from keyboards import inline as ikb
from utils.states import BuyCardStates
from utils.notifications import send_card_code, send_order_status_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import RobloxProduct, Order, Payment, CardCode, User
import uuid
from datetime import datetime

router = Router()


@router.message(F.text == "🛍 Купити картку")
async def buy_card(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик кнопки 'Купити картку'"""
    # Получаем доступные продукты из БД
    stmt = (
        select(RobloxProduct)
        .where(RobloxProduct.is_available == True)
        .order_by(RobloxProduct.robux_amount)
    )
    result = await session.execute(stmt)
    products = result.scalars().all()

    if not products:
        await message.answer(
            "❌ На жаль, зараз немає доступних карток для покупки. Будь ласка, спробуйте пізніше.",
            reply_markup=kb.get_main_menu_keyboard(),
        )
        return

    # Создаем клавиатуру с доступными продуктами
    await message.answer(
        "🛍 <b>Виберіть картку Roblox:</b>\n\n"
        "У нас є різні номінали карток Roblox з різною кількістю Robux:",
        reply_markup=ikb.get_products_keyboard(products),
    )
    await state.set_state(BuyCardStates.select_product)


@router.callback_query(BuyCardStates.select_product, F.data.startswith("product_"))
async def product_selected(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Обработчик выбора продукта"""
    # Получаем ID продукта из callback_data
    product_id = int(callback.data.split("_")[1])

    # Получаем информацию о продукте из БД
    stmt = select(RobloxProduct).where(RobloxProduct.product_id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        await callback.message.edit_text(
            "❌ Обраний продукт більше не доступний. Будь ласка, виберіть інший.",
            reply_markup=ikb.get_back_to_menu_keyboard(),
        )
        return

    # Сохраняем ID продукта в состоянии
    await state.update_data(product_id=product_id)

    # Проверяем наличие свободных кодов
    stmt = (
        select(CardCode)
        .where(CardCode.card_value == product.card_value, CardCode.is_used == False)
        .limit(product.card_count)
    )
    result = await session.execute(stmt)
    available_codes = result.scalars().all()

    if len(available_codes) < product.card_count:
        await callback.message.edit_text(
            f"❌ На жаль, для цього продукту недостатньо карток на складі ({len(available_codes)}/{product.card_count}).\n"
            f"Будь ласка, виберіть інший продукт або зв'яжіться з підтримкою.",
            reply_markup=ikb.get_back_to_products_keyboard(),
        )
        return

    # Формируем детали заказа
    await callback.message.edit_text(
        f"📄 <b>Деталі замовлення:</b>\n\n"
        f"🎮 {product.name}\n"
        f"💰 Кількість Robux: {product.robux_amount}\n"
        f"💵 Номінал: ${product.card_value} (кількість карток: {product.card_count})\n"
        f"💳 До оплати: {product.price_uah}₴\n\n"
        f"Для продовження натисніть кнопку 'Оплатити'",
        reply_markup=ikb.get_payment_keyboard(product_id, product.price_uah),
    )
    await state.set_state(BuyCardStates.confirm_payment)


@router.callback_query(BuyCardStates.confirm_payment, F.data.startswith("pay_"))
async def proceed_to_payment(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Обработчик кнопки 'Оплатити'"""
    # Получаем ID продукта и цену из callback_data
    _, product_id, price = callback.data.split("_")
    product_id = int(product_id)
    price = float(price)

    # Получаем информацию о продукте
    stmt = select(RobloxProduct).where(RobloxProduct.product_id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        await callback.message.edit_text(
            "❌ Продукт більше не доступний. Будь ласка, почніть покупку спочатку.",
            reply_markup=ikb.get_back_to_menu_keyboard(),
        )
        return

    # Создаем новый заказ
    order = await create_order(
        session,
        user_id=callback.from_user.id,
        product_id=product_id,
        price=price,
        cards_required=product.card_count,
    )

    # Генерируем URL для оплаты (здесь нужна интеграция с Portmone)
    payment_url = generate_payment_url(order.order_id, price)

    # Сохраняем URL в базе
    payment = order.payment
    payment.payment_url = payment_url
    await session.commit()

    # Сохраняем данные заказа в состоянии
    await state.update_data(order_id=order.order_id)

    await callback.message.edit_text(
        f"💳 <b>Перехід до оплати</b>\n\n"
        f"Ви будете перенаправлені на сторінку оплати Portmone.com\n"
        f"Після успішної оплати ви отримаєте код картки в цьому чаті.\n\n"
        f"<b>Номер замовлення:</b> #{order.order_id}",
        reply_markup=ikb.get_payment_url_keyboard(payment_url),
    )
    await state.set_state(BuyCardStates.waiting_payment)


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Назад' в главное меню"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "📋 <b>Головне меню</b>\n\n" "Виберіть потрібний розділ:",
        reply_markup=kb.get_main_menu_keyboard(),
    )


@router.callback_query(F.data == "back_to_products")
async def back_to_products(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Обработчик кнопки 'Назад' к выбору продуктов"""
    # Получаем доступные продукты из БД
    stmt = (
        select(RobloxProduct)
        .where(RobloxProduct.is_available == True)
        .order_by(RobloxProduct.robux_amount)
    )
    result = await session.execute(stmt)
    products = result.scalars().all()

    await callback.message.edit_text(
        "🛍 <b>Виберіть картку Roblox:</b>\n\n"
        "У нас є різні номінали карток Roblox з різною кількістю Robux:",
        reply_markup=ikb.get_products_keyboard(products),
    )
    await state.set_state(BuyCardStates.select_product)


# Обработчик для webhook от платежной системы или симуляции платежа
@router.message(Command("simulate_payment"))
async def simulate_payment(message: Message, session: AsyncSession):
    """Симуляция успешной оплаты (только для тестирования)"""
    try:
        # Извлекаем ID заказа
        order_id = int(message.text.split()[1])

        # Получаем заказ
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            await message.answer("❌ Замовлення не знайдено!")
            return

        # Получаем продукт
        stmt = select(RobloxProduct).where(RobloxProduct.product_id == order.product_id)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            await message.answer("❌ Продукт не знайдено!")
            return

        # Обновляем статус заказа и платежа
        order.status = "paid"
        order.payment.status = "success"
        order.payment.payment_date = datetime.now()

        # Получаем необходимое количество свободных кодов карт
        stmt = (
            select(CardCode)
            .where(CardCode.card_value == product.card_value, CardCode.is_used == False)
            .limit(product.card_count)
        )
        result = await session.execute(stmt)
        card_codes = result.scalars().all()

        if len(card_codes) < product.card_count:
            await message.answer(
                f"❌ Недостатньо карток на складі ({len(card_codes)}/{product.card_count})!"
            )
            return

        # Привязываем коды к заказу
        codes_text = ""
        for card_code in card_codes:
            card_code.is_used = True
            card_code.order_id = order.order_id
            card_code.used_at = datetime.now()
            order.cards_issued += 1
            codes_text += f"🔑 <code>{card_code.code}</code>\n"

        # Если все коды выданы, помечаем заказ как завершенный
        if order.cards_issued >= order.cards_required:
            order.status = "completed"
            order.completed_at = datetime.now()

        await session.commit()

        # Отправляем коды пользователю
        await message.bot.send_message(
            order.user_id,
            f"✅ <b>Оплата успішно завершена!</b>\n\n"
            f"🎮 {product.name}\n"
            f"💰 Кількість Robux: {product.robux_amount}\n"
            f"💵 Номінал: ${product.card_value} (кількість карток: {product.card_count})\n\n"
            f"<b>Ваші коди карток:</b>\n"
            f"{codes_text}\n"
            f"Для активації перейдіть на сайт <a href='https://www.roblox.com/redeem'>roblox.com/redeem</a>\n\n"
            f"Дякуємо за покупку! Будемо раді бачити вас знову.",
            reply_markup=kb.get_main_menu_keyboard(),
        )

        await message.answer(
            f"✅ Платіж за замовленням #{order_id} оброблений успішно!"
        )

    except (ValueError, IndexError):
        await message.answer(
            "❌ Невірний формат команди. Використовуйте: /simulate_payment <order_id>"
        )
    except Exception as e:
        await message.answer(f"❌ Сталася помилка: {e}")


async def create_order(
    session: AsyncSession,
    user_id: int,
    product_id: int,
    price: float,
    cards_required: int,
) -> Order:
    """Создание заказа в базе данных"""
    # Создаем заказ
    order = Order(
        user_id=user_id,
        product_id=product_id,
        status="created",
        cards_required=cards_required,
        cards_issued=0,
        total_price=price,
    )
    session.add(order)
    await session.flush()

    # Создаем запись о платеже
    payment = Payment(
        order_id=order.order_id,
        amount=price,
        status="pending",
        portmone_order_id=str(uuid.uuid4()),  # Временный ID для Portmone
    )
    session.add(payment)
    await session.commit()

    return order


def generate_payment_url(order_id: int, amount: float) -> str:
    """Генерация URL для оплаты через Portmone (заглушка)"""
    # Здесь должна быть интеграция с Portmone API
    # Пока возвращаем фейковый URL
    return f"https://www.portmone.com.ua/r3/payment?order={order_id}&amount={amount}"
