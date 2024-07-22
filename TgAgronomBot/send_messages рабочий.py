import mysql.connector
import telebot
from datetime import datetime, timedelta
import logging
from config import DB_CONFIG, TOKEN
import time
import schedule

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения временных меток последней проверки
last_check_time = {}


def create_connection():
    return mysql.connector.connect(**DB_CONFIG)


def get_traders():
    query = """
    SELECT 
        u.user_id,
        u.role,
        u.signup,
        u.trial_duration,
        r.region_name,
        m.material_name
    FROM 
        users_tg_bot u
    JOIN 
        user_regions ur ON u.user_id = ur.user_id
    JOIN 
        regions r ON ur.region_id = r.region_id
    JOIN 
        user_raw_materials urm ON u.user_id = urm.user_id
    JOIN 
        raw_materials m ON urm.material_id = m.material_id
    WHERE
        u.role = 'trader';
    """
    try:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query)
                traders = cursor.fetchall()
        return traders
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        return []


def get_new_messages(trader, check_time):
    user_id, role, signup, trial_duration, region, material = trader
    query = """
    SELECT
        Messages, data_time
    FROM
        messages_tg
    WHERE
        data_time > %s AND
        FIND_IN_SET(%s, Regions) > 0 AND
        FIND_IN_SET(%s, Raw_Materials) > 0 AND
        trade = 'sell';
    """
    try:
        with create_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (check_time, region, material))
                messages = cursor.fetchall()
        if messages:
            logger.info(f"New messages for user {user_id}: {messages}")
        # else:
        # logger.info(
        #     f"No new messages for user {user_id} with region {region} and material {material} since {check_time}"
        # )
        return messages
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        return []


def send_messages_to_traders():
    traders = get_traders()
    current_time = datetime.now()
    for trader in traders:
        user_id, role, signup, trial_duration, region, material = trader
        signup_time = signup  # signup уже является datetime объектом
        end_trial_time = signup_time + timedelta(seconds=trial_duration)

        if current_time > end_trial_time:
            message = "Ваше пробне время закінчилось, для отримання повідомлень оформіть підписку."
            try:
                bot.send_message(user_id, message)
                logger.info(f"Sent trial period ended message to user {user_id}")
            except telebot.apihelper.ApiException as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
        else:
            check_time = last_check_time.get(user_id, signup_time)
            messages = get_new_messages(trader, check_time)
            if messages:
                for message in messages:
                    try:
                        bot.send_message(user_id, message[0])
                        logger.info(f"Sent message to user {user_id}: {message[0]}")
                        # Обновляем время последней проверки на время последнего сообщения
                        last_check_time[user_id] = message[1]
                    except telebot.apihelper.ApiException as e:
                        logger.error(f"Failed to send message to user {user_id}: {e}")
            # else:
            #     logger.info(f"No new messages to send to user {user_id}")


if __name__ == "__main__":
    # Используем schedule для планирования задач
    schedule.every(10).seconds.do(send_messages_to_traders)

    while True:
        schedule.run_pending()
        time.sleep(1)
