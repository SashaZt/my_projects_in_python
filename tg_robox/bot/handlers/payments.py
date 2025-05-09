from aiogram import Router, F
from aiogram.types import PreCheckoutQuery, Message, LabeledPrice, SuccessfulPayment
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db.models import Order, Payment, RobloxProduct, CardCode, User
from config.logger import logger
from utils.payment_logging import log_payment_event
from datetime import datetime
from keyboards import inline as ikb


router = Router()


@router.pre_checkout_query()
async def pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery, session: AsyncSession
):
    """Обработчик предварительной проверки платежа"""
    try:
        # Получаем информацию о заказе из payload
        payload = pre_checkout_query.invoice_payload
        parts = payload.split("_")
        order_id = int(parts[1]) if len(parts) > 1 else None
        user_id = pre_checkout_query.from_user.id

        # Логируем проверку платежа
        log_payment_event(
            event_type="pre_checkout",
            user_id=user_id,
            order_id=order_id,
            payment_data={
                "invoice_payload": payload,
                "total_amount": pre_checkout_query.total_amount,
                "currency": pre_checkout_query.currency,
            },
        )

        # Проверяем, существует ли заказ
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            log_payment_event(
                event_type="pre_checkout_order_not_found",
                user_id=user_id,
                order_id=order_id,
            )
            await pre_checkout_query.answer(
                ok=False, error_message="Замовлення не знайдено!"
            )
            return

        # Проверяем, что статус заказа "created"
        if order.status != "created":
            log_payment_event(
                event_type="pre_checkout_invalid_order_status",
                user_id=user_id,
                order_id=order_id,
                payment_data={"status": order.status},
            )
            await pre_checkout_query.answer(
                ok=False, error_message="Замовлення вже оброблено або скасовано."
            )
            return

        # Проверяем наличие достаточного количества кодов
        stmt = select(RobloxProduct).where(RobloxProduct.product_id == order.product_id)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            log_payment_event(
                event_type="pre_checkout_product_not_found",
                user_id=user_id,
                order_id=order_id,
                payment_data={"product_id": order.product_id},
            )
            await pre_checkout_query.answer(
                ok=False, error_message="Продукт не знайдено!"
            )
            return

        stmt = (
            select(CardCode)
            .where(CardCode.card_value == product.card_value, CardCode.is_used == False)
            .limit(product.card_count)
        )
        result = await session.execute(stmt)
        available_codes = result.scalars().all()

        if len(available_codes) < product.card_count:
            log_payment_event(
                event_type="pre_checkout_not_enough_codes",
                user_id=user_id,
                order_id=order_id,
                payment_data={
                    "available": len(available_codes),
                    "required": product.card_count,
                },
            )
            await pre_checkout_query.answer(
                ok=False,
                error_message=f"Недостатньо карток на складі ({len(available_codes)}/{product.card_count})!",
            )
            return

        # Все проверки пройдены, разрешаем платеж
        log_payment_event(
            event_type="pre_checkout_success", user_id=user_id, order_id=order_id
        )
        await pre_checkout_query.answer(ok=True)

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при предварительной проверке платежа: {error_msg}")
        log_payment_event(
            event_type="pre_checkout_error",
            user_id=pre_checkout_query.from_user.id,
            order_id=order_id if "order_id" in locals() else None,
            payment_data={"error": error_msg, "error_type": type(e).__name__},
        )
        await pre_checkout_query.answer(
            ok=False, error_message="Сталася помилка. Спробуйте пізніше."
        )


@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession):
    """Обработчик успешного платежа"""
    try:
        payment_info = message.successful_payment
        payload = payment_info.invoice_payload
        parts = payload.split("_")
        order_id = int(parts[1]) if len(parts) > 1 else None
        user_id = message.from_user.id

        # Логируем успешную оплату
        log_payment_event(
            event_type="payment_success",
            user_id=user_id,
            order_id=order_id,
            payment_data={
                "currency": payment_info.currency,
                "total_amount": payment_info.total_amount,
                "invoice_payload": payload,
                "telegram_payment_charge_id": payment_info.telegram_payment_charge_id,
                "provider_payment_charge_id": payment_info.provider_payment_charge_id,
            },
        )

        # Получаем заказ
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            log_payment_event(
                event_type="payment_success_order_not_found",
                user_id=user_id,
                order_id=order_id,
            )
            await message.answer(
                "❌ Оплата пройшла успішно, але замовлення не знайдено.\n"
                "Наш менеджер зв'яжеться з вами найближчим часом."
            )
            return

        # Получаем продукт
        stmt = select(RobloxProduct).where(RobloxProduct.product_id == order.product_id)
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            log_payment_event(
                event_type="payment_success_product_not_found",
                user_id=user_id,
                order_id=order_id,
                payment_data={"product_id": order.product_id},
            )
            await message.answer(
                "❌ Оплата пройшла успішно, але виникла проблема з видачею коду.\n"
                "Наш менеджер зв'яжеться з вами найближчим часом."
            )
            return

        # Обновляем статус заказа и платежа
        order.status = "paid"

        stmt = select(Payment).where(Payment.order_id == order.order_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = "success"
            payment.payment_date = datetime.now()
            payment.transaction_id = payment_info.telegram_payment_charge_id

        # Получаем необходимое количество свободных кодов карт
        stmt = (
            select(CardCode)
            .where(CardCode.card_value == product.card_value, CardCode.is_used == False)
            .limit(product.card_count)
        )
        result = await session.execute(stmt)
        card_codes = result.scalars().all()

        log_payment_event(
            event_type="payment_codes_found",
            user_id=user_id,
            order_id=order_id,
            payment_data={
                "codes_found": len(card_codes),
                "codes_required": product.card_count,
            },
        )

        if len(card_codes) < product.card_count:
            logger.error(f"Недостаточно карт после оплаты для заказа #{order_id}!")
            log_payment_event(
                event_type="payment_success_not_enough_codes",
                user_id=user_id,
                order_id=order_id,
                payment_data={
                    "available": len(card_codes),
                    "required": product.card_count,
                },
            )
            await message.answer(
                "❌ Оплата пройшла успішно, але виникла проблема з видачею коду.\n"
                "Наш менеджер зв'яжеться з вами найближчим часом."
            )
            return

        # Привязываем коды к заказу
        codes_text = ""
        issued_codes = []
        for card_code in card_codes:
            card_code.is_used = True
            card_code.order_id = order.order_id
            card_code.used_at = datetime.now()
            order.cards_issued += 1
            codes_text += f"🔑 <code>{card_code.code}</code>\n"
            issued_codes.append(card_code.code)

        # Если все коды выданы, помечаем заказ как завершенный
        if order.cards_issued >= order.cards_required:
            order.status = "completed"
            order.completed_at = datetime.now()

        await session.commit()

        log_payment_event(
            event_type="payment_codes_issued",
            user_id=user_id,
            order_id=order_id,
            payment_data={
                "codes_issued": order.cards_issued,
                "order_status": order.status,
            },
        )

        if "premium" not in product.name.lower():
            # Обычные карты
            await message.answer(
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
                "Код обов'язково потрібно активувати через сайт http://roblox.com/redeem ❗️❗️❗️"
            )
        else:
            # Премиум карты
            await message.answer(
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
                "8. Натисніть Cancel Renewal ❗️❗️❗️"
            )
        await message.answer(
            "Дякуємо за покупку! Будемо вдячні, якщо ви залишите відгук про наш сервіс.",
            reply_markup=ikb.get_review_keyboard(order.order_id),
        )
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при обработке успешного платежа: {error_msg}")
        log_payment_event(
            event_type="payment_success_processing_error",
            user_id=message.from_user.id,
            order_id=order_id if "order_id" in locals() else None,
            payment_data={"error": error_msg, "error_type": type(e).__name__},
        )
        await message.answer(
            "❌ Виникла помилка при обробці платежу.\n"
            "Будь ласка, зверніться до підтримки з номером вашого замовлення."
        )


@router.message(Command("cancel_payment"))
async def cancel_payment(message: Message, state: FSMContext, session: AsyncSession):
    """Обработчик команды отмены платежа"""
    try:
        # Получаем текущее состояние
        state_data = await state.get_data()
        order_id = state_data.get("order_id")

        if not order_id:
            await message.answer("У вас немає активних замовлень для скасування.")
            return

        # Получаем заказ
        stmt = select(Order).where(Order.order_id == order_id)
        result = await session.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            await message.answer("Замовлення не знайдено.")
            return

        # Проверяем статус заказа
        if order.status != "created":
            await message.answer(
                f"Замовлення #{order_id} не може бути скасовано, оскільки має статус '{order.status}'."
            )
            return

        # Отменяем заказ
        order.status = "cancelled"

        # Обновляем статус платежа
        stmt = select(Payment).where(Payment.order_id == order.order_id)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = "cancelled"

        await session.commit()

        # Логируем отмену заказа
        log_payment_event(
            event_type="payment_cancelled",
            user_id=message.from_user.id,
            order_id=order_id,
        )

        # Очищаем состояние
        await state.clear()

        await message.answer(f"✅ Замовлення #{order_id} успішно скасовано.")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при отмене платежа: {error_msg}")
        log_payment_event(
            event_type="payment_cancel_error",
            user_id=message.from_user.id,
            order_id=order_id if "order_id" in locals() else None,
            payment_data={"error": error_msg, "error_type": type(e).__name__},
        )
        await message.answer("❌ Сталася помилка при скасуванні замовлення.")
