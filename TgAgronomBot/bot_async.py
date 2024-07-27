from telebot.async_telebot import AsyncTeleBot
import telebot.apihelper as apihelper
import random

from telebot import types
from telebot.types import BotCommand
from datetime import datetime, timedelta, time as dtime
from database import Database
from configuration.config import (
    TOKEN,
    CHANNEL_USERNAME,
    ADMIN_IDS,
    MODERATION_GROUP_ID,
    NAME_CHANNEL,
    DB_CONFIG,
)

# from loguru import logger
from configuration.logger_setup import logger
import os
import asyncio
import aiomysql
import schedule


bot = AsyncTeleBot(TOKEN)  # Изменить инициализацию бота

# db =  Database()
# db.initialize_db()
USERS_PER_PAGE = 10
user_data = {}

# Словарь для хранения временных меток последней проверки
last_check_time = {}
# Словарь для хранения количества отправленных сообщений за день
daily_message_count = {}
# Словарь для хранения отправленных сообщений
user_messages = {}
# Словарь для хранения временных меток последней проверки
sent_messages = {}

# Определение продуктов и регионов
products = [
    # ("Пшениця (2,3,4кл)", "product_wheat234"),
    ("Пшениця", "product_wheat"),
    ("Соняшник", "product_sunflower"),
    ("Соя", "product_soy"),
    ("Ріпак", "product_rapeseed"),
    ("Жито", "product_rye"),
    ("Тритикале", "product_triticale"),
    ("Кукурудза", "product_corn"),
    ("Ячмінь", "product_barley"),
    ("Горох", "product_pea"),
    ("Овес", "product_oat"),
    ("Гречка", "product_buckwheat"),
    ("Нішеві", "product_niches"),
]

# Список регионов
regions = [
    ("Київська", "region_kyiv"),
    ("Львівська", "region_lviv"),
    ("Одеська", "region_odesa"),
    ("Харківська", "region_kharkiv"),
    ("Дніпропетровська", "region_dnipro"),
    ("Запорізька", "region_zaporizhzhia"),
    ("Вінницька", "region_vinnytsia"),
    ("Полтавська", "region_poltava"),
    ("Миколаївська", "region_mykolaiv"),
    ("Чернігівська", "region_chernihiv"),
    ("Сумська", "region_sumy"),
    ("Житомирська", "region_zhytomyr"),
    ("Черкаська", "region_cherkasy"),
    ("Рівненська", "region_rivne"),
    ("Івано-Франківська", "region_ivano_frankivsk"),
    ("Волинська", "region_volyn"),
    ("Тернопільська", "region_ternopil"),
    ("Хмельницька", "region_khmelnytskyi"),
    ("Кіровоградська", "region_kirovohrad"),
    ("Луганська", "region_luhansk"),
    ("Донецька", "region_donetsk"),
    ("Закарпатська", "region_zakarpattia"),
    ("Чернівецька", "region_chernivtsi"),
    ("Херсонська", "region_kherson"),
]


user_messages = {}


# # Создаем постоянное меню
# def create_menu():
#     markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
#     markup.add(KeyboardButton("/tarif"))
#     markup.add(KeyboardButton("/id"))
#     markup.add(KeyboardButton("/support"))
#     markup.add(KeyboardButton("/balance"))
#     return markup


# Устанавливаем команды бота
async def set_commands():
    commands = [
        BotCommand(command="/start", description="Запустит / Перезапустити"),
        BotCommand(command="/tarif", description="обрати тариф, котрий вам підходить"),
        BotCommand(command="/id", description="покаже ваш ID"),
        BotCommand(command="/support", description="звʼязатися з підтримкою"),
        BotCommand(command="/balance", description="дізнайтеся, скільки діє ваш тариф"),
    ]
    await bot.set_my_commands(commands)


# Обработчик команды /start
@bot.message_handler(commands=["start"])
async def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    nickname = message.from_user.username

    # Проверка роли пользователя
    if user_id in ADMIN_IDS:
        await bot.send_message(
            chat_id, "Добро пожаловать в админ панель.", reply_markup=admin_markup()
        )
    else:
        # Проверка подписки на канал
        if not await is_subscribed(user_id):
            await bot.send_message(
                chat_id,
                "Будь ласка, підпишіться на канал, щоб продовжити.",
                reply_markup=trial_markup(),
            )
            return

        if not await db.user_exists(user_id):
            await db.add_user_start(user_id, nickname)

            signup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            trial_duration = 172800  # 48 часов в секундах
            user_data[chat_id] = {
                "nickname": nickname,
                "signup_time": signup_time,
                "trial_duration": trial_duration,
                "role": None,
                "products": [],
                "regions": [],
                "state": "initial",
            }
            message_text = (
                "👋Привіт! Я — бот Agro Helper, який автоматизує пошук вигідних пропозицій на ринку зерна.\n\n"
                "👀Бот замість вас 24/7 стежить за пропозиціями у всьому інтернеті фільтрує та сортує їх за вашим запитом\n<b></b>\n"
                "<a href='https://www.youtube.com/shorts/OBtCzSeYfVM'>‼️ДИВІТЬСЯ ВІДЕО ІНСТРУКЦІЮ</a>\n\n"
                "🚀Отримайте 2 дні безкоштовного користування.🚀"
            )

            await bot.send_message(
                chat_id,
                message_text,
                parse_mode="HTML",
                reply_markup=trial_markup(),
                disable_web_page_preview=True,
            )

        else:
            signup_time = await db.get_signup_time(user_id)
            trial_duration = await db.get_trial_duration(user_id)
            current_time = datetime.now()

            if signup_time:
                if isinstance(signup_time, str):
                    signup_time = datetime.strptime(signup_time, "%Y-%m-%d %H:%M:%S")

                if trial_duration is None:
                    trial_duration = 0

                trial_end_time = signup_time + timedelta(seconds=trial_duration)
                remaining_time = trial_end_time - current_time

                if remaining_time.total_seconds() > 0:
                    trial_days = remaining_time.days
                    trial_hours = remaining_time.seconds // 3600
                    await bot.send_message(
                        chat_id,
                        f"Ви вже підписані і ваш тестовий період активний. Залишилось {trial_days} днів і {trial_hours} годин.",
                    )

                    return
                else:
                    pass
                    # await bot.send_message(chat_id, "Ваш тестовий період завершився!")
    if timedelta(0) < remaining_time <= timedelta(days=1):
        logger.info(f"Осталось времени: {remaining_time} для пользователя {user_id}")

        # # Проверка временного статуса и времени отправки
        # can_send = await can_send_message(user_id)
        # if can_send:
        #     logger.info(f"Отправка сообщения трейдеру {user_id}")
        await send_trial_end_message(user_id)
        # else:
        #     logger.info(
        #         f"Сообщение не отправлено трейдеру {user_id}. Условия не выполнены."
        #     )
    elif remaining_time <= timedelta(0):
        # Действия, если время закончилось или меньше нуля
        logger.info(
            f"Время закончилось или меньше нуля для пользователя {user_id}. Осталось времени: {remaining_time}"
        )
        # Ваш код для обработки случая, когда время закончилось
        await send_trial_end_message(user_id)
    else:
        logger.info(
            f"Условия не выполнены для пользователя {user_id}. Осталось времени: {remaining_time}"
        )


@bot.message_handler(commands=["tarif"])
async def send_tarif_message(message):
    logger.info(f"Обработка команды: {message.text}")
    response_message = (
        "Ваш пробний час закінчився.\nОформіть підписку для отримання повідомлень.\n\n"
        "<b>🌾БАЗОВИЙ ПЛАН</b>\n"
        "1 культура, 1 регіон, щоденні оновлення - 780 грн./міс.\n\n"
        "<b>🌽СТАНДАРТ (Найпопулярніший)</b>\n"
        "5 культур, 3 регіони, щоденні оновлення - 1985 грн./міс.\n\n"
        "<b>🌱ЕКСТРА</b>"
        "Необмежені культури та регіони, щоденні оновлення - 3890 грн./міс.\n\n"
        "Який з тарифів підходить під ваши потреби?\n👇👇👇👇"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Базовый", callback_data="trial_tarif_basic"),
        types.InlineKeyboardButton("Стандартный", callback_data="trial_tarif_standard"),
        types.InlineKeyboardButton("Экстра", callback_data="trial_tarif_extra"),
    )

    await bot.send_message(
        message.chat.id, response_message, parse_mode="HTML", reply_markup=markup
    )
    logger.info(f"Отправлено сообщение с тарифами: {response_message}")


# Обработчик для кнопки "📨Зв'язатися з підтримкою📨"
@bot.message_handler(commands=["support"])
async def contact_support(message):
    await bot.send_message(
        message.chat.id,
        "Зв'яжіться з нашою підтримкою: @AgroHelper_supp",
        # reply_markup=support(),
    )


# Обработчик команды /id
@bot.message_handler(commands=["id"])
async def handle_id(message):
    await bot.send_message(message.chat.id, f"Ваш ID: {message.from_user.id}")


# Обработчик команды /balance
@bot.message_handler(commands=["balance"])
async def handle_balance(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    signup_time = await db.get_signup_time(user_id)
    trial_duration = await db.get_trial_duration(user_id)
    current_time = datetime.now()

    if signup_time:
        if isinstance(signup_time, str):
            signup_time = datetime.strptime(signup_time, "%Y-%m-%d %H:%M:%S")

        if trial_duration is None:
            trial_duration = 0

        trial_end_time = signup_time + timedelta(seconds=trial_duration)
        remaining_time = trial_end_time - current_time

        if remaining_time.total_seconds() > 0:
            trial_days = remaining_time.days
            trial_hours = remaining_time.seconds // 3600
            await bot.send_message(
                chat_id,
                f"Ви вже підписані і ваш тестовий період активний. Залишилось {trial_days} днів і {trial_hours} годин.",
            )
    else:
        await bot.send_message(chat_id, "Ваш тестовий період завершився!")
    # Проверка, что времени осталось меньше суток
    if timedelta(0) < remaining_time <= timedelta(days=1):
        logger.info(f"Осталось времени: {remaining_time} для пользователя {user_id}")

        # # Проверка временного статуса и времени отправки
        # can_send = await can_send_message(user_id)
        # if can_send:
        #     logger.info(f"Отправка сообщения трейдеру {user_id}")
        await send_trial_end_message(user_id)
        # else:
        #     logger.info(
        #         f"Сообщение не отправлено трейдеру {user_id}. Условия не выполнены."
        #     )
    elif remaining_time <= timedelta(0):
        # Действия, если время закончилось или меньше нуля
        logger.info(
            f"Время закончилось или меньше нуля для пользователя {user_id}. Осталось времени: {remaining_time}"
        )
        # Ваш код для обработки случая, когда время закончилось
        await send_trial_end_message(user_id)
    else:
        logger.info(
            f"Условия не выполнены для пользователя {user_id}. Осталось времени: {remaining_time}"
        )


def support():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📨Зв'язатися з підтримкою📨"))
    return markup


# Разметка для кнопки пробного периода
def trial_markup():
    markup = types.InlineKeyboardMarkup(row_width=True)
    register_button = types.InlineKeyboardButton(
        text="🚀Отримати 2 дні безкоштовно 🚀", callback_data="register"
    )
    markup.add(register_button)

    return markup


# Появляется после двух дней
def tarif_markup_to_2days():
    markup = types.InlineKeyboardMarkup(row_width=3)
    basic_button = types.InlineKeyboardButton(
        text="Базовый", callback_data="tarif_basic"
    )
    standard_button = types.InlineKeyboardButton(
        text="Стандартный", callback_data="tarif_standard"
    )
    extra_button = types.InlineKeyboardButton(
        text="Экстра", callback_data="tarif_extra"
    )
    markup.add(basic_button, standard_button, extra_button)
    return markup


async def send_trial_end_message(user_id):
    """Отправка сообщения о завершении пробного периода"""
    message = (
        "Ваш пробний час закінчився. Оформіть підписку для отримання повідомлень /tarif\n\n"
        "🌾<b>БАЗОВИЙ ПЛАН</b>\n"
        "🌽<b>СТАНДАРТ (Найпопулярніший)</b>\n"
        "🌱<b>ЕКСТРА</b>\n\n"
        "Який з тарифів підходить під ваши потреби?\n👇👇ОБЕРІТЬ👇👇"
    )
    # message = (
    #     "Ваш пробний час закінчився. Оформіть підписку для отримання повідомлень:| /tarif |.\n"
    #     "🌾БАЗОВИЙ ПЛАН\n"
    #     "🌽СТАНДАРТ (Найпопулярніший)\n"
    #     "🌱ЕКСТРА\n"
    #     "Який з тарифів підходить під ваши потреби?\n"
    #     "👇👇ОБЕРІТЬ👇👇"
    # )

    try:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Переглянути тарифи", callback_data="tarif"),
        )
        sent_message = await bot.send_message(
            user_id, message, parse_mode="HTML", reply_markup=markup
        )
        logger.info(f"Sent trial period ended message to user {user_id}")
        last_check_time[user_id] = datetime.now()
        daily_message_count[user_id] = daily_message_count.get(user_id, 0) + 1
        user_messages[user_id] = [sent_message.message_id]
    except apihelper.ApiException as e:
        logger.error(f"Failed to send message to user {user_id}: {e}")


# Подключение к БД
async def create_connection():
    return await aiomysql.connect(
        host=DB_CONFIG["host"],
        port=3306,  # Укажите порт, если он отличается
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        db=DB_CONFIG["db"],
    )


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
        return traders
    except aiomysql.Error as err:
        logger.error(f"Ошибка при получении трейдеров: {err}")
        return []
    finally:
        conn.close()


async def get_traders_trial():
    query = """
    SELECT 
        user_id,
        role,
        signup,
        trial_duration,
        temporary_status
    FROM 
        users_tg_bot
    WHERE
        role = 'trader';
    """
    try:
        conn = await create_connection()
        async with conn.cursor() as cursor:
            await cursor.execute(query)
            traders = await cursor.fetchall()
        return traders
    except aiomysql.Error as err:
        logger.error(f"Ошибка при получении трейдеров: {err}")
        return []
    finally:
        conn.close()


async def check_and_send_trial_end_messages():
    logger.info("Запуск проверки и отправки сообщений о завершении пробного периода")
    traders = await get_traders_trial()

    current_time = datetime.now()
    logger.info(f"Сейчас {current_time} ")

    for trader in traders:
        user_id, role, signup, trial_duration, temporary_status = trader
        if temporary_status != 1:
            continue

        signup_time = signup
        end_trial_time = signup_time + timedelta(seconds=trial_duration)
        remaining_time = end_trial_time - current_time

        logger.info(f"Окончание {end_trial_time} для пользователя {user_id}")
        logger.info(f"Проверка трейдера {user_id} на окончание пробного периода")

        # Проверка, что времени осталось меньше суток
        if timedelta(0) < remaining_time <= timedelta(days=1):
            logger.info(
                f"Осталось времени: {remaining_time} для пользователя {user_id}"
            )

            # Проверка временного статуса и времени отправки
            can_send = await can_send_message(user_id)
            if can_send:
                logger.info(f"Отправка сообщения трейдеру {user_id}")
                await send_trial_end_message(user_id)
            else:
                logger.info(
                    f"Сообщение не отправлено трейдеру {user_id}. Условия не выполнены."
                )
        elif remaining_time <= timedelta(0):
            # Действия, если время закончилось или меньше нуля
            logger.info(
                f"Время закончилось или меньше нуля для пользователя {user_id}. Осталось времени: {remaining_time}"
            )
            # Ваш код для обработки случая, когда время закончилось
            await send_trial_end_message(user_id)
        else:
            logger.info(
                f"Условия не выполнены для пользователя {user_id}. Осталось времени: {remaining_time}"
            )


# #Рабачая, убрать потом
# async def can_send_message(user_id):
#     """Проверка, может ли быть отправлено сообщение"""
#     now = datetime.now()
#     if not (dtime(8, 0) <= now.time() <= dtime(20, 0)):
#         logger.info(
#             f"Сообщения могут быть отправлены только с 8:00 до 20:00. Сейчас: {now.time()}"
#         )
#         return False

#     last_sent = last_check_time.get(user_id)
#     if last_sent:
#         logger.info(f"Последняя отправка {last_sent}")
#     else:
#         logger.info(
#             f"Для пользователя {user_id} нет записей о последней отправке сообщений"
#         )

#     if last_sent and now - last_sent < timedelta(minutes=1):
#         logger.info(
#             f"Сообщение пользователю {user_id} было отправлено менее минуты назад."
#         )
#         return False

#     count = daily_message_count.get(user_id, 0)
#     logger.info(
#         f"Количество сообщений, отправленных пользователю {user_id} за сегодня: {count}"
#     )

#     if count >= 20:
#         logger.info(f"Достигнут лимит в 20 сообщений в день для пользователя {user_id}")
#         return False


#     return True
# async def can_send_message(user_id):
#     """Проверка, может ли быть отправлено сообщение (временная версия для тестирования)"""
#     now = datetime.now()

#     # Убрать проверку на временные рамки отправки сообщений
#     # if not (dtime(8, 0) <= now.time() <= dtime(20, 0)):
#     #     logger.info(f"Сообщения могут быть отправлены только с 8:00 до 20:00. Сейчас: {now.time()}")
#     #     return False

#     last_sent = last_check_time.get(user_id)
#     if last_sent:
#         logger.info(f"Последняя отправка {last_sent}")
#     else:
#         logger.info(
#             f"Для пользователя {user_id} нет записей о последней отправке сообщений"
#         )

#     # Убрать проверку на интервал времени между отправками
#     # if last_sent and now - last_sent < timedelta(minutes=1):
#     #     logger.info(f"Сообщение пользователю {user_id} было отправлено менее минуты назад.")
#     #     return False

#     count = daily_message_count.get(user_id, 0)
#     logger.info(
#         f"Количество сообщений, отправленных пользователю {user_id} за сегодня: {count}"
#     )

#     # Убрать проверку на лимит сообщений в день
#     # if count >= 20:
#     #     logger.info(f"Достигнут лимит в 20 сообщений в день для пользователя {user_id}")
#     #     return False

#     return True  # Всегда возвращаем True для тестирования


async def can_send_message(user_id):
    """Проверка, может ли быть отправлено сообщение"""
    now = datetime.now()

    if not (dtime(8, 0) <= now.time() <= dtime(20, 0)):
        logger.info(
            f"Сообщения могут быть отправлены только с 8:00 до 20:00. Сейчас: {now.time()}"
        )
        return False

    last_sent = last_check_time.get(user_id)
    if last_sent:
        logger.info(f"Последняя отправка {last_sent}")
    else:
        logger.info(
            f"Для пользователя {user_id} нет записей о последней отправке сообщений"
        )

    if last_sent and now - last_sent < timedelta(minutes=60):
        logger.info(
            f"Сообщение пользователю {user_id} было отправлено менее часа назад."
        )
        return False

    count = daily_message_count.get(user_id, 0)
    logger.info(
        f"Количество сообщений, отправленных пользователю {user_id} за сегодня: {count}"
    )

    if count >= 3:
        logger.info(f"Достигнут лимит в 3 сообщения в день для пользователя {user_id}")
        return False

    return True


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


# Админская команда для вывода списка пользователей
@bot.message_handler(
    func=lambda message: message.text == "Список пользователей"
    and message.from_user.id in ADMIN_IDS
)
async def list_users(message):
    await show_users_page(message.chat.id, 0)


# Показ страницы со списком пользователей
async def show_users_page(chat_id, page):
    try:
        connection = await create_connection()
        async with connection.cursor() as cursor:
            await cursor.execute(
                "SELECT user_id, nickname, signup, trial_duration FROM users_tg_bot"
            )
            users = await cursor.fetchall()
            total_pages = (len(users) - 1) // USERS_PER_PAGE + 1
            start_index = page * USERS_PER_PAGE
            end_index = start_index + USERS_PER_PAGE
            users_on_page = users[start_index:end_index]

            response = f"Список пользователей (Страница {page + 1} из {total_pages}):\n"
            for user in users_on_page:
                trial_days = user[3] // (24 * 60 * 60)
                response += f"\nID: {user[0]}, Никнейм: {user[1]}, Дата регистрации: {user[2]}, Тестовый період: {trial_days} днів\n"

            keyboard = types.InlineKeyboardMarkup()
            if page > 0:
                keyboard.add(
                    types.InlineKeyboardButton(
                        "⬅️ Назад", callback_data=f"prev_page_{page - 1}"
                    )
                )
            if page < total_pages - 1:
                keyboard.add(
                    types.InlineKeyboardButton(
                        "Вперед ➡️", callback_data=f"next_page_{page + 1}"
                    )
                )

            await bot.send_message(chat_id, response, reply_markup=keyboard)
        connection.close()
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        await bot.send_message(
            chat_id,
            "Возникла ошибка при получении списка пользователей. Пожалуйста, попробуйте позже.",
        )


@bot.callback_query_handler(func=lambda call: call.data == "tarif")
async def all_tarif_callback_query(call):
    logger.info(f"Обработка callback: {call.data}")
    current_directory = os.getcwd()
    message_all_tarif = (
        "Ваш пробний час закінчився\\.\\ Оформіть підписку для отримання повідомлень\\.\\\n"  # Экранирование .
        "*🌾БАЗОВИЙ ПЛАН* \n"  # Жирный текст
        "1 культура\\,\\ 1 регіон\\,\\ щоденні оновлення \\-\\ 780 грн\\.\\/міс\\."  # Экранирование . - ,
        "*🌽СТАНДАРТ* \\(_Найпопулярніший_\)\\ \n"  # кусивом _Найпопулярніший_
        "5 культур\\,\\ 3 регіони\\,\\ щоденні оновлення \\-\\ 1985 грн\\.\\/міс\\. \n"
        "*🌱ЕКСТРА* \n"
        "Необмежені культури та регіони\\,\\ щоденні оновлення \\-\\ 3890 грн\\.\\/міс\\."
        "Який з тарифів підходить під ваши потреби?👇👇👇👇\n"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Базовый", callback_data="trial_tarif_basic"),
        types.InlineKeyboardButton("Стандартный", callback_data="trial_tarif_standard"),
        types.InlineKeyboardButton("Экстра", callback_data="trial_tarif_extra"),
    )
    await bot.send_message(
        call.message.chat.id,
        message_all_tarif,
        reply_markup=markup,
        parse_mode="MarkdownV2",
    )
    logger.info(f"Отправлено сообщение с тарифами: {message_all_tarif}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("trial_"))
async def trial_callback_query(call):
    current_directory = os.getcwd()
    logger.info(f"Обработка callback: {call.data}")
    if call.data == "trial_tarif_basic":
        message_basic = (
            "Ви обрали:\n\n"
            "*🌾БАЗОВИЙ ПЛАН* \n"
            "\\-\\ Доступ до інформації про 1 культуру \n"
            "\\-\\ Доступ до пропозицій з 1 регіону \n"
            "\\-\\ Щоденні оновлення \n"
            "💰780 грн\\.\\ місяць \n\n"
            "*Реквізити для оплати тарифів:* \n\n"
            "*💳Приват Банк* \n"
            "`5457 0822 5614 6379` \n"
            "Одержувач: Стеценко Данило \n\n"
            "*Після оплати написати з чеком:* @AgroHelper\\_\\supp"
        )
        photo_path_basic = os.path.join(current_directory, "img/tarif_basic.png")
        with open(photo_path_basic, "rb") as photo:
            await bot.send_photo(
                call.message.chat.id,
                photo,
                caption=message_basic,
                parse_mode="MarkdownV2",
            )
        logger.info(f"Отправлено сообщение: {message_basic}")
    elif call.data == "trial_tarif_standard":
        message_standard = (
            "Ви обрали:\n\n"
            "*🌽СТАНДАРТ* \\(_Найпопулярніший_\)\\ \n"
            "\\-\\ Доступ до інформації про 5 культур \n"
            "\\-\\ Доступ до пропозицій з 3 регіону \n"
            "\\-\\ Щоденні оновлення \n"
            "💰1985 грн\\.\\ місяць \n\n"
            "*Реквізити для оплати тарифів:* \n\n"
            "*💳Приват Банк* \n"
            "`5457 0822 5614 6379` \n"
            "Одержувач: Стеценко Данило \n\n"
            "*Після оплати написати з чеком:* @AgroHelper\\_\\supp"
        )
        photo_path_standard = os.path.join(current_directory, "img/tarif_standard.png")
        with open(photo_path_standard, "rb") as photo:
            await bot.send_photo(
                call.message.chat.id,
                photo,
                caption=message_standard,
                parse_mode="MarkdownV2",
            )
        logger.info(f"Отправлено сообщение: {message_standard}")
    elif call.data == "trial_tarif_extra":
        message_extra = (
            "Ви обрали:\n\n"
            "*🌱ЕКСТРА* \n"
            "\\-\\ Доступ до інформації про необмежену кількість культур \n"
            "\\-\\  Доступ до пропозицій з необмеженої кількості регіонів \n"
            "\\-\\ Щоденні оновлення \n"
            "💰3890 грн\\.\\ місяць \n\n"
            "*Реквізити для оплати тарифів:* \n\n"
            "*💳Приват Банк* \n"
            "`5457 0822 5614 6379` \n"
            "Одержувач: Стеценко Данило \n\n"
            "*Після оплати написати з чеком:* @AgroHelper\\_\\supp"
        )
        photo_path_extra = os.path.join(current_directory, "img/tarif_extra.png")
        with open(photo_path_extra, "rb") as photo:
            await bot.send_photo(
                call.message.chat.id,
                photo,
                caption=message_extra,
                parse_mode="MarkdownV2",
            )
        logger.info(f"Отправлено сообщение: {message_extra}")


# Разметка для админов
def admin_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Добавить время пользователю"))
    markup.add(types.KeyboardButton("Список пользователей"))
    # markup.add(types.KeyboardButton("Добавить группу"))
    # markup.add(types.KeyboardButton("Начать парсинг"))
    return markup


# Разметка для кнопок подписки и проверки
def start_markup():
    markup = types.InlineKeyboardMarkup(row_width=True)
    link_keyboard = types.InlineKeyboardButton(
        text="Підписатися👉",
        url=f"https://t.me/{NAME_CHANNEL}",
    )
    check_keyboard = types.InlineKeyboardButton(
        text="Перевірити підписку✅", callback_data="check"
    )
    markup.add(link_keyboard, check_keyboard)
    return markup


# Функция проверки подписки
async def is_subscribed(user_id):
    try:
        channel_chat_id = f"@{NAME_CHANNEL}"
        member = await bot.get_chat_member(channel_chat_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False


# # Функция проверки подписки РАБОЧИЙ
# async def is_subscribed(user_id):
#     try:
#         # Используем ID канала напрямую
#         channel_chat_id = CHANNEL_USERNAME  # Должен быть числовым ID канала
#         member = await bot.get_chat_member(channel_chat_id, user_id)
#         return member.status in ["member", "administrator", "creator"]
#     except Exception as e:
#         logger.error(f"Ошибка при проверке подписки: {e}")
#         return False


# Разметка для выбора активности
def activity_markup():
    markup = types.InlineKeyboardMarkup(row_width=True)
    farmer_button = types.InlineKeyboardButton(
        text="🌾 Я фермер, хочу продавати", callback_data="farmer"
    )
    trader_button = types.InlineKeyboardButton(
        text="📈 Я трейдер, хочу купити", callback_data="trader"
    )
    markup.add(farmer_button, trader_button)
    return markup


# Разметка для выбора регионов
def region_markup(selected_regions):
    markup = types.InlineKeyboardMarkup()
    buttons = []
    for region in regions:
        text = region[0]
        if region[0] in selected_regions:
            text = "✅ " + text
        buttons.append(types.InlineKeyboardButton(text=text, callback_data=region[1]))

    # Группируем кнопки по две в строке
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i : i + 2])

    select_all_text = (
        "Скасувати всі" if len(selected_regions) == len(regions) else "Обрати всі"
    )
    markup.add(
        types.InlineKeyboardButton(
            text=select_all_text, callback_data="select_all_regions"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            text="Завершити вибір", callback_data="finish_region_selection"
        )
    )

    return markup


# Разметка для выбора продуктов
def product_markup(selected_products):
    markup = types.InlineKeyboardMarkup()
    buttons = []
    for product in products:
        text = product[0]
        if product[0] in selected_products:
            text = "✅ " + text
        buttons.append(types.InlineKeyboardButton(text=text, callback_data=product[1]))

    # Группируем кнопки по две в строке
    for i in range(0, len(buttons), 2):
        markup.add(*buttons[i : i + 2])

    select_all_text = (
        "Скасувати всі" if len(selected_products) == len(products) else "Обрати всі"
    )
    markup.add(
        types.InlineKeyboardButton(
            text=select_all_text, callback_data="select_all_products"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            text="Завершити вибір", callback_data="finish_product_selection"
        )
    )

    return markup


# Обработчик команды /start РАБОЧИЙ
# @bot.message_handler(commands=["start"])
# async def start(message):
#     user_id = message.from_user.id
#     chat_id = message.chat.id

#     # Проверка роли пользователя
#     if user_id in ADMIN_IDS:
#         await bot.send_message(
#             chat_id, "Добро пожаловать в админ панель.", reply_markup=admin_markup()
#         )
#     elif not db.user_exists(user_id):
#         nickname = message.from_user.username
#         signup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         trial_duration = 172800  # 48 часов в секундах
#         user_data[chat_id] = {
#             "nickname": nickname,
#             "signup_time": signup_time,
#             "trial_duration": trial_duration,
#             "role": None,
#             "products": [],
#             "regions": [],
#             "state": "initial",
#         }
#         message = "👋Привіт! Я — бот Agro Helper, який автоматизує пошук вигідних пропозицій на ринку зерна.\n\n👀Я цілодобово моніторю джерела, збираю, фільтрую та сортуваю пропозиції згідно з вашими потребами. Вам залишається лише обирати найкращі варіанти, зв'язуватися з продавцями та укладати угоди. Економте час і гроші з Agro Helper! 🌾\n<b></b>\n<a href='https://www.youtube.com/shorts/OBtCzSeYfVM'>‼️ДИВІТЬСЯ ВІДЕО ІНСТРУКЦІЮ</a>\n\n🚀Отримайте 2 дні безкоштовного користування.🚀"

#         await bot.send_message(
#             chat_id,
#             message,
#             parse_mode="HTML",
#             reply_markup=trial_markup(),
#             disable_web_page_preview=True,
#         )

#     else:
#         signup_time = db.get_signup_time(user_id)
#         trial_duration = db.get_trial_duration(user_id)
#         current_time = datetime.now()

#         if signup_time:
#             if isinstance(signup_time, str):
#                 signup_time = datetime.strptime(signup_time, "%Y-%m-%d %H:%M:%S")

#             if trial_duration is None:
#                 trial_duration = 0

#             trial_end_time = signup_time + timedelta(seconds=trial_duration)
#             remaining_time = trial_end_time - current_time


#             if remaining_time.total_seconds() > 0:
#                 trial_days = remaining_time.days
#                 trial_hours = remaining_time.seconds // 3600
#                 await bot.send_message(
#                     chat_id,
#                     f"Ви вже підписані і ваш тестовий період активний. Залишилось {trial_days} днів і {trial_hours} годин.",
#                 )
#                 await bot.send_message(
#                     chat_id,
#                     "📨Зв'язатися з підтримкою📨",
#                     reply_markup=technical_support(),
#                 )
#                 return
#             else:
#                 await bot.send_message(chat_id, "Ваш тестовий період завершився!")
#                 await bot.send_message(
#                     chat_id,
#                     "📨Зв'язатися з підтримкою📨",
#                     reply_markup=technical_support(),
#                 )
#         else:
#             await bot.send_message(
#                 chat_id,
#                 "📨Зв'язатися з підтримкою📨",
#                 reply_markup=technical_support(),
#             )

# # Обработчик команды /start
# @bot.message_handler(commands=["start"])
# async def start(message):
#     user_id = message.from_user.id
#     chat_id = message.chat.id

#     # Проверка роли пользователя
#     if user_id in ADMIN_IDS:
#         await bot.send_message(
#             chat_id, "Добро пожаловать в админ панель.", reply_markup=admin_markup()
#         )
#     else:
#         # Проверка подписки на канал
#         chat_member = await bot.get_chat_member(
#             chat_id=f"@{NAME_CHANNEL}", user_id=user_id
#         )
#         if chat_member.status not in ["member", "administrator", "creator"]:
#             await bot.send_message(
#                 chat_id,
#                 "Будь ласка, підпишіться на канал, щоб продовжити.",
#                 reply_markup=trial_markup(),
#             )
#             return

#         if not db.user_exists(user_id):
#             nickname = message.from_user.username
#             signup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             trial_duration = 172800  # 48 часов в секундах
#             user_data[chat_id] = {
#                 "nickname": nickname,
#                 "signup_time": signup_time,
#                 "trial_duration": trial_duration,
#                 "role": None,
#                 "products": [],
#                 "regions": [],
#                 "state": "initial",
#             }
#             message_text = (
#                 "👋Привіт! Я — бот Agro Helper, який автоматизує пошук вигідних пропозицій на ринку зерна.\n\n"
#                 "👀Я цілодобово моніторю джерела, збираю, фільтрую та сортуваю пропозиції згідно з вашими потребами. "
#                 "Вам залишається лише обирати найкращі варіанти, зв'язуватися з продавцями та укладати угоди. "
#                 "Економте час і гроші з Agro Helper! 🌾\n<b></b>\n"
#                 "<a href='https://www.youtube.com/shorts/OBtCzSeYfVM'>‼️ДИВІТЬСЯ ВІДЕО ІНСТРУКЦІЮ</a>\n\n"
#                 "🚀Отримайте 2 дні безкоштовного користування.🚀"
#             )

#             await bot.send_message(
#                 chat_id,
#                 message_text,
#                 parse_mode="HTML",
#                 reply_markup=trial_markup(),
#                 disable_web_page_preview=True,
#             )

#         else:
#             signup_time = db.get_signup_time(user_id)
#             trial_duration = db.get_trial_duration(user_id)
#             current_time = datetime.now()

#             if signup_time:
#                 if isinstance(signup_time, str):
#                     signup_time = datetime.strptime(signup_time, "%Y-%m-%d %H:%M:%S")

#                 if trial_duration is None:
#                     trial_duration = 0

#                 trial_end_time = signup_time + timedelta(seconds=trial_duration)
#                 remaining_time = trial_end_time - current_time


#                 if remaining_time.total_seconds() > 0:
#                     trial_days = remaining_time.days
#                     trial_hours = remaining_time.seconds // 3600
#                     await bot.send_message(
#                         chat_id,
#                         f"Ви вже підписані і ваш тестовий період активний. Залишилось {trial_days} днів і {trial_hours} годин.",
#                     )
#                     await bot.send_message(
#                         chat_id,
#                         "📨Зв'язатися з підтримкою📨",
#                         reply_markup=technical_support(),
#                     )
#                     return
#                 else:
#                     await bot.send_message(chat_id, "Ваш тестовий період завершився!")
#                     await bot.send_message(
#                         chat_id,
#                         "📨Зв'язатися з підтримкою📨",
#                         reply_markup=technical_support(),
#                     )
#             else:
#                 await bot.send_message(
#                     chat_id,
#                     "📨Зв'язатися з підтримкою📨",
#                     reply_markup=technical_support(),
#                 )


# Обработчик нажатия кнопки "register" для получения пробного периода
@bot.callback_query_handler(func=lambda call: call.data == "register")
async def callback_register(call):
    chat_id = call.message.chat.id
    await bot.delete_message(chat_id=chat_id, message_id=call.message.id)
    await bot.send_message(
        chat_id,
        "Щоб користуватися ботом, необхідно підписатися на канал 📢😉. Не пропусти новини та оновлення!",
        reply_markup=start_markup(),
    )


# # Обработчик нажатия кнопки "check" для проверки подписки и регистрации пользователя РАБОЧИЙ
# @bot.callback_query_handler(func=lambda call: call.data == "check")
# async def callback_check_subscription(call):
#     user_id = call.from_user.id
#     chat_id = call.message.chat.id
#     nickname = call.from_user.username

#     await bot.delete_message(chat_id=chat_id, message_id=call.message.id)

#     if is_subscribed(user_id):
#         if not db.user_exists(user_id):
#             signup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             user_data[chat_id] = {
#                 "nickname": nickname,
#                 "signup_time": signup_time,
#                 "role": None,
#                 "products": [],
#                 "regions": [],
#                 "state": "initial",
#             }
#             await bot.answer_callback_query(call.id, "Ваша підписка розпочалась! 🎉")
#             sent_message = await bot.send_message(
#                 chat_id,
#                 "Ваша підписка розпочалась! 🎉",
#             )
#             user_messages[chat_id] = [sent_message.message_id]
#         else:
#             await bot.answer_callback_query(
#                 call.id, "Ваша підписка вже активована! 🌟."
#             )

#         if chat_id in user_messages:
#             for message_id in user_messages[chat_id]:
#                 await bot.delete_message(chat_id=chat_id, message_id=message_id)


#         sent_message_2 = await bot.send_message(
#             chat_id,
#             "Виберіть свою діяльність:",
#             reply_markup=activity_markup(),
#         )
#         user_messages[chat_id] = sent_message_2.message_id
#     else:
#         sent_message = await bot.send_message(
#             chat_id,
#             "Щоб користуватися ботом, необхідно підписатися на канал!",
#             reply_markup=start_markup(),
#         )
#         user_messages[chat_id] = [sent_message.message_id]
# Обработчик нажатия кнопки "check" для проверки подписки и регистрации пользователя
@bot.callback_query_handler(func=lambda call: call.data == "check")
async def callback_check_subscription(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    nickname = call.from_user.username

    await bot.delete_message(chat_id=chat_id, message_id=call.message.id)

    if await is_subscribed(user_id):
        if not await db.user_exists(user_id):
            signup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_data[chat_id] = {
                "nickname": nickname,
                "signup_time": signup_time,
                "role": None,
                "products": [],
                "regions": [],
                "state": "initial",
            }
            await bot.answer_callback_query(call.id, "Ваша підписка розпочалась! 🎉")
            sent_message = await bot.send_message(
                chat_id,
                "Ваша підписка розпочалась! 🎉",
            )
            user_messages[chat_id] = [sent_message.message_id]
        else:
            await bot.answer_callback_query(
                call.id, "Ваша підписка вже активована! 🌟."
            )

        if chat_id in user_messages:
            for message_id in user_messages[chat_id]:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)

        sent_message_2 = await bot.send_message(
            chat_id,
            "Виберіть свою діяльність:",
            reply_markup=activity_markup(),
        )
        user_messages[chat_id] = [sent_message_2.message_id]
    else:
        sent_message = await bot.send_message(
            chat_id,
            "Щоб користуватися ботом, необхідно підписатися на канал!",
            reply_markup=trial_markup(),
        )
        user_messages[chat_id] = [sent_message.message_id]


# Обработчик выбора активности "farmer" или "trader"
@bot.callback_query_handler(func=lambda call: call.data in ["farmer", "trader"])
async def activity_selection(call):
    chat_id = call.message.chat.id
    current_directory = os.getcwd()
    photo_path = os.path.join(current_directory, "img/crops.png")
    await bot.delete_message(chat_id=chat_id, message_id=call.message.id)
    role = "farmer" if call.data == "farmer" else "trader"
    user_data[chat_id]["role"] = role

    product_buttons = product_markup(user_data[chat_id]["products"])
    with open(photo_path, "rb") as photo:
        await bot.send_photo(
            chat_id,
            photo,
            caption="🌽Виберіть зернові, яка вас цікавить, можете вибрати кілька культур та натисніть «завершити вибір»",
            reply_markup=product_buttons,
        )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("product_")
    or call.data in ["select_all_products", "finish_product_selection"]
)
async def product_selection(call):
    chat_id = call.message.chat.id
    if call.data == "select_all_products":
        if len(user_data[chat_id]["products"]) == len(products):
            user_data[chat_id]["products"] = []
        else:
            user_data[chat_id]["products"] = [product[0] for product in products]
    elif call.data == "finish_product_selection":
        user_data[chat_id]["state"] = "region_selection"
        await bot.delete_message(chat_id=chat_id, message_id=call.message.id)
        photo_path = "img/region.png"
        region_buttons = region_markup(user_data[chat_id]["regions"])
        with open(photo_path, "rb") as photo:
            await bot.send_photo(
                chat_id,
                photo,
                caption="🇺🇦Виберіть область, яка вас цікавить, можете вибрати кілька регіонів та натисніть «завершити вибір»",
                reply_markup=region_buttons,
            )
        return
    else:
        product = call.data
        product_name = next((prod[0] for prod in products if prod[1] == product), None)
        if product_name:
            if product_name in user_data[chat_id]["products"]:
                user_data[chat_id]["products"].remove(product_name)
            else:
                user_data[chat_id]["products"].append(product_name)

    selected_products = user_data[chat_id]["products"]
    logger.info(f"Selected products for user {chat_id}: {selected_products}")
    await bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=call.message.id,
        reply_markup=product_markup(selected_products),
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("region_")
    or call.data in ["select_all_regions", "finish_region_selection"]
)
async def region_selection(call):
    chat_id = call.message.chat.id
    if call.data == "select_all_regions":
        if len(user_data[chat_id]["regions"]) == len(regions):
            user_data[chat_id]["regions"] = []
        else:
            user_data[chat_id]["regions"] = [region[0] for region in regions]
    elif call.data == "finish_region_selection":
        await register_user(chat_id)  # Используем await для вызова асинхронной функции
        await bot.delete_message(chat_id=chat_id, message_id=call.message.id)
        return
    else:
        region = call.data
        region_name = next((reg[0] for reg in regions if reg[1] == region), None)
        if region_name:
            if region_name in user_data[chat_id]["regions"]:
                user_data[chat_id]["regions"].remove(region_name)
            else:
                user_data[chat_id]["regions"].append(region_name)

    selected_regions = user_data[chat_id]["regions"]
    logger.info(f"Selected regions for user {chat_id}: {selected_regions}")
    await bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=call.message.id,
        reply_markup=region_markup(selected_regions),
    )


# # РАБОЧАЯ!!!!
# async def register_user(chat_id):
#     logger.info(f"Attempting to register user {chat_id}")

#     user_info = user_data.get(chat_id, {})
#     logger.info(f"user_data for {chat_id}: {user_info}")

#     if not user_info:
#         logger.error(f"No user data found for chat_id {chat_id}")
#         await bot.send_message(chat_id, "Ошибка регистрации. Попробуйте снова.")
#         return

#     nickname = user_info.get("nickname", "")
#     signup_time = user_info.get("signup_time", "")
#     role = user_info.get("role", "")
#     products = user_info.get("products", [])
#     regions = user_info.get("regions", [])

#     logger.info(
#         f"Registering user {chat_id} with role: {role}, products: {products}, regions: {regions}"
#     )

#     # Проверка на пустые списки продуктов и регионов
#     if not products:
#         await bot.send_message(
#             chat_id,
#             "Ви не вибрали жодного продукту. Будь ласка, виберіть хоча б один продукт:",
#             reply_markup=product_markup(user_data[chat_id]["products"]),
#         )
#         return

#     if not regions:
#         await bot.send_message(
#             chat_id,
#             "Ви не вибрали жодного регіону. Будь ласка, виберіть хоча б один регіон:",
#             reply_markup=region_markup(user_data[chat_id]["regions"]),
#         )
#         return

#     if role and products and regions:
#         if not db.user_exists(chat_id):
#             db.add_user(chat_id, nickname, signup_time, role)
#             db.set_trial_duration(chat_id, user_info.get("trial_duration", 172800))
#             logger.info(
#                 f"User {chat_id} added with signup_time {signup_time} and role {role}"
#             )
#         else:
#             logger.info(f"User {chat_id} already exists")

#         for product in products:
#             product_id = db.get_product_id_by_name(product)
#             if product_id is not None:
#                 db.add_user_raw_material(chat_id, product_id)
#                 logger.info(
#                     f"Product {product} with ID {product_id} added for user {chat_id}"
#                 )
#             else:
#                 logger.error(f"Product ID not found for product: {product}")

#         for region in regions:
#             region_id = db.get_region_id_by_name(region)
#             if region_id is not None:
#                 db.add_user_region(chat_id, region_id)
#                 logger.info(
#                     f"Region {region} with ID {region_id} added for user {chat_id}"
#                 )
#             else:
#                 logger.error(f"Region ID not found for region: {region}")

#         await bot.send_message(
#             chat_id,
#             "🎉 Вашу пробну версію активовано!\n\nВи отримали 2 дні безкоштовного використання.\n\n <b>Як тільки з'являться пропозиції на ринку, ви одразу їх отримаєте</b>🚀",
#             parse_mode="HTML",
#         )

#     else:
#         logger.info(f"Недостаточно данных для регистрации пользователя {chat_id}")
#         await bot.send_message(
#             chat_id, "Будь ласка, оберіть усі необхідні дані для реєстрації."
#         )


async def user_exists(user_id):
    connection = await create_connection()
    async with connection.cursor() as cursor:
        await cursor.execute(
            "SELECT COUNT(*) FROM users_tg_bot WHERE user_id = %s", (user_id,)
        )
        result = await cursor.fetchone()
    connection.close()
    return result[0] > 0


async def set_trial_duration(user_id, duration):
    connection = await create_connection()
    async with connection.cursor() as cursor:
        await cursor.execute(
            "UPDATE users_tg_bot SET trial_duration = %s WHERE user_id = %s",
            (duration, user_id),
        )
        await connection.commit()
    connection.close()


# Админская команда для добавления времени пользователю
@bot.message_handler(
    func=lambda message: message.text == "Добавить время пользователю"
    and message.from_user.id in ADMIN_IDS
)
async def add_time_to_user(message):
    await bot.send_message(
        message.chat.id,
        "Введите ID пользователя и количество секунд через пробел (например, 123456789 30):",
    )


@bot.message_handler(func=lambda message: message.from_user.id in ADMIN_IDS)
async def process_add_time(message):
    try:
        user_id, duration = map(int, message.text.split())
        if await user_exists(user_id):
            await set_trial_duration(user_id, duration)
            await bot.send_message(
                message.chat.id,
                f"Тестовый период для пользователя {user_id} установлен на {duration} секунд.",
            )
        else:
            await bot.send_message(
                message.chat.id, "Пользователь с таким ID не найден."
            )
    except (IndexError, ValueError):
        await bot.send_message(
            message.chat.id,
            "Неверный формат. Пожалуйста, введите ID пользователя и количество секунд через пробел.",
        )


async def register_user(chat_id):
    logger.info(f"Attempting to register user {chat_id}")

    user_info = user_data.get(chat_id, {})
    logger.info(f"user_data for {chat_id}: {user_info}")

    if not user_info:
        logger.error(f"No user data found for chat_id {chat_id}")
        await bot.send_message(chat_id, "Ошибка регистрации. Попробуйте снова.")
        return

    nickname = user_info.get("nickname", "")
    signup_time = user_info.get("signup_time", "")
    role = user_info.get("role", "")
    products = user_info.get("products", [])
    regions = user_info.get("regions", [])

    logger.info(
        f"Registering user {chat_id} with role: {role}, products: {products}, regions: {regions}"
    )

    # Проверка на пустые списки продуктов и регионов
    if not products:
        await bot.send_message(
            chat_id,
            "Ви не вибрали жодного продукту. Будь ласка, виберіть хоча б один продукт:",
            reply_markup=product_markup(user_data[chat_id]["products"]),
        )
        return

    if not regions:
        await bot.send_message(
            chat_id,
            "Ви не вибрали жодного регіону. Будь ласка, виберіть хоча б один регіон:",
            reply_markup=region_markup(user_data[chat_id]["regions"]),
        )
        return

    if role and products and regions:
        if await db.user_exists(chat_id):
            await db.add_user(chat_id, nickname, signup_time, role)
            await db.set_trial_duration(
                chat_id, user_info.get("trial_duration", 172800)
            )
            logger.info(
                f"User {chat_id} added with signup_time {signup_time} and role {role}"
            )
        else:
            logger.info(f"User {chat_id} already exists")

        for product in products:
            product_id = await db.get_product_id_by_name(product)
            if product_id is not None:
                await db.add_user_raw_material(chat_id, product_id)
                logger.info(
                    f"Product {product} with ID {product_id} added for user {chat_id}"
                )
            else:
                logger.error(f"Product ID not found for product: {product}")

        for region in regions:
            region_id = await db.get_region_id_by_name(region)
            if region_id is not None:
                await db.add_user_region(chat_id, region_id)
                logger.info(
                    f"Region {region} with ID {region_id} added for user {chat_id}"
                )
            else:
                logger.error(f"Region ID not found for region: {region}")

        await bot.send_message(
            chat_id,
            "🎉 Вашу пробну версію активовано!\n\nВи отримали 2 дні безкоштовного використання.\n\n <b>Як тільки з'являться пропозиції на ринку, ви одразу їх отримаєте</b>🚀",
            parse_mode="HTML",
        )

        # Запрос контактных данных, если роль - "farmer"
        if role == "farmer":
            await bot.send_message(chat_id, "Будь ласка, введіть ваші контактні дані:")
            user_data[chat_id]["state"] = "awaiting_contact"

    else:
        logger.info(f"Недостаточно данных для регистрации пользователя {chat_id}")
        await bot.send_message(
            chat_id, "Будь ласка, оберіть усі необхідні дані для реєстрації."
        )


def schedule_messages():
    start_time = dtime(8, 0)
    end_time = dtime(20, 0)
    intervals = 3

    now = datetime.now()
    first_send = now.replace(hour=8, minute=0, second=0, microsecond=0)
    last_send = now.replace(hour=20, minute=0, second=0, microsecond=0)

    time_deltas = [
        (last_send - first_send) / intervals * i
        + timedelta(minutes=random.randint(0, 59))
        for i in range(1, intervals + 1)
    ]

    for delta in time_deltas:
        send_time = first_send + delta
        if send_time > now:
            schedule.every().day.at(send_time.strftime("%H:%M")).do(
                lambda: asyncio.create_task(check_and_send_trial_end_messages())
            )


# Обработка введенного контакта
@bot.message_handler(
    func=lambda message: user_data.get(message.chat.id, {}).get("state")
    == "awaiting_contact"
)
async def process_contact(message):
    chat_id = message.chat.id
    contact = message.text
    user_data[chat_id]["contact"] = contact
    user_data[chat_id]["state"] = None
    await send_application_to_moderation(chat_id)


# Отправка заявки на модерацию
async def send_application_to_moderation(chat_id):
    data = user_data[chat_id]
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    application_text = (
        f"НОВА ЗАЯВКА ({date})\n\n"
        f"Сырье: {data['products']}\n"
        f"Регион: {data['regions']}\n"
        f"Контакты: {data['contact']}"
    )
    moderation_group_id = MODERATION_GROUP_ID  # Замените на ID вашей группы модерации
    try:
        await bot.send_message(moderation_group_id, application_text)
        await bot.send_message(
            chat_id, "Ваша заявка була відправлена на модерацію. Дякуємо!"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в группу модерации: {e}")
        await bot.send_message(
            chat_id,
            "Возникла ошибка при отправке заявки на модерацию. Пожалуйста, попробуйте позже.",
        )


async def run_scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def main():
    global db

    loop = asyncio.get_running_loop()
    db = Database(loop)
    await db.create_connection()
    await db.initialize_db()
    asyncio.create_task(run_scheduler())  # Запуск планировщика из send_messages_asio.py
    schedule.every(30).seconds.do(
        lambda: asyncio.create_task(send_messages_to_traders())
    )
    schedule_messages()
    await set_commands()  # Устанавливаем команды перед запуском бота
    await bot.infinity_polling()


if __name__ == "__main__":
    asyncio.run(main())
