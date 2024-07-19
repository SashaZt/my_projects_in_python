import mysql.connector
import telebot
from datetime import datetime, timedelta
import logging
from config import DB_CONFIG, TOKEN
import time

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
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(query)
    traders = cursor.fetchall()
    cursor.close()
    connection.close()
    return traders


def get_new_messages(trader, check_time):
    user_id, role, signup, trial_duration, region, material = trader
    query = """
    SELECT
        Messages
    FROM
        messages_tg
    WHERE
        data_time > %s AND
        FIND_IN_SET(%s, Regions) > 0 AND
        FIND_IN_SET(%s, Raw_Materials) > 0 AND
        trade = 'sell';
    """
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute(query, (check_time, region, material))
    messages = cursor.fetchall()
    cursor.close()
    connection.close()
    if messages:
        logger.info(f"New messages for user {user_id}: {messages}")
    return messages


def send_messages_to_traders():
    traders = get_traders()
    current_time = datetime.now()
    for trader in traders:
        user_id, role, signup, trial_duration, region, material = trader
        signup_time = signup  # signup уже является datetime объектом
        end_trial_time = signup_time + timedelta(seconds=trial_duration)

        if current_time > end_trial_time:
            message = "Ваше пробне время закінчилось, для отримання повідомлень оформіть підписку."
            bot.send_message(user_id, message)
            logger.info(f"Sent trial period ended message to user {user_id}")
        else:
            check_time = last_check_time.get(user_id, signup_time)
            messages = get_new_messages(trader, check_time)
            for message in messages:
                bot.send_message(user_id, message[0])
                logger.info(f"Sent message to user {user_id}: {message[0]}")
            last_check_time[user_id] = (
                current_time  # Обновляем время последней проверки
            )


if __name__ == "__main__":
    while True:
        send_messages_to_traders()
        time.sleep(30)
