# handlers/but.py
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
import asyncio
from utils.checkbox_payment import CheckboxPayment
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, LabeledPrice, Message
from db.models import CardCode, Order, Payment, RobloxProduct, User
from keyboards import inline as ikb
from keyboards import reply as kb
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# from utils.monobank import MonobankPayment
# from utils.notifications import send_card_code, send_order_status_update
from utils.payment_logging import log_payment_event
from utils.states import BuyCardStates
from db.database import get_session_maker
from db.database import get_session_maker, create_async_engine

import os



# Добавляем корневую директорию в PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent.absolute()
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.logger import logger

from config.config import Config

router = Router()

config = Config.load()
engine = create_async_engine(config.db)
session_maker = get_session_maker(engine)


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
    
    # Определяем путь к видео
    video_stock_path = "assets/images/stock.mp4"
    
    # Текст подписи к видео
    caption = (
        "🛍 <b>Виберіть картку Roblox:</b>\n\n"
        "Ось доступні Roblox-картки\n"
        "Обери потрібний номінал: 👾\n"
        "Після оплати ти отримаєш код або кілька кодів, які поповнять твій баланс."
    )
    
    try:
        # Проверяем существование видеофайла
        if os.path.exists(video_stock_path):
            # Отправляем видео с подписью и клавиатурой
            video = FSInputFile(video_stock_path)
            await message.answer_video(
                video=video,
                caption=caption,
                reply_markup=ikb.get_products_keyboard(products),
            )
        else:
            # Если видео не найдено, отправляем только текст
            logger.warning(f"Видеофайл не найден: {video_stock_path}")
            await message.answer(
                caption,
                reply_markup=ikb.get_products_keyboard(products),
            )
            
    except Exception as e:
        logger.error(f"Ошибка при отправке видео: {e}")
        # В случае ошибки отправляем только текст
        await message.answer(
            caption,
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
    print(products)
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

    # Теперь можно использовать существующие поля
    payment = Payment(
        order_id=order.order_id,
        amount=price,
        status="pending",
        portmone_order_id=None,  # Это поле есть в БД!
    )
    session.add(payment)
    await session.commit()

    return order

async def monitor_checkbox_payment(order_id: int, invoice_id: str, bot, session_maker):
    """Мониторинг статуса платежа Checkbox"""
    checkbox = CheckboxPayment()
    max_attempts = 30  # 5 минут (30 * 10 сек)
    attempt = 0
    
    while attempt < max_attempts:
        try:
            status_result = await checkbox.check_invoice_status(invoice_id)
            
            if status_result:
                status = status_result.get("status")
                logger.info(f"Статус платежа {invoice_id}: {status}")
                
                # SUCCESS - окончательный успешный статус
                if status == "SUCCESS":
                    logger.info(f"Платеж {invoice_id} успешен, отправляем коды")
                    await process_successful_checkbox_payment(order_id, status_result, bot, session_maker)
                    break
                elif status in ["FAILED", "EXPIRED", "CANCELLED", "ERROR"]:
                    await process_failed_checkbox_payment(order_id, status_result, bot, session_maker)
                    break
                # Если CREATED - продолжаем ждать
                
            attempt += 1
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Ошибка мониторинга платежа {invoice_id}: {e}")
            attempt += 1
            await asyncio.sleep(10)
    
    # Если превышено время ожидания
    if attempt >= max_attempts:
        logger.warning(f"Превышено время ожидания для платежа {invoice_id}")
        await process_timeout_checkbox_payment(order_id, bot, session_maker)


@router.callback_query(BuyCardStates.confirm_payment, F.data.startswith("pay_checkbox_"))
async def proceed_to_checkbox_payment(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    """Обработчик оплаты через Checkbox"""
    # Получаем ID продукта и цену из callback_data
    _, _, product_id, price = callback.data.split("_")
    product_id = int(product_id)
    price = float(price)
    user_id = callback.from_user.id

    # ДОБАВИТЬ: Получаем информацию о продукте
    stmt = select(RobloxProduct).where(RobloxProduct.product_id == product_id)
    result = await session.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        await callback.message.edit_text(
            "❌ Продукт більше не доступний.",
            reply_markup=ikb.get_back_to_menu_keyboard(),
        )
        return

    # Создаем новый заказ
    order = await create_order(
        session,
        user_id=user_id,
        product_id=product_id,
        price=price,
        cards_required=product.card_count,
    )

    # Создаем инвойс в Checkbox
    checkbox = CheckboxPayment()
    amount_kopecks = int(price * 100)
    product_name = f"{product.name} ({product.robux_amount} ROBUX)"
    
    invoice_result = await checkbox.create_invoice(
        product_name=product_name,
        amount_kopecks=amount_kopecks,
        order_id=order.order_id
    )

    if not invoice_result:
        try:
            await callback.message.edit_text(
                "❌ Помилка при створенні рахунку. Спробуйте пізніше.",
                reply_markup=ikb.get_back_to_products_keyboard(),
            )
        except Exception:
            # Если не получается редактировать (например, это фото), отправляем новое сообщение
            await callback.message.answer(
                "❌ Помилка при створенні рахунку. Спробуйте пізніше.",
                reply_markup=ikb.get_back_to_products_keyboard(),
            )

    # Сохраняем информацию о платеже - используем СУЩЕСТВУЮЩИЕ поля!
    stmt = select(Payment).where(Payment.order_id == order.order_id)
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()

    if payment:
        payment.portmone_order_id = invoice_result.get("id")  
        payment.payment_url = invoice_result.get("page_url")  
        payment.payment_data = invoice_result              
        await session.commit()

    # Отправляем пользователю ссылку на оплату
    # Отправляем пользователю ссылку на оплату
    try:
        await callback.message.edit_text(
            f"💳 <b>Оплата через Mono Pay</b>\n\n"
            f"Замовлення: #{order.order_id}\n"
            f"Сума: {price} грн\n\n"
            f"⚠️ <b>Важливо!</b> У вас є 2.5 хвилини для оплати.\n"
            f"Натисніть кнопку нижче для переходу до оплати:",
            reply_markup=ikb.get_checkbox_payment_keyboard(invoice_result.get("page_url")),
        )
    except Exception:
        await callback.message.answer(
            f"💳 <b>Оплата через Mono Pay</b>\n\n"
            f"Замовлення: #{order.order_id}\n"
            f"Сума: {price} грн\n\n"
            f"⚠️ <b>Важливо!</b> У вас є 2.5 хвилини для оплати.\n"
            f"Натисніть кнопку нижче для переходу до оплати:",
            reply_markup=ikb.get_checkbox_payment_keyboard(invoice_result.get("page_url")),
        )

    # Запускаем мониторинг статуса платежа
    asyncio.create_task(monitor_checkbox_payment(
        order.order_id, 
        invoice_result.get("id"),
        callback.bot,
        session_maker
    ))

    await state.set_state(BuyCardStates.waiting_payment)
    await callback.answer()
    
async def process_successful_checkbox_payment(order_id: int, status_result: dict, bot, session_maker):
    """Обработка успешного платежа Checkbox"""
    async with session_maker() as session:
        # Получаем заказ
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            logger.error(f"Заказ не найден: {order_id}")
            return

        # Получаем продукт
        stmt = select(RobloxProduct).where(RobloxProduct.product_id == order.product_id)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            logger.error(f"Продукт не найден для заказа: {order_id}")
            return

        # Обновляем статус заказа и платежа
        order.status = "paid"

        stmt = select(Payment).where(Payment.order_id == order.order_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = "success"
            payment.payment_date = datetime.now()
            payment.payment_data = status_result

        # Получаем коды карт
        stmt = (
            select(CardCode)
            .where(CardCode.card_value == product.card_value, CardCode.is_used == False)
            .limit(product.card_count)
        )
        result = await session.execute(stmt)
        card_codes = result.scalars().all()

        if len(card_codes) < product.card_count:
            logger.error(f"Недостаточно карт для заказа: {order_id}")
            return

        # Привязываем коды к заказу
        codes_text = ""
        for card_code in card_codes:
            card_code.is_used = True
            card_code.order_id = order.order_id
            card_code.used_at = datetime.now()
            order.cards_issued += 1
            codes_text += f"🔑 <code>{card_code.code}</code>\n"

        # Завершаем заказ
        if order.cards_issued >= order.cards_required:
            order.status = "completed"
            order.completed_at = datetime.now()

        await session.commit()

        # Отправляем коды пользователю
        if "premium" not in product.name.lower():
            await bot.send_message(
                order.user_id,
                f"✅ Оплата успішно завершена!\n\n"
                f"🎮 {product.name}\n"
                f"💰 Кількість Robux: {product.robux_amount}\n"
                f"💵 Номінал: ${product.card_value} (кількість карток: {product.card_count})\n\n"
                f"<b>Ваші коди карток:</b>\n"
                f"{codes_text}\n\n"
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
            )
        else:
            await bot.send_message(
                order.user_id,
                f"✅ Оплата успішно завершена!\n\n"
                f"🎮 {product.name}\n"
                f"💰 Кількість Robux: {product.robux_amount}\n"
                f"💵 Номінал: ${product.card_value} (кількість карток: {product.card_count})\n\n"
                f"<b>Ваші коди карток:</b>\n"
                f"{codes_text}\n\n"
                "ПЕРЕД АКТИВАЦІЄЮ УВАЖНО ПОДИВІТЬСЯ ІНСТРУКЦІЮ ❗️❗️❗️\n\n"
                "Ось відео інструкція як активувати код:\n\n"
                "https://youtu.be/BtiaZTegCSI\n\n"
                "1. Перейдіть на офіційний сайт гри http://roblox.com/redeem\n"
                "2. Увійдіть до акаунту на якому бажаєте активувати код та підписку.\n"
                "3. Потім перейдіть за посиланням:\n"
                "https://www.roblox.com/upgrades/redeem?ap=481&pm=redeemCard&selectedUpsellProductId=0\n"
                '4. Вставте наданий код в поле для вводу та натисніть **"Redeem"**\n'
                "5. Підтвердіть покупку натиснувши **Subscribe!**\n"
                "6. Перейдіть сюди: https://www.roblox.com/my/account#!/subscriptions\n"
                "7. Натисніть на вашу підписку\n"
                "8. Натисніть Cancel Renewal ❗️❗️❗️",
            )

        # Предлагаем оставить отзыв
        await bot.send_message(
            order.user_id,
            "Дякуємо за покупку! Будемо вдячні, якщо ви залишите відгук про наш сервіс.",
            reply_markup=ikb.get_review_keyboard(order.order_id),
        )

async def process_failed_checkbox_payment(order_id: int, status_result: dict, bot, session_maker):
    """Обработка неудачного платежа Checkbox"""
    async with session_maker() as session:
        # Получаем заказ
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            return

        # Обновляем статус
        order.status = "cancelled"
        
        stmt = select(Payment).where(Payment.order_id == order.order_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = "failed"
            payment.payment_data = status_result

        await session.commit()

        # Уведомляем пользователя
        await bot.send_message(
            order.user_id,
            "❌ На жаль, оплата не пройшла.\n"
            "Ви можете спробувати оплатити замовлення знову.",
        )

async def process_timeout_checkbox_payment(order_id: int, bot, session_maker):
    """Обработка таймаута платежа Checkbox"""
    async with session_maker() as session:
        # Получаем заказ
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            return

        # Обновляем статус
        order.status = "cancelled"
        
        stmt = select(Payment).where(Payment.order_id == order.order_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = "timeout"

        await session.commit()

        # Уведомляем пользователя
        await bot.send_message(
            order.user_id,
            "⏰ Час оплати закінчився.\n"
            "Ви можете створити нове замовлення.",
        )