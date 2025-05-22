# handlers/but.py
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LabeledPrice, Message
from db.models import CardCode, Order, Payment, RobloxProduct, User
from keyboards import inline as ikb
from keyboards import reply as kb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from utils.monobank import MonobankPayment
from utils.notifications import send_card_code, send_order_status_update
from utils.payment_logging import log_payment_event
from utils.states import BuyCardStates

# Добавляем корневую директорию в PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.logger import logger

from config.config import Config

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
        "Ось доступні Roblox-картки\n"
        "Обери потрібний номінал: 👾\n"
        "Після оплати ти отримаєш код або кілька кодів, які поповнять твій баланс.",
        reply_markup=ikb.get_products_keyboard(products),
    )
    await state.set_state(BuyCardStates.select_product)


import os

from aiogram.types import FSInputFile


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
        .where(CardCode.card_value == 10, CardCode.is_used == False)
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

    # Формируем детали заказа и отправляем как подпись к фото
    caption = (
        f"📄 <b>Деталі замовлення:</b>\n\n"
        f"🎮 {product.name}\n"
        f"💰 Кількість Robux: {product.robux_amount}\n"
        f"💵 Номінал: ${product.card_value} (кількість карток: {product.card_count})\n"
        f"💳 До оплати: {product.price_uah}₴\n\n"
        f"⚠️ Придбані ігрові картки є цифровими товарами.\n"
        f"Повернення коштів не передбачене після покупки.\n"
        f"Оплачуючи, ви погоджуєтеся з умовами покупки."
        f"Для продовження натисніть кнопку 'Оплатити'"
    )

    # Удаляем предыдущее сообщение
    await callback.message.delete()

    # Определяем путь к изображению
    photo_path = f"assets/images/{product.product_id}.jpg"

    try:
        # Проверяем существование файла
        if os.path.exists(photo_path):
            # Отправляем фото с подписью и клавиатурой
            photo = FSInputFile(photo_path)
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=photo,
                caption=caption,
                reply_markup=ikb.get_payment_keyboard(product_id, product.price_uah),
            )
        else:
            # Если фото не найдено, отправляем только текст
            logger.warning(f"Изображение не найдено: {photo_path}")
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text=caption,
                reply_markup=ikb.get_payment_keyboard(product_id, product.price_uah),
            )

    except Exception as e:
        logger.error(f"Ошибка при отправке изображения: {e}")
        # В случае ошибки отправляем только текст
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=caption,
            reply_markup=ikb.get_payment_keyboard(product_id, product.price_uah),
        )

    await state.set_state(BuyCardStates.confirm_payment)


@router.callback_query(BuyCardStates.confirm_payment, F.data.startswith("pay_mono_"))
async def proceed_to_monobank_payment(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Обработчик кнопки 'Оплатити через Monobank'"""
    # Получаем ID продукта и цену из callback_data
    _, _, product_id, price = callback.data.split("_")
    product_id = int(product_id)
    price = float(price)
    user_id = callback.from_user.id

    # Логируем начало процесса оплаты
    log_payment_event(
        event_type="monobank_payment_started",
        user_id=user_id,
        payment_data={
            "product_id": product_id,
            "price": price,
            "callback_data": callback.data,
        },
    )

    # Получаем информацию о продукте
    stmt = select(RobloxProduct).where(RobloxProduct.product_id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        log_payment_event(
            event_type="monobank_product_unavailable",
            user_id=user_id,
            payment_data={"product_id": product_id},
        )
        # Удаляем предыдущее сообщение и отправляем новое
        try:
            await callback.message.delete()
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="❌ Продукт більше не доступний. Будь ласка, почніть покупку спочатку.",
                reply_markup=ikb.get_back_to_menu_keyboard(),
            )
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")
            # Пробуем просто отправить новое сообщение без удаления
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="❌ Продукт більше не доступний. Будь ласка, почніть покупку спочатку.",
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

    log_payment_event(
        event_type="monobank_order_created",
        user_id=user_id,
        order_id=order.order_id,
        payment_data={
            "product_id": product_id,
            "price": price,
            "card_count": product.card_count,
        },
    )

    # Получаем ссылку на бота для редиректа после оплаты
    bot_info = await callback.bot.get_me()
    redirect_url = f"https://t.me/{bot_info.username}?start=order_{order.order_id}"

    # Создаем клиент Monobank и инвойс
    monobank = MonobankPayment()
    amount_kopecks = int(price * 100)  # Переводим в копейки
    description = f"Покупка {product.name} ({product.robux_amount} Robux)"

    # Получаем webhook_url из конфигурации
    config = Config.load()
    webhook_url = config.monobank.webhook_url

    # Создаем инвойс
    invoice_result = await monobank.create_invoice(
        amount=amount_kopecks,
        order_id=order.order_id,
        redirect_url=redirect_url,
        webhook_url=webhook_url,
        description=description,
    )

    if not invoice_result:
        log_payment_event(
            event_type="monobank_invoice_failed",
            user_id=user_id,
            order_id=order.order_id,
        )
        await callback.message.edit_text(
            "❌ Помилка при створенні рахунку. Будь ласка, спробуйте пізніше або виберіть інший спосіб оплати.",
            reply_markup=ikb.get_back_to_products_keyboard(),
        )
        return

    # Получаем ID инвойса и URL для оплаты
    invoice_id = invoice_result.get("invoiceId")
    payment_url = invoice_result.get("pageUrl")

    # Сохраняем информацию о платеже
    stmt = select(Payment).where(Payment.order_id == order.order_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if payment:
        payment.portmone_order_id = (
            invoice_id  # Можно использовать то же поле или добавить новое
        )
        payment.payment_url = payment_url
        payment.payment_data = invoice_result  # Сохраняем все данные о платеже
        await session.commit()

    log_payment_event(
        event_type="monobank_invoice_created",
        user_id=user_id,
        order_id=order.order_id,
        payment_data={
            "invoice_id": invoice_id,
            "payment_url": payment_url,
        },
    )

    # Удаляем предыдущее сообщение и отправляем новое
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Ошибка при удалении сообщения: {e}")

    # Информируем пользователя о переходе к оплате
    await callback.bot.send_message(
        chat_id=callback.message.chat.id,
        text=f"💳 <b>Оплата через Monobank</b>\n\n"
        f"Заказ: #{order.order_id}\n"
        f"Сумма: {price} грн\n\n"
        f"Для оплаты нажмите кнопку ниже и следуйте инструкциям на странице оплаты.\n"
        f"После успешной оплаты вы получите код карты в этом чате.",
        reply_markup=ikb.get_monobank_payment_keyboard(payment_url),
    )

    # Устанавливаем состояние ожидания оплаты
    await state.set_state(BuyCardStates.waiting_payment)
    await callback.answer()


@router.callback_query(BuyCardStates.confirm_payment, F.data.startswith("pay_"))
async def proceed_to_payment(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Обработчик кнопки 'Оплатити'"""
    # Получаем ID продукта и цену из callback_data
    _, product_id, price = callback.data.split("_")
    product_id = int(product_id)
    price = float(price)

    user_id = callback.from_user.id

    # Логируем начало процесса оплаты
    log_payment_event(
        event_type="payment_started",
        user_id=user_id,
        payment_data={
            "product_id": product_id,
            "price": price,
            "callback_data": callback.data,
        },
    )

    # Получаем информацию о продукте
    stmt = select(RobloxProduct).where(RobloxProduct.product_id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        log_payment_event(
            event_type="product_unavailable",
            user_id=user_id,
            payment_data={"product_id": product_id},
        )
        # Удаляем предыдущее сообщение и отправляем новое
        try:
            await callback.message.delete()
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="❌ Продукт більше не доступний. Будь ласка, почніть покупку спочатку.",
                reply_markup=ikb.get_back_to_menu_keyboard(),
            )
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")
            # Пробуем просто отправить новое сообщение без удаления
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="❌ Продукт більше не доступний. Будь ласка, почніть покупку спочатку.",
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

    log_payment_event(
        event_type="order_created",
        user_id=user_id,
        order_id=order.order_id,
        payment_data={
            "product_id": product_id,
            "price": price,
            "card_count": product.card_count,
        },
    )

    # Получаем платежный токен из конфигурации
    config = Config.load()
    provider_token = config.portmone.portmone_token

    if not provider_token:
        log_payment_event(
            event_type="payment_token_missing", user_id=user_id, order_id=order.order_id
        )
        # Удаляем предыдущее сообщение и отправляем новое
        try:
            await callback.message.delete()
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="❌ Платежі тимчасово недоступні. Будь ласка, спробуйте пізніше.",
                reply_markup=ikb.get_back_to_menu_keyboard(),
            )
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="❌ Платежі тимчасово недоступні. Будь ласка, спробуйте пізніше.",
                reply_markup=ikb.get_back_to_menu_keyboard(),
            )
        return

    try:
        # Формируем цену в копейках (минимальная единица = 1 копейка)
        price_in_kopecks = int(price * 100)

        # Готовим данные для инвойса
        invoice_id = str(uuid.uuid4())

        # Сохраняем invoice_id в платеже
        stmt = select(Payment).where(Payment.order_id == order.order_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment:
            payment.portmone_order_id = invoice_id
            await session.commit()
            log_payment_event(
                event_type="invoice_id_saved",
                user_id=user_id,
                order_id=order.order_id,
                payment_data={"invoice_id": invoice_id},
            )

        # Удаляем предыдущее сообщение и отправляем новое
        try:
            await callback.message.delete()
        except Exception as e:
            logger.error(f"Ошибка при удалении сообщения: {e}")

        # Информируем пользователя о переходе к оплате
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text=f"💳 <b>Перехід до оплати</b>\n\n"
            f"Зараз вам буде відправлено платіжну форму.\n"
            f"Після успішної оплати ви отримаєте код картки в цьому чаті.\n\n"
            f"<b>Номер замовлення:</b> #{order.order_id}",
        )

        # Отправляем запрос на создание платежа
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Купівля {product.name}",
            description=f"Замовлення #{order.order_id} - Roblox Gift Card на {product.robux_amount} ROBUX",
            payload=f"order_{order.order_id}_{invoice_id}",
            provider_token=provider_token,
            currency="UAH",
            prices=[LabeledPrice(label=product.name, amount=price_in_kopecks)],
            start_parameter="buy_roblox_card",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False,
            protect_content=True,
        )

        log_payment_event(
            event_type="invoice_sent",
            user_id=user_id,
            order_id=order.order_id,
            payment_data={
                "invoice_id": invoice_id,
                "amount": price,
                "amount_kopecks": price_in_kopecks,
                "product_name": product.name,
                "robux_amount": product.robux_amount,
            },
        )

        # Устанавливаем состояние ожидания оплаты
        await state.set_state(BuyCardStates.waiting_payment)
        await callback.answer()

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при создании платежа: {error_msg}")
        log_payment_event(
            event_type="payment_error",
            user_id=user_id,
            order_id=order.order_id if "order" in locals() else None,
            payment_data={"error": error_msg, "error_type": type(e).__name__},
        )

        # Обработка ошибки - отправка сообщения пользователю
        try:
            # Пробуем удалить предыдущее сообщение
            await callback.message.delete()
        except Exception:
            pass

        # Отправляем сообщение об ошибке
        try:
            await callback.bot.send_message(
                chat_id=callback.message.chat.id,
                text="❌ Сталася помилка при створенні платежу. Будь ласка, спробуйте пізніше.",
                reply_markup=ikb.get_back_to_menu_keyboard(),
            )
        except Exception:
            # В крайнем случае, просто показываем всплывающее уведомление
            await callback.answer(
                "Сталася помилка при створенні платежу. Будь ласка, спробуйте пізніше.",
                show_alert=True,
            )


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

    try:
        # Удаляем текущее сообщение (которое может быть фото)
        await callback.message.delete()

        # Отправляем новое сообщение
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="🛍 <b>Виберіть картку Roblox:</b>\n\n"
            "Ось доступні Roblox-картки.\n"
            "Обери потрібний номінал: 👾\n"
            "Після оплати ти отримаєш код або кілька кодів, які поповнять твій баланс.",
            reply_markup=ikb.get_products_keyboard(products),
        )
    except Exception as e:
        logger.error(f"Ошибка при возврате к выбору продуктов: {e}")
        # Альтернативный вариант - отправить новое сообщение без удаления старого
        await callback.bot.send_message(
            chat_id=callback.message.chat.id,
            text="🛍 <b>Виберіть картку Roblox:</b>\n\n"
            "Ось доступні Roblox-картки.\n"
            "Обери потрібний номінал: 👾\n"
            "Після оплати ти отримаєш код або кілька кодів, які поповнять твій баланс.",
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
        if "premium" not in product.name.lower():
            logger.info(product.name.lower())
            # Отправляем коды пользователю
            await message.bot.send_message(
                order.user_id,
                f"✅ Оплата успішно завершена!\n\n"
                f"🎮 {product.name}\n"
                f"💰 Кількість Robux: {product.robux_amount}\n"
                f"💵 Номінал: ${product.card_value} (кількість карток: {product.card_count})\n\n"
                f"<b>Ваші коди карток:</b>\n"
                + "\n".join(f"🔑 {code}" for code in codes_text.splitlines())
                + "\n\n"
                "Ось відео інструкція як активувати код.\n\n"
                "https://youtu.be/6r9qPBOOzHk\n\n"
                "1. Перейдіть на офіційний сайт гри http://roblox.com/redeem\n"
                "2. Увійдіть до акаунту на якому бажаєте активувати код.\n"
                "3. Уведіть код.\n"
                "4. Підтвердіть активацію.\n"
                "5. Обміняйте баланс на пакет Робуксів в магазині❗️\n\n"
                "Щоб обміняти баланс на Робукси 💰\n"
                'Активуйте код та натисніть на кнопку "Get Robux"\n\n'
                "Код обов'язково потрібно активувати через сайт http://roblox.com/redeem ❗️❗️❗️",
                reply_markup=kb.get_main_menu_keyboard(),
            )

            await message.answer(
                f"✅ Платіж за замовленням #{order_id} оброблений успішно!"
            )
        else:
            await message.bot.send_message(
                order.user_id,
                f"✅ Оплата успішно завершена!\n\n"
                f"🎮 {product.name}\n"
                f"💰 Кількість Robux: {product.robux_amount}\n"
                f"💵 Номінал: ${product.card_value} (кількість карток: {product.card_count})\n\n"
                f"<b>Ваші коди карток:</b>\n"
                + "\n".join(f"🔑 {code}" for code in codes_text.splitlines())
                + "\n\n"
                "ПЕРЕД АКТИВАЦІЄЮ УВАЖНО ПОДИВІТЬСЯ ІНСТРУКЦІЮ ❗️❗️❗️\n\n"
                "Ось відео інструкція як активувати код:\n\n"
                "https://youtu.be/BtiaZTegCSI\n\n"
                "1. Перейдіть на офіційний сайт гри http://roblox.com/redeem\n"
                "2. Увійдіть до акаунту на якому бажаєте активувати код та підписку.\n"
                "3. Потім перейдіть за посиланням\n"
                "https://www.roblox.com/upgrades/redeem?ap=481&pm=redeemCard&selectedUpsellProductId=0\n"
                '4. Вставте наданий код в поле для вводу та натисніть **"Redeem"**"\n'
                "5. Підтвердіть покупку натиснувши **Subscribe!**\n"
                "6. Перейдіть сюди https://www.roblox.com/my/account#!/subscriptions\n"
                "7. Натисніть на вашу підписку\n"
                "8. Натисніть Cancel Renewal ❗❗❗",
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
    await session.flush()  # Используем flush для получения ID заказа

    # Создаем запись о платеже
    payment = Payment(
        order_id=order.order_id,
        amount=price,
        status="pending",
        portmone_order_id=str(uuid.uuid4()),  # Временный ID для Portmone
    )
    session.add(payment)
    await session.commit()

    # Возвращаем заказ
    return order


def generate_payment_url(order_id: int, amount: float) -> str:
    """Генерация URL для оплаты через Portmone (заглушка)"""
    # Здесь должна быть интеграция с Portmone API
    # Пока возвращаем фейковый URL
    return f"https://www.portmone.com.ua/r3/payment?order={order_id}&amount={amount}"
