import mysql.connector
import telebot
from datetime import datetime, timedelta
import logging
from TgAgronomBot.configuration.config import DB_CONFIG, TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения временных меток последней проверки
last_check_time = {}
# Словарь для хранения отправленных сообщений по ID
sent_messages = {}


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
        id, Messages, data_time
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
        return messages
    except mysql.connector.Error as err:
        logger.error(f"Error: {err}")
        return []


def send_messages_to_traders():
    traders = get_traders()
    current_time = datetime.now()
    check_time_threshold = current_time - timedelta(seconds=30)

    for trader in traders:
        user_id, role, signup, trial_duration, region, material = trader
        signup_time = signup  # signup уже является datetime объектом
        end_trial_time = signup_time + timedelta(seconds=trial_duration)

        if current_time <= end_trial_time:
            check_time = last_check_time.get(user_id, signup_time)
            if check_time < check_time_threshold:
                check_time = check_time_threshold

            messages = get_new_messages(trader, check_time)
            if messages:
                for message in messages:
                    message_id, message_text, message_time = message
                    if message_id not in sent_messages.get(user_id, set()):
                        try:
                            bot.send_message(user_id, message_text)
                            logger.info(
                                f"Sent message to user {user_id}: {message_text}"
                            )
                            # Добавляем ID сообщения в список отправленных
                            if user_id not in sent_messages:
                                sent_messages[user_id] = set()
                            sent_messages[user_id].add(message_id)
                            # Обновляем время последней проверки на время последнего сообщения
                            last_check_time[user_id] = max(
                                last_check_time.get(user_id, signup_time), message_time
                            )
                        except telebot.apihelper.ApiException as e:
                            logger.error(
                                f"Failed to send message to user {user_id}: {e}"
                            )
            last_check_time[user_id] = (
                current_time  # Обновляем время проверки даже если нет новых сообщений
            )
