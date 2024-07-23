import telebot
from datetime import datetime, timedelta, time as dtime
import logging
import schedule
from config import TOKEN
import time
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения временных меток последней проверки
last_check_time = {}
# Словарь для хранения количества отправленных сообщений за день
daily_message_count = {}
# Словарь для хранения отправленных сообщений
user_messages = {}


def can_send_message(user_id):
    """Проверка, может ли быть отправлено сообщение"""
    now = datetime.now()
    if not (dtime(8, 0) <= now.time() <= dtime(20, 0)):
        return False

    last_sent = last_check_time.get(user_id)
    if last_sent and now - last_sent < timedelta(minutes=1):
        return False

    count = daily_message_count.get(user_id, 0)
    if count >= 20:
        return False

    return True


def tarif_markup():
    markup = telebot.types.InlineKeyboardMarkup(row_width=3)
    basic_button = telebot.types.InlineKeyboardButton(
        text="Базовый", callback_data="tarif_basic"
    )
    standard_button = telebot.types.InlineKeyboardButton(
        text="Стандартный", callback_data="tarif_standard"
    )
    extra_button = telebot.types.InlineKeyboardButton(
        text="Экстра", callback_data="tarif_extra"
    )
    markup.add(basic_button, standard_button, extra_button)
    return markup


def send_trial_end_message(user_id):
    """Отправка сообщения о завершении пробного периода"""
    message = (
        "Ваше пробне время закінчилось, для отримання повідомлень оформіть підписку.\n"
        "🌾БАЗОВИЙ ПЛАН\n"
        "- Доступ до інформації про 1 культуру\n"
        "- Доступ до пропозицій з 1 регіону\n"
        "- Щоденні оновлення\n"
        "💰780 грн. /місяць\n\n"
        "🌽СТАНДАРТ (Найпопулярніший)\n"
        "- Доступ до інформації про 5 культур\n"
        "- Доступ до пропозицій з 3 регіону\n"
        "- Щоденні оновлення\n"
        "💰1985 грн. /місяць\n\n"
        "🌱ЕКСТРА\n"
        "- Доступ до інформації про необмежену кількість культур\n"
        "- Доступ до пропозицій з необмеженої кількості регіонів\n"
        "- Щоденні оновлення\n"
        "💰3890 грн. /місяць\n\n"
        "Який з тарифів підходить під ваши потреби?\n"
        "👇👇ОБЕРІТЬ👇👇"
    )
    try:
        sent_message = bot.send_message(user_id, message, reply_markup=tarif_markup())
        logger.info(f"Sent trial period ended message to user {user_id}")
        last_check_time[user_id] = datetime.now()
        daily_message_count[user_id] = daily_message_count.get(user_id, 0) + 1
        user_messages[user_id] = [sent_message.message_id]
    except telebot.apihelper.ApiException as e:
        logger.error(f"Failed to send message to user {user_id}: {e}")


def check_and_send_trial_end_messages():
    from send_messages_asio import get_traders

    logger.info("Запуск проверки и отправки сообщений о завершении пробного периода")
    # traders = get_traders()
    traders = asyncio.run(get_traders())

    current_time = datetime.now()

    for trader in traders:
        user_id, role, signup, trial_duration, region, material = trader
        signup_time = signup
        end_trial_time = signup_time + timedelta(seconds=trial_duration)

        logger.info(f"Проверка трейдера {user_id} на окончание пробного периода")

        if (
            current_time > end_trial_time - timedelta(days=1)
            and current_time <= end_trial_time
            and can_send_message(user_id)
        ):
            logger.info(f"Отправка сообщения трейдеру {user_id}")
            send_trial_end_message(user_id)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    logger.info(f"Обработка callback: {call.data}")
    if call.data == "tarif_basic":
        message_basic = (
            "Ви обрали:\n"
            "🌾БАЗОВИЙ ПЛАН\n"
            "- Доступ до інформації про 1 культуру\n"
            "- Доступ до пропозицій з 1 регіону\n"
            "- Щоденні оновлення\n"
            "💰780 грн. /місяць\n\n"
            "Реквізити для оплати тарифів:\n"
            "💳 Приват Банк\n"
            "5457 0822 5614 6379\n"
            "Одержувач: Стеценко Данило\n"
            "Після оплати написати з чеком: @AgroHelper_supp"
        )
        bot.send_message(call.message.chat.id, message_basic)
        logger.info(f"Отправлено сообщение: {message_basic}")
    elif call.data == "tarif_standard":
        message_standard = (
            "Ви обрали:\n"
            "🌽СТАНДАРТ (Найпопулярніший)\n"
            "- Доступ до інформації про 5 культур\n"
            "- Доступ до пропозицій з 3 регіону\n"
            "- Щоденні оновлення\n"
            "💰1985 грн. /місяць\n\n"
            "Реквізити для оплати тарифів:\n"
            "💳 Приват Банк\n"
            "5457 0822 5614 6379\n"
            "Одержувач: Стеценко Данило\n"
            "Після оплати написати з чеком: @AgroHelper_supp"
        )
        bot.send_message(call.message.chat.id, message_standard)
        logger.info(f"Отправлено сообщение: {message_standard}")
    elif call.data == "tarif_extra":
        message_extra = (
            "Ви обрали:\n"
            "🌱ЕКСТРА\n"
            "- Доступ до інформації про необмежену кількість культур\n"
            "- Доступ до пропозицій з необмеженої кількості регіонів\n"
            "- Щоденні оновлення\n"
            "💰3890 грн. /місяць\n\n"
            "Реквізити для оплати тарифів:\n"
            "💳 Приват Банк\n"
            "5457 0822 5614 6379\n"
            "Одержувач: Стеценко Данило\n"
            "Після оплати написати з чеком: @AgroHelper_supp"
        )
        bot.send_message(call.message.chat.id, message_extra)
        logger.info(f"Отправлено сообщение: {message_extra}")


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    logger.info("Запускаем main")
    schedule.every(1).minute.do(check_and_send_trial_end_messages)

    run_scheduler()


if __name__ == "__main__":
    main()
    bot.polling(none_stop=True)
