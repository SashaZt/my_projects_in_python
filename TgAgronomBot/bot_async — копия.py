from telebot.async_telebot import AsyncTeleBot
import telebot.apihelper as apihelper

from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta, time as dtime
from database import Database
from TgAgronomBot.configuration.config import (
    TOKEN,
    CHANNEL_USERNAME,
    ADMIN_IDS,
    MODERATION_GROUP_ID,
    NAME_CHANNEL,
    DB_CONFIG,
)
from loguru import logger
import os
import asyncio
import aiomysql
import schedule


bot = AsyncTeleBot(TOKEN)  # Изменить инициализацию бота

db = Database()
db.initialize_db()
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
]

user_messages = {}


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
            user_id, message, reply_markup=tarif_markup_to_2days()
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
        db=DB_CONFIG["database"],
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
        conn.close()
        return traders
    except aiomysql.Error as err:
        logger.error(f"Ошибка при получении трейдеров: {err}")
        return []


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
        # text="Підписатися👉", url=f"https://t.me/{CHANNEL_USERNAME}"
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
        # Используем ID канала напрямую
        channel_chat_id = CHANNEL_USERNAME  # Должен быть числовым ID канала
        member = await bot.get_chat_member(channel_chat_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False


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


# Обработчик команды /start
@bot.message_handler(commands=["start"])
async def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Проверка роли пользователя
    if user_id in ADMIN_IDS:
        await bot.send_message(
            chat_id, "Добро пожаловать в админ панель.", reply_markup=admin_markup()
        )
    elif not db.user_exists(user_id):
        nickname = message.from_user.username
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
        # Отправка видео с текстом
        with open("video.mp4", "rb") as video:
            await bot.send_video(
                chat_id,
                video,
                caption="🚀<b>ОТРИМАЙТЕ 2 ДНІ БЕЗКОШТОВНОГО ВИКОРИСТАННЯ</b>\n\n‼️Дивіться відео інструкцію‼️\n\n🌽Отримуйте прямі пропозиції на продаж зернових та інших культур без посередників. Щодня отримуйте свіжі заявки з контактами продавців🌻",
                parse_mode="HTML",
                reply_markup=trial_markup(),
            )
    else:
        signup_time = db.get_signup_time(user_id)
        trial_duration = db.get_trial_duration(user_id)
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
                await bot.send_message(chat_id, "Ваш тестовий період завершився!")


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


# Обработчик нажатия кнопки "check" для проверки подписки и регистрации пользователя
@bot.callback_query_handler(func=lambda call: call.data == "check")
async def callback_check_subscription(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    nickname = call.from_user.username

    await bot.delete_message(chat_id=chat_id, message_id=call.message.id)

    if is_subscribed(user_id):
        if not db.user_exists(user_id):
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
        user_messages[chat_id] = sent_message_2.message_id
    else:
        sent_message = await bot.send_message(
            chat_id,
            "Щоб користуватися ботом, необхідно підписатися на канал!",
            reply_markup=start_markup(),
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
        if not db.user_exists(chat_id):
            db.add_user(chat_id, nickname, signup_time, role)
            db.set_trial_duration(chat_id, user_info.get("trial_duration", 172800))
            logger.info(
                f"User {chat_id} added with signup_time {signup_time} and role {role}"
            )
        else:
            logger.info(f"User {chat_id} already exists")

        for product in products:
            product_id = db.get_product_id_by_name(product)
            if product_id is not None:
                db.add_user_raw_material(chat_id, product_id)
                logger.info(
                    f"Product {product} with ID {product_id} added for user {chat_id}"
                )
            else:
                logger.error(f"Product ID not found for product: {product}")

        for region in regions:
            region_id = db.get_region_id_by_name(region)
            if region_id is not None:
                db.add_user_region(chat_id, region_id)
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

    else:
        logger.info(f"Недостаточно данных для регистрации пользователя {chat_id}")
        await bot.send_message(
            chat_id, "Будь ласка, оберіть усі необхідні дані для реєстрації."
        )


async def run_scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


async def main():
    # schedule.every(30).seconds.do(
    #     lambda: asyncio.create_task(send_messages_to_traders())
    # )
    # schedule.every(60).seconds.do(
    #     lambda: asyncio.create_task(check_and_send_trial_end_messages())
    # )

    # asyncio.create_task(run_scheduler())  # Запуск планировщика из send_messages_asio.py
    await bot.infinity_polling()


if __name__ == "__main__":
    asyncio.run(main())
