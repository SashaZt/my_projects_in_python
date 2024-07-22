import telebot
from datetime import datetime, timedelta, time as dtime
import logging
from config import TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения временных меток последней проверки
last_check_time = {}
# Словарь для хранения количества отправленных сообщений за день
daily_message_count = {}


def can_send_message(user_id):
    """Проверка, может ли быть отправлено сообщение"""
    now = datetime.now()
    if not (dtime(8, 0) <= now.time() <= dtime(20, 0)):
        return False

    last_sent = last_check_time.get(user_id)
    if last_sent and now - last_sent < timedelta(hours=1):
        return False

    count = daily_message_count.get(user_id, 0)
    if count >= 3:
        return False

    return True


def send_trial_end_message(user_id):
    """Отправка сообщения о завершении пробного периода"""
    message = (
        "Ваше пробне время закінчилось, для отримання повідомлень оформіть підписку."
    )
    try:
        bot.send_message(user_id, message)
        logger.info(f"Sent trial period ended message to user {user_id}")
        last_check_time[user_id] = datetime.now()
        daily_message_count[user_id] = daily_message_count.get(user_id, 0) + 1
    except telebot.apihelper.ApiException as e:
        logger.error(f"Failed to send message to user {user_id}: {e}")


async def check_and_send_trial_end_messages():
    from send_messages_asio import (
        get_traders,
    )  # Импортировать здесь, чтобы избежать циклического импорта

    logger.info("Проверка и отправка сообщений о завершении пробного периода")
    traders = await get_traders()
    current_time = datetime.now()

    for trader in traders:
        user_id, role, signup, trial_duration, region, material = trader
        signup_time = signup  # signup уже является datetime объектом
        end_trial_time = signup_time + timedelta(seconds=trial_duration)

        logger.info(f"Проверка трейдера {user_id} на окончание пробного периода")

        if (
            current_time > end_trial_time - timedelta(days=1)
            and current_time <= end_trial_time
            and can_send_message(user_id)
        ):
            send_trial_end_message(user_id)
