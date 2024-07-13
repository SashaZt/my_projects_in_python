import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from threading import local
from datetime import datetime, timedelta
from database import Database
from Parse import TelegramParse
import asyncio
USERS_PER_PAGE = 10
api_id = ''
api_hash = ''
bot = telebot.TeleBot("")

ADMIN_IDS = []
thread_local = local()

db = Database('users_db.sqlite')
db.initialize_db()

user_data = {}

products = [
    ("Пшениця (2,3,4кл)", "product_wheat234"),
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
    ("Нішеві", "product_niches")
]

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
    ("Рівненська", "region_rivne")
]


def start_markup():
    markup = types.InlineKeyboardMarkup(row_width=True)
    link_keyboard = types.InlineKeyboardButton(text="Підписатися👉", url='') # MAIN GROUP
    check_keyboard = types.InlineKeyboardButton(text="Перевірити підписку✅", callback_data="check")
    markup.add(link_keyboard, check_keyboard)
    return markup


def trial_markup():
    markup = types.InlineKeyboardMarkup(row_width=True)
    register_button = types.InlineKeyboardButton(text="Отримати пробний період на 2 дні 🕒", callback_data="register")
    markup.add(register_button)
    return markup


def activity_markup():
    markup = types.InlineKeyboardMarkup(row_width=True)
    farmer_button = types.InlineKeyboardButton(text="🌾 Я фермер, хочу продавати", callback_data="farmer")
    trader_button = types.InlineKeyboardButton(text="📈 Я трейдер, хочу купити", callback_data="trader")
    markup.add(farmer_button, trader_button)
    return markup


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
        markup.add(*buttons[i:i + 2])

    select_all_text = "Скасувати всі" if len(selected_products) == len(products) else "Обрати всі"
    markup.add(types.InlineKeyboardButton(text=select_all_text, callback_data="select_all_products"))
    markup.add(types.InlineKeyboardButton(text="Завершити вибір", callback_data="finish_product_selection"))

    return markup


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
        markup.add(*buttons[i:i + 2])

    select_all_text = "Скасувати всі" if len(selected_regions) == len(regions) else "Обрати всі"
    markup.add(types.InlineKeyboardButton(text=select_all_text, callback_data="select_all_regions"))
    markup.add(types.InlineKeyboardButton(text="Завершити вибір", callback_data="finish_region_selection"))

    return markup


def admin_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Добавить время пользователю"))
    markup.add(types.KeyboardButton("Список пользователей"))
    markup.add(types.KeyboardButton("Добавить группу"))
    markup.add(types.KeyboardButton("Начать парсинг"))
    return markup


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in ADMIN_IDS:
        bot.send_message(chat_id, "Добро пожаловать в админ панель.", reply_markup=admin_markup())
    elif not is_subscribed(chat_id):
        bot.send_message(chat_id,
                         "Щоб користуватися ботом, необхідно підписатися на канал 📢😉. Не пропусти новини та оновлення!",
                         reply_markup=start_markup())
    elif not db.user_exists(user_id):
        bot.send_message(chat_id,
                         "🌟 Спробуйте наш телеграм-бот на два дні безкоштовно! 🌟",
                         reply_markup=trial_markup())
    else:
        signup_time = db.get_signup_time(user_id)
        trial_duration = db.get_trial_duration(user_id)
        current_time = datetime.now()

        if signup_time:
            signup_time = datetime.strptime(signup_time, '%Y-%m-%d %H:%M:%S')
            if current_time < signup_time + timedelta(seconds=trial_duration):
                trial_days = trial_duration // (24 * 60 * 60)
                bot.send_message(chat_id,
                                 f"Ви вже підписані і ваш тестовий період активний {trial_days} днів.\n Виберіть свою діяльність:",
                                 reply_markup=activity_markup())
            else:
                bot.send_message(chat_id, "Ваша підписка завершилась!")



@bot.callback_query_handler(func=lambda call: call.data == "register")
def callback_register(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if not db.user_exists(user_id):
        nickname = call.from_user.username
        signup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.add_user(user_id, nickname, signup_time)
        bot.answer_callback_query(call.id, "Ваша підписка розпочалась! 🎉")
        bot.send_message(chat_id, "Ваша підписка розпочалась! 🎉\nВиберіть свою діяльність:", reply_markup=activity_markup())
    else:
        bot.answer_callback_query(call.id, "Ваша підписка вже активована! 🌟.")


@bot.callback_query_handler(func=lambda call: call.data == "check")
def callback(call):
    chat_id = call.message.chat.id
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    if is_subscribed(chat_id):
        bot.send_message(chat_id, "Дякуємо за підписку на канал! 🎉 Залишайтеся з нами! 🚀")
        bot.send_message(chat_id, "🌟 Спробуйте наш телеграм-бот на два дні безкоштовно! 🌟",
                         reply_markup=trial_markup())
    else:
        bot.send_message(chat_id, "Щоб користуватися ботом, необхідно підписатися на канал!",
                         reply_markup=start_markup())


@bot.callback_query_handler(func=lambda call: call.data in ["farmer", "trader"])
def activity_selection(call):
    chat_id = call.message.chat.id
    if call.data == "farmer":
        bot.send_message(chat_id, "Ви вибрали: 🌾 Я фермер, хочу продавати")
        user_data[chat_id] = {"role": "farmer", "state": "product_selection"}
        ask_product(chat_id)
    elif call.data == "trader":
        bot.send_message(chat_id, "Ви вибрали: 📈 Я трейдер, хочу купити")
        user_data[chat_id] = {"role": "trader", "products": [], "regions": [], "state": "product_selection"}
        photo_path = 'img/crops.png'
        product_buttons = product_markup(user_data[chat_id]["products"])
        with open(photo_path, 'rb') as photo:
            bot.send_photo(chat_id, photo, reply_markup=product_buttons)

def ask_product(chat_id):
    msg = bot.send_message(chat_id, "Що продаєте? (наприклад, пшениця, ячмінь, горох і т.д.) 🌾")
    bot.register_next_step_handler(msg, process_product)

def process_product(message):
    chat_id = message.chat.id
    product = message.text
    user_data[chat_id]["product"] = product
    ask_region(chat_id)

def ask_region(chat_id):
    msg = bot.send_message(chat_id, "Де знаходиться склад? (вкажіть регіон) 🌍")
    bot.register_next_step_handler(msg, process_region)

def process_region(message):
    chat_id = message.chat.id
    region = message.text
    user_data[chat_id]["region"] = region
    ask_contact(chat_id)

def ask_contact(chat_id):
    msg = bot.send_message(chat_id, "Вкажіть номер телефону для зв'язку 📞")
    bot.register_next_step_handler(msg, process_contact)

def process_contact(message):
    chat_id = message.chat.id
    contact = message.text
    user_data[chat_id]["contact"] = contact
    send_application_to_moderation(chat_id)

def send_application_to_moderation(chat_id):
    data = user_data[chat_id]
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    application_text = (
        f"НОВА ЗАЯВКА ({date})\n\n"
        f"Сырье: {data['product']}\n"
        f"Регион: {data['region']}\n"
        f"Контакты: {data['contact']}"
    )
    moderation_group_id = ''  # Замените на ID группы модерации
    bot.send_message(moderation_group_id, application_text)
    bot.send_message(chat_id, "Ваша заявка була відправлена на модерацію. Дякуємо!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("product_") or call.data in ["select_all_products", "finish_product_selection"])
def product_selection(call):
    chat_id = call.message.chat.id
    if call.data == "select_all_products":
        if chat_id in user_data:
            if len(user_data[chat_id]["products"]) == len(products):
                user_data[chat_id]["products"] = []
            else:
                user_data[chat_id]["products"] = [product[0] for product in products]
    elif call.data == "finish_product_selection":
        if chat_id in user_data:
            user_data[chat_id]["state"] = "region_selection"

            bot.delete_message(chat_id=chat_id, message_id=call.message.id)

            photo_path = 'img/region.png'
            region_buttons = region_markup(user_data[chat_id]["regions"])
            with open(photo_path, 'rb') as photo:
                bot.send_photo(chat_id, photo, reply_markup=region_buttons)
            #
            # bot.send_message(chat_id, "Виберіть регіон, де ви хочете купити:",
            #                  reply_markup=region_markup(user_data[chat_id]["regions"]))
        return
    else:
        product = call.data
        product_name = next((prod[0] for prod in products if prod[1] == product), None)
        if chat_id in user_data and product_name:
            if product_name in user_data[chat_id]["products"]:
                user_data[chat_id]["products"].remove(product_name)
            else:
                user_data[chat_id]["products"].append(product_name)
    selected_products = user_data[chat_id]["products"]
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id,
                                  reply_markup=product_markup(selected_products))


@bot.callback_query_handler(func=lambda call: call.data.startswith("region_") or call.data in ["select_all_regions", "finish_region_selection"])
def region_selection(call):
    chat_id = call.message.chat.id
    if call.data == "select_all_regions":
        if chat_id in user_data:
            if len(user_data[chat_id]["regions"]) == len(regions):
                user_data[chat_id]["regions"] = []
            else:
                user_data[chat_id]["regions"] = [region[0] for region in regions]
    elif call.data == "finish_region_selection":

        asyncio.run(send_selected_messages(chat_id, user_data[chat_id]["products"], user_data[chat_id]["regions"]))
        bot.delete_message(chat_id=chat_id, message_id=call.message.id)
        return
    else:
        region = call.data
        region_name = next((reg[0] for reg in regions if reg[1] == region), None)
        if chat_id in user_data and region_name:
            if region_name in user_data[chat_id]["regions"]:
                user_data[chat_id]["regions"].remove(region_name)
            else:
                user_data[chat_id]["regions"].append(region_name)
    selected_regions = user_data[chat_id]["regions"]
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.id,
                                  reply_markup=region_markup(selected_regions))


@bot.message_handler(commands=['set_trial'])
def set_trial(message):
    user_id = message.from_user.id
    try:
        duration = int(message.text.split()[1])
        db.set_trial_duration(user_id, duration)
        bot.send_message(message.chat.id, f"Тестовый период установлен на {duration} секунд.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Использование: /set_trial <длительность в секундах>")


@bot.message_handler(func=lambda message: message.text == "Добавить время пользователю" and message.from_user.id in ADMIN_IDS)
def add_time_to_user(message):
    msg = bot.send_message(message.chat.id, "Введите ID пользователя и количество секунд через пробел (например, 123456789 30):")
    bot.register_next_step_handler(msg, process_add_time)


def process_add_time(message):
    try:
        user_id, duration = map(int, message.text.split())
        if db.user_exists(user_id):
            db.set_trial_duration(user_id, duration)
            bot.send_message(message.chat.id, f"Тестовый период для пользователя {user_id} установлен на {duration} секунд.")
        else:
            bot.send_message(message.chat.id, "Пользователь с таким ID не найден.")
    except (IndexError, ValueError):
        bot.send_message(message.chat.id, "Неверный формат. Пожалуйста, введите ID пользователя и количество секунд через пробел.")

@bot.message_handler(func=lambda message: message.text == "Список пользователей" and message.from_user.id in ADMIN_IDS)
def list_users(message):
    show_users_page(message.chat.id, 0)


def show_users_page(chat_id, page):
    connection = db.create_connection()
    with connection:
        cursor = connection.cursor()
        users = cursor.execute("SELECT user_id, nickname, signup, trial_duration FROM users").fetchall()
        total_pages = (len(users) - 1) // USERS_PER_PAGE + 1
        start_index = page * USERS_PER_PAGE
        end_index = start_index + USERS_PER_PAGE
        users_on_page = users[start_index:end_index]

        response = f"Список пользователей (Страница {page + 1} из {total_pages}):\n"
        for user in users_on_page:
            trial_days = user[3] // (24 * 60 * 60)
            response += f"\nID: {user[0]}, Никнейм: {user[1]}, Дата регистрации: {user[2]}, Тестовый период: {trial_days} дней\n"

        keyboard = InlineKeyboardMarkup()
        if page > 0:
            keyboard.add(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_page_{page - 1}"))
        if page < total_pages - 1:
            keyboard.add(InlineKeyboardButton("Вперед ➡️", callback_data=f"next_page_{page + 1}"))

        bot.send_message(chat_id, response, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: call.data.startswith("prev_page_") or call.data.startswith("next_page_"))
def handle_pagination(call):
    page = int(call.data.split("_")[-1])
    show_users_page(call.message.chat.id, page)


async def send_selected_messages(chat_id, products, regions):
    parser = TelegramParse(products, regions, chat_id, False, True)
    await parser.start()


def is_subscribed(chat_id):
    status = ['creator', 'administrator', 'member']
    for i in status:
        if i == bot.get_chat_member(chat_id="", user_id=chat_id).status: # Замените на ID основной группи
            return True
    return False


bot.polling(non_stop=True)
