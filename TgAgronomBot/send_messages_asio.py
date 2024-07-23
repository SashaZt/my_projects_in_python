import aiomysql
import asyncio
from telebot.async_telebot import AsyncTeleBot
from datetime import datetime, timedelta
import logging
import schedule
from config import DB_CONFIG, TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
bot = AsyncTeleBot(TOKEN)

# Словарь для хранения временных меток последней проверки
last_check_time = {}
# Словарь для хранения отправленных сообщений по ID
sent_messages = {}


# Подключение к БД
async def create_connection():
    return await aiomysql.connect(
        host=DB_CONFIG["host"],
        port=3306,  # Укажите порт, если он отличается
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        db=DB_CONFIG["database"],
    )


#
async def get_traders():
    # logger.info("Получение списка трейдеров")
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
        conn = await create_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(query)
            traders = await cursor.fetchall()
        conn.close()
        return traders
    except aiomysql.Error as err:
        logger.error(f"Ошибка при получении трейдеров: {err}")
        return []


async def get_new_messages(trader, check_time):
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
        conn = await create_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(query, (check_time, region, material))
            messages = await cursor.fetchall()
        conn.close()
        if messages:
            logger.info(f"Новые сообщения для {user_id}")
            # logger.info(f"Новые сообщения для {user_id}: {messages}")
        return messages
    except aiomysql.Error as err:
        logger.error(f"Ошибка при получении новых сообщений для {user_id}: {err}")
        return []


async def send_message(user_id, message_text):
    # logger.info(f"Отправка сообщения пользователю {user_id}: {message_text}")
    try:
        await bot.send_message(user_id, message_text)
        logger.info(f"Сообщение пользователю {user_id} отправлено успешно")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")


async def send_messages_to_traders():
    # logger.info("Отправка сообщений трейдерам")
    traders = await get_traders()
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

            messages = await get_new_messages(trader, check_time)
            if messages:
                for message in messages:
                    message_id, message_text, message_time = message
                    if message_id not in sent_messages.get(user_id, set()):
                        await send_message(user_id, message_text)
                        if user_id not in sent_messages:
                            sent_messages[user_id] = set()
                        sent_messages[user_id].add(message_id)
                        last_check_time[user_id] = max(
                            last_check_time.get(user_id, signup_time), message_time
                        )
            last_check_time[user_id] = current_time


async def run_scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


def main():
    schedule.every(30).seconds.do(
        lambda: asyncio.create_task(send_messages_to_traders())
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(run_scheduler())
    loop.run_forever()


if __name__ == "__main__":
    main()
