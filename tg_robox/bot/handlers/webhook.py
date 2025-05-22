# handlers/webhook.py
from datetime import datetime

from aiogram import Bot, Router
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web
from config.logger import logger
from db.database import get_session_maker
from db.models import CardCode, Order, Payment, RobloxProduct
from keyboards import inline as ikb
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from utils.payment_logging import log_payment_event

from config.config import Config

# Создаем Router для веб-хуков
router = Router()  # Это изменение: переименовываем webhook_router в router


async def monobank_webhook_handler(request):
    """Обработчик вебхуков от Monobank"""
    try:
        # Получаем данные запроса
        data = await request.json()
        logger.info(f"Получен вебхук от Monobank: {data}")

        # Извлекаем информацию о платеже
        invoice_id = data.get("invoiceId")
        status = data.get("status")
        reference = data.get("reference")  # Это ID заказа

        if not all([invoice_id, status, reference]):
            logger.error("Отсутствуют обязательные поля в вебхуке Monobank")
            return web.json_response(
                {"status": "error", "message": "Missing required fields"}, status=400
            )

        # Получаем ID заказа
        try:
            order_id = int(reference)
        except ValueError:
            logger.error(f"Некорректный ID заказа в вебхуке Monobank: {reference}")
            return web.json_response(
                {"status": "error", "message": "Invalid order ID"}, status=400
            )

        # Создаем сессию базы данных
        config = Config.load()
        engine = create_async_engine(config.db.get_connection_string())
        session_maker = get_session_maker(engine)

        async with session_maker() as session:
            # Получаем информацию о заказе
            stmt = select(Order).where(Order.order_id == order_id)
            result = await session.execute(stmt)
            order = result.scalar_one_or_none()

            if not order:
                logger.error(f"Заказ не найден: {order_id}")
                return web.json_response(
                    {"status": "error", "message": "Order not found"}, status=404
                )

            # Логируем событие вебхука
            log_payment_event(
                event_type=f"monobank_webhook_{status}",
                user_id=order.user_id,
                order_id=order_id,
                payment_data=data,
            )

            # Обновляем информацию о платеже
            stmt = select(Payment).where(Payment.order_id == order_id)
            result = await session.execute(stmt)
            payment = result.scalar_one_or_none()

            if not payment:
                logger.error(f"Платеж не найден для заказа: {order_id}")
                return web.json_response(
                    {"status": "error", "message": "Payment not found"}, status=404
                )

            # Проверяем статус платежа
            if status == "success":
                # Обработка успешной оплаты
                payment.status = "success"
                payment.payment_date = datetime.now()
                payment.payment_data = data  # Сохраняем данные вебхука
                order.status = "paid"

                # Получаем информацию о продукте
                stmt = select(RobloxProduct).where(
                    RobloxProduct.product_id == order.product_id
                )
                result = await session.execute(stmt)
                product = result.scalar_one_or_none()

                if not product:
                    logger.error(f"Продукт не найден для заказа: {order_id}")
                    return web.json_response(
                        {"status": "error", "message": "Product not found"}, status=404
                    )

                # Получаем необходимое количество свободных кодов карт
                stmt = (
                    select(CardCode)
                    .where(
                        CardCode.card_value == product.card_value,
                        CardCode.is_used == False,
                    )
                    .limit(product.card_count)
                )
                result = await session.execute(stmt)
                card_codes = result.scalars().all()

                if len(card_codes) < product.card_count:
                    logger.error(f"Недостаточно карт для заказа: {order_id}")
                    return web.json_response(
                        {"status": "error", "message": "Not enough card codes"},
                        status=400,
                    )

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

                # Отправляем сообщение пользователю
                bot = Bot(token=config.bot.token)

                try:
                    if "premium" not in product.name.lower():
                        # Обычные карты
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
                        # Премиум карты
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

                    # Отправляем предложение оставить отзыв
                    review_keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="⭐ Залишити відгук",
                                    callback_data=f"review_{order.order_id}",
                                )
                            ]
                        ]
                    )

                    await bot.send_message(
                        order.user_id,
                        "Дякуємо за покупку! Будемо вдячні, якщо ви залишите відгук про наш сервіс.",
                        reply_markup=review_keyboard,
                    )

                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке сообщения пользователю после успешной оплаты: {e}"
                    )

                finally:
                    await bot.session.close()

            elif status == "failure" or status == "expired":
                # Обработка неудачной оплаты или истечения срока действия
                payment.status = "failed"
                payment.payment_data = data  # Сохраняем данные вебхука
                order.status = "canceled"
                await session.commit()

                # Отправляем сообщение пользователю
                try:
                    bot = Bot(token=config.bot.token)
                    await bot.send_message(
                        order.user_id,
                        "❌ На жаль, оплата не пройшла або термін дії рахунку закінчився.\n"
                        "Ви можете спробувати оплатити замовлення знову, створивши новий заказ.",
                    )
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке сообщения пользователю после неудачной оплаты: {e}"
                    )
                finally:
                    await bot.session.close()

            elif status == "processing":
                # Платеж в процессе обработки
                payment.status = "processing"
                payment.payment_data = data  # Сохраняем данные вебхука
                await session.commit()

                # Можно отправить пользователю сообщение о том, что платеж обрабатывается
                try:
                    bot = Bot(token=config.bot.token)
                    await bot.send_message(
                        order.user_id,
                        "⏳ Ваш платіж обробляється. Це може зайняти кілька хвилин.\n"
                        "Ми повідомимо вас, коли оплата буде підтверджена.",
                    )
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке сообщения о обработке платежа: {e}"
                    )
                finally:
                    await bot.session.close()

            # Отправляем успешный ответ в любом случае
            return web.json_response({"status": "success"})

    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука Monobank: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


# Настройка маршрутов веб-сервера для обработки вебхуков
def setup_webhook_routes(app):
    """Настройка маршрутов для обработки вебхуков"""
    config = Config.load()

    # Получаем путь для вебхука Monobank из конфигурации
    if hasattr(config, "monobank") and config.monobank.webhook_url:
        # Извлекаем путь из полного URL
        webhook_url = config.monobank.webhook_url
        # Извлекаем последнюю часть пути
        if "/" in webhook_url:
            webhook_path = webhook_url.split("/")[-1]
        else:
            webhook_path = webhook_url

        # Если путь не начинается с /, добавляем его
        if not webhook_path.startswith("/"):
            webhook_path = f"/{webhook_path}"

        # Регистрируем обработчик для пути вебхука
        app.router.add_post(webhook_path, monobank_webhook_handler)
        logger.info(f"Зарегистрирован вебхук Monobank по пути: {webhook_path}")

    return app


# Функция для запуска веб-сервера вебхуков
async def start_webhook_server():
    """Запуск веб-сервера для обработки вебхуков"""
    config = Config.load()

    # Проверяем, настроен ли вебхук Monobank
    if not hasattr(config, "monobank") or not config.monobank.webhook_url:
        logger.info("Вебхук Monobank не настроен, сервер вебхуков не запускается")
        return None

    # Создаем приложение aiohttp
    app = web.Application()

    # Настраиваем маршруты для обработки вебхуков
    app = setup_webhook_routes(app)

    # Запускаем веб-сервер
    runner = web.AppRunner(app)
    await runner.setup()

    # Получаем порт из конфигурации или используем порт по умолчанию
    webhook_port = (
        config.monobank.webhook_port
        if hasattr(config.monobank, "webhook_port")
        else 8080
    )

    # Запускаем сайт
    site = web.TCPSite(runner, "0.0.0.0", webhook_port)
    await site.start()
    logger.info(f"Веб-сервер для вебхуков запущен на порту {webhook_port}")

    return runner
