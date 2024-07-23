import aiomysql
import asyncio
from telebot.async_telebot import AsyncTeleBot
from datetime import datetime, timedelta, time as dtime
import logging
import schedule
from config import DB_CONFIG, TOKEN
import telebot  # Импортируем telebot для доступа к типам

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка бота
bot = AsyncTeleBot(TOKEN)

# Словарь для хранения временных меток последней проверки
last_check_time = {}
# Словарь для хранения отправленных сообщений по ID
sent_messages = {}
# Словарь для хранения количества отправленных сообщений за день
daily_message_count = {}
# Словарь для хранения отправленных сообщений
user_messages = {}


# Подключение к БД
async def create_connection():
    return await aiomysql.connect(
        host=DB_CONFIG["host"],
        port=3306,  # Укажите порт, если он отличается
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        db=DB_CONFIG["database"],
    )


async def get_traders():
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
        return messages
    except aiomysql.Error as err:
        logger.error(f"Ошибка при получении новых сообщений для {user_id}: {err}")
        return []


async def send_message(user_id, message_text):
    try:
        await bot.send_message(user_id, message_text)
        logger.info(f"Сообщение пользователю {user_id} отправлено успешно")
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")


async def send_messages_to_traders():
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


# Временное сообщение
async def send_trial_end_message(user_id):
    """Отправка сообщения о завершении пробного периода"""
    if user_id in user_messages:
        return  # Сообщение уже отправлено, пропускаем

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
        sent_message = await bot.send_message(
            user_id, message, reply_markup=await tarif_markup()
        )
        logger.info(f"Sent trial period ended message to user {user_id}")
        last_check_time[user_id] = datetime.now()
        daily_message_count[user_id] = daily_message_count.get(user_id, 0) + 1
        user_messages[user_id] = [sent_message.message_id]
    except Exception as e:
        logger.error(f"Failed to send message to user {user_id}: {e}")


async def check_and_send_trial_end_messages():
    logger.info("Запуск проверки и отправки сообщений о завершении пробного периода")

    current_time = datetime.now()
    traders = await get_traders()
    for trader in traders:
        user_id, role, signup, trial_duration, region, material = trader
        signup_time = signup
        end_trial_time = signup_time + timedelta(seconds=trial_duration)

        logger.info(f"Проверка трейдера {user_id} на окончание пробного периода")

        if (
            current_time > end_trial_time - timedelta(days=1)
            and current_time <= end_trial_time
            and await can_send_message(user_id)
        ):
            logger.info(f"Отправка сообщения трейдеру {user_id}")
            await send_trial_end_message(user_id)


async def tarif_markup():
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


async def can_send_message(user_id):
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


@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call):
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
        await bot.send_message(call.message.chat.id, message_basic)
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
        await bot.send_message(call.message.chat.id, message_standard)
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
        await bot.send_message(call.message.chat.id, message_extra)
        logger.info(f"Отправлено сообщение: {message_extra}")


async def run_scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def main():
    schedule.every(30).seconds.do(
        lambda: asyncio.create_task(send_messages_to_traders())
    )
    asyncio.create_task(check_and_send_trial_end_messages())
    await bot.infinity_polling()


if __name__ == "__main__":
    asyncio.run(main())
