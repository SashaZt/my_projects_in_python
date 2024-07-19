import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from database import Database
from config import TOKEN, CHANNEL_USERNAME, ADMIN_IDS, MODERATION_GROUP_ID, NAME_CHANNEL
from loguru import logger
import os
import asyncio

# from Parse import TelegramParse

bot = telebot.TeleBot(TOKEN)
db = Database()
db.initialize_db()
USERS_PER_PAGE = 10
user_data = {}

# Определение продуктов и регионов
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


# Разметка для кнопки пробного периода
def trial_markup():
    markup = types.InlineKeyboardMarkup(row_width=True)
    register_button = types.InlineKeyboardButton(
        text="Отримати пробний період на 2 дні 🕒", callback_data="register"
    )
    markup.add(register_button)

    return markup


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


# Разметка для админов
def admin_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Добавить время пользователю"))
    markup.add(types.KeyboardButton("Список пользователей"))
    markup.add(types.KeyboardButton("Добавить группу"))
    markup.add(types.KeyboardButton("Начать парсинг"))
    return markup


# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id in ADMIN_IDS:
        bot.send_message(
            chat_id, "Добро пожаловать в админ панель.", reply_markup=admin_markup()
        )

    elif not db.user_exists(user_id):
        bot.send_message(
            chat_id,
            "🌟 Спробуйте наш телеграм-бот на два дні безкоштовно! 🌟",
            reply_markup=trial_markup(),
        )

    else:
        signup_time = db.get_signup_time(user_id)
        trial_duration = db.get_trial_duration(user_id)
        current_time = datetime.now()

        if signup_time:
            # Убедитесь, что signup_time является объектом datetime
            if isinstance(signup_time, str):
                signup_time = datetime.strptime(signup_time, "%Y-%m-%d %H:%M:%S")

            if current_time < signup_time + timedelta(seconds=trial_duration):
                trial_days = trial_duration // (24 * 60 * 60)
                bot.send_message(
                    chat_id,
                    f"Ви вже підписані і ваш тестовий період активний {trial_days} днів.\n Виберіть свою діяльність:",
                    reply_markup=activity_markup(),
                )
            else:
                bot.send_message(chat_id, "Ваша підписка завершилась!")


# Обработчик нажатия кнопки "register" для получения пробного периода
@bot.callback_query_handler(func=lambda call: call.data == "register")
def callback_register(call):
    chat_id = call.message.chat.id
    # Удаление текущего сообщения
    bot.delete_message(chat_id=chat_id, message_id=call.message.id)
    # Отправка сообщения о необходимости подписки
    bot.send_message(
        chat_id,
        "Щоб користуватися ботом, необхідно підписатися на канал 📢😉. Не пропусти новини та оновлення!",
        reply_markup=start_markup(),
    )


# Обработчик нажатия кнопки "check" для проверки подписки и регистрации пользователя
@bot.callback_query_handler(func=lambda call: call.data == "check")
def callback_check_subscription(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    # Удаление текущего сообщения
    bot.delete_message(chat_id=chat_id, message_id=call.message.id)

    if is_subscribed(user_id):
        if not db.user_exists(user_id):
            nickname = call.from_user.username
            signup_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            db.add_user(user_id, nickname, signup_time)
            bot.answer_callback_query(call.id, "Ваша підписка розпочалась! 🎉")
            bot.send_message(
                chat_id,
                "Ваша підписка розпочалась! 🎉",
            )
        else:
            bot.answer_callback_query(call.id, "Ваша підписка вже активована! 🌟.")

        bot.send_message(
            chat_id, "Дякуємо за підписку на канал! 🎉 Залишайтеся з нами! 🚀"
        )
        bot.send_message(
            chat_id,
            "Виберіть свою діяльність:",
            reply_markup=activity_markup(),
        )
    else:
        bot.send_message(
            chat_id,
            "Щоб користуватися ботом, необхідно підписатися на канал!",
            reply_markup=start_markup(),
        )


# Функция проверки подписки
def is_subscribed(user_id):
    try:
        # Используем ID канала напрямую
        channel_chat_id = CHANNEL_USERNAME  # Должен быть числовым ID канала
        member = bot.get_chat_member(channel_chat_id, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        return False


# Обработчик выбора активности "farmer" или "trader"
@bot.callback_query_handler(func=lambda call: call.data in ["farmer", "trader"])
def activity_selection(call):
    chat_id = call.message.chat.id
    current_directory = os.getcwd()
    photo_path = os.path.join(current_directory, "img/crops.png")

    if call.data == "farmer":
        bot.send_message(chat_id, "Ви вибрали: 🌾 Я фермер, хочу продавати")
        user_data[chat_id] = {
            "role": "farmer",
            "products": [],
            "regions": [],
            "state": "product_selection",
        }
        product_buttons = product_markup(user_data[chat_id]["products"])
        with open(photo_path, "rb") as photo:
            bot.send_photo(chat_id, photo, reply_markup=product_buttons)

    elif call.data == "trader":
        bot.send_message(chat_id, "Ви вибрали: 📈 Я трейдер, хочу купити")
        user_data[chat_id] = {
            "role": "trader",
            "products": [],
            "regions": [],
            "state": "product_selection",
        }
        product_buttons = product_markup(user_data[chat_id]["products"])
        with open(photo_path, "rb") as photo:
            bot.send_photo(chat_id, photo, reply_markup=product_buttons)


# Функция для запроса продукта у пользователя
def ask_product(chat_id):
    msg = bot.send_message(
        chat_id, "Що продаєте? (наприклад, пшениця, ячмінь, горох і т.д.) 🌾"
    )
    bot.register_next_step_handler(msg, process_product)


# Обработка введенного продукта
def process_product(message):
    chat_id = message.chat.id
    product = message.text
    user_data[chat_id]["product"] = product
    ask_region(chat_id)


# Функция для запроса региона у пользователя
def ask_region(chat_id):
    msg = bot.send_message(chat_id, "Де знаходиться склад? (вкажіть регіон) 🌍")
    bot.register_next_step_handler(msg, process_region)


# Обработка введенного региона
def process_region(message):
    chat_id = message.chat.id
    region = message.text
    user_data[chat_id]["region"] = region
    ask_contact(chat_id)


# Функция для запроса контакта у пользователя
def ask_contact(chat_id):
    msg = bot.send_message(chat_id, "Вкажіть номер телефону для зв'язку 📞")
    bot.register_next_step_handler(msg, process_contact)


# Обработка введенного контакта
def process_contact(message):
    chat_id = message.chat.id
    contact = message.text
    user_data[chat_id]["contact"] = contact
    send_application_to_moderation(chat_id)


# Отправка заявки на модерацию
def send_application_to_moderation(chat_id):
    data = user_data[chat_id]
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    application_text = (
        f"НОВА ЗАЯВКА ({date})\n\n"
        f"Сырье: {data['product']}\n"
        f"Регион: {data['region']}\n"
        f"Контакты: {data['contact']}"
    )
    moderation_group_id = MODERATION_GROUP_ID  # Замените на ID вашей группы модерации
    try:
        bot.send_message(moderation_group_id, application_text)
        bot.send_message(chat_id, "Ваша заявка була відправлена на модерацію. Дякуємо!")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в группу модерации: {e}")
        bot.send_message(
            chat_id,
            "Возникла ошибка при отправке заявки на модерацию. Пожалуйста, попробуйте позже.",
        )


# Обработчик выбора продукта
@bot.callback_query_handler(
    func=lambda call: call.data.startswith("product_")
    or call.data in ["select_all_products", "finish_product_selection"]
)
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

            photo_path = "img/region.png"
            region_buttons = region_markup(user_data[chat_id]["regions"])
            with open(photo_path, "rb") as photo:
                bot.send_photo(chat_id, photo, reply_markup=region_buttons)
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
    bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=call.message.id,
        reply_markup=product_markup(selected_products),
    )


# Обработчик выбора региона
@bot.callback_query_handler(
    func=lambda call: call.data.startswith("region_")
    or call.data in ["select_all_regions", "finish_region_selection"]
)
def region_selection(call):
    chat_id = call.message.chat.id
    if call.data == "select_all_regions":
        if chat_id in user_data:
            if len(user_data[chat_id]["regions"]) == len(regions):
                user_data[chat_id]["regions"] = []
            else:
                user_data[chat_id]["regions"] = [region[0] for region in regions]
    elif call.data == "finish_region_selection":
        # asyncio.run(
        #     send_selected_messages(
        #         chat_id, user_data[chat_id]["products"], user_data[chat_id]["regions"]
        #     )
        # )
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
    bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=call.message.id,
        reply_markup=region_markup(selected_regions),
    )


# Команда для установки тестового периода
@bot.message_handler(commands=["set_trial"])
def set_trial(message):
    user_id = message.from_user.id
    try:
        duration = int(message.text.split()[1])
        db.set_trial_duration(user_id, duration)
        bot.send_message(
            message.chat.id, f"Тестовый период установлен на {duration} секунд."
        )
    except (IndexError, ValueError):
        bot.send_message(
            message.chat.id, "Использование: /set_trial <длительность в секундах>"
        )


# Админская команда для добавления времени пользователю
@bot.message_handler(
    func=lambda message: message.text == "Добавить время пользователю"
    and message.from_user.id in ADMIN_IDS
)
def add_time_to_user(message):
    msg = bot.send_message(
        message.chat.id,
        "Введите ID пользователя и количество секунд через пробел (например, 123456789 30):",
    )
    bot.register_next_step_handler(msg, process_add_time)


# Обработка добавления времени пользователю
def process_add_time(message):
    try:
        user_id, duration = map(int, message.text.split())
        if db.user_exists(user_id):
            db.set_trial_duration(user_id, duration)
            bot.send_message(
                message.chat.id,
                f"Тестовый период для пользователя {user_id} установлен на {duration} секунд.",
            )
        else:
            bot.send_message(message.chat.id, "Пользователь с таким ID не найден.")
    except (IndexError, ValueError):
        bot.send_message(
            message.chat.id,
            "Неверный формат. Пожалуйста, введите ID пользователя и количество секунд через пробел.",
        )


# Админская команда для вывода списка пользователей
@bot.message_handler(
    func=lambda message: message.text == "Список пользователей"
    and message.from_user.id in ADMIN_IDS
)
def list_users(message):
    show_users_page(message.chat.id, 0)


# Показ страницы со списком пользователей
def show_users_page(chat_id, page):
    try:
        connection = db.create_connection()
        with connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT user_id, nickname, signup, trial_duration FROM users_tg_bot"
            )
            users = cursor.fetchall()
            total_pages = (len(users) - 1) // USERS_PER_PAGE + 1
            start_index = page * USERS_PER_PAGE
            end_index = start_index + USERS_PER_PAGE
            users_on_page = users[start_index:end_index]

            response = f"Список пользователей (Страница {page + 1} из {total_pages}):\n"
            for user in users_on_page:
                trial_days = user[3] // (24 * 60 * 60)
                response += f"\nID: {user[0]}, Никнейм: {user[1]}, Дата регистрации: {user[2]}, Тестовый період: {trial_days} днів\n"

            keyboard = InlineKeyboardMarkup()
            if page > 0:
                keyboard.add(
                    InlineKeyboardButton(
                        "⬅️ Назад", callback_data=f"prev_page_{page - 1}"
                    )
                )
            if page < total_pages - 1:
                keyboard.add(
                    InlineKeyboardButton(
                        "Вперед ➡️", callback_data=f"next_page_{page + 1}"
                    )
                )

            bot.send_message(chat_id, response, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {e}")
        bot.send_message(
            chat_id,
            "Возникла ошибка при получении списка пользователей. Пожалуйста, попробуйте позже.",
        )


# Обработчик пагинации
@bot.callback_query_handler(
    func=lambda call: call.data.startswith("prev_page_")
    or call.data.startswith("next_page_")
)
def handle_pagination(call):
    page = int(call.data.split("_")[-1])
    show_users_page(call.message.chat.id, page)


# Отправка сообщений с выбранными продуктами и регионами
# async def send_selected_messages(chat_id, products, regions):
#     parser = TelegramParse(products, regions, chat_id, False, True)
#     await parser.start()


# # Проверка подписки на канал
# def is_subscribed(user_id):
#     """
#     Проверяет, подписан ли пользователь на канал.
#     """
#     try:
#         # Используем ID канала напрямую
#         channel_chat_id = CHANNEL_USERNAME  # Должен быть числовым ID канала
#         member = bot.get_chat_member(channel_chat_id, user_id)
#         return member.status in ["member", "administrator", "creator"]
#     except Exception as e:
#         logger.error(f"Ошибка при проверке подписки: {e}")
#         return False


# Запуск бота
bot.polling(non_stop=True)
