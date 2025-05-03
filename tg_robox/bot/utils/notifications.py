# bot/utils/notifications.py
from aiogram import Bot
from typing import List, Union, Optional
from config.logger import logger


async def notify_admins(bot: Bot, admin_ids: List[int], message: str):
    """Отправка уведомления администраторам"""
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, message)
            logger.info(f"Уведомление отправлено администратору {admin_id}")
        except Exception as e:
            logger.error(
                f"Не удалось отправить сообщение администратору {admin_id}: {e}"
            )


async def send_card_code(bot: Bot, user_id: int, card_code: str, card_value: str):
    """Отправка кода карты пользователю после успешной оплаты"""
    message = (
        f"✅ <b>Оплата успешно завершена!</b>\n\n"
        f"💳 Номинал карты: ${card_value}\n"
        f"🔑 Код карты: <code>{card_code}</code>\n\n"
        f"Спасибо за покупку! Будем рады видеть вас снова."
    )

    try:
        await bot.send_message(user_id, message, parse_mode="HTML")
        logger.info(f"Код карты отправлен пользователю {user_id}")
        return True
    except Exception as e:
        logger.error(f"Не удалось отправить код карты пользователю {user_id}: {e}")
        return False


async def send_order_status_update(
    bot: Bot,
    user_id: int,
    order_id: int,
    status: str,
    additional_info: Optional[str] = None,
):
    """Отправка обновления статуса заказа пользователю"""
    status_emoji = {
        "created": "🕒",
        "paid": "✅",
        "completed": "✅",
        "canceled": "❌",
        "failed": "❌",
    }.get(status, "❓")

    message = (
        f"{status_emoji} <b>Обновление статуса заказа #{order_id}</b>\n\n"
        f"Новый статус: <b>{status.capitalize()}</b>\n"
    )

    if additional_info:
        message += f"\n{additional_info}\n"

    try:
        await bot.send_message(user_id, message, parse_mode="HTML")
        logger.info(
            f"Обновление статуса заказа #{order_id} отправлено пользователю {user_id}"
        )
        return True
    except Exception as e:
        logger.error(
            f"Не удалось отправить обновление статуса заказа пользователю {user_id}: {e}"
        )
        return False


async def send_error_notification(bot: Bot, chat_id: int, error_message: str):
    """Отправка уведомления об ошибке пользователю"""
    message = (
        f"❌ <b>Произошла ошибка</b>\n\n"
        f"{error_message}\n\n"
        f"Пожалуйста, обратитесь в поддержку или попробуйте позже."
    )

    try:
        await bot.send_message(chat_id, message, parse_mode="HTML")
        return True
    except Exception as e:
        logger.error(
            f"Не удалось отправить уведомление об ошибке пользователю {chat_id}: {e}"
        )
        return False


async def broadcast_message(
    bot: Bot, user_ids: List[int], message: str, parse_mode: str = "HTML"
):
    """Массовая рассылка сообщений пользователям"""
    successful = 0
    failed = 0

    for user_id in user_ids:
        try:
            await bot.send_message(user_id, message, parse_mode=parse_mode)
            successful += 1
        except Exception as e:
            logger.error(f"Не удалось отправить рассылку пользователю {user_id}: {e}")
            failed += 1

    logger.info(f"Рассылка завершена. Успешно: {successful}, Неудачно: {failed}")
    return successful, failed
