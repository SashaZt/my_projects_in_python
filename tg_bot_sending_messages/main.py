import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
import aiosqlite
import os
from database import DatabaseInitializer

# from loguru import logger
from configuration.logger_setup import logger

api_id = "29672931"
api_hash = "91335e92be641e03aca068501705a503"
API_TOKEN = "7305890308:AAG8c3BY5dPb1wg0LhN2EVIpAngF4WCh8co"

# Инициализация бота и диспетчера
logger.info("Инициализация бота и диспетчера")
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создание экземпляра Router для обработки маршрутов
router = Router()

# Получение текущей директории и создание пути для базы данных
current_directory = os.getcwd()
database_path = os.path.join(current_directory, "database")

# Создание директории для базы данных, если она не существует
os.makedirs(database_path, exist_ok=True)
DATABASE = os.path.join(database_path, "bot_data.db")


# Разметка для кнопок
def main_markup():
    logger.debug("Создание разметки для кнопок")
    buttons = [
        [types.KeyboardButton(text="Отправить сообщение")],
        [types.KeyboardButton(text="Обновить список групп")],
        [types.KeyboardButton(text="Сменить аккаунт")],
    ]
    markup = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return markup


# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    # Отправка приветственного сообщения с клавиатурой
    msg = await message.answer("Выберите действие:", reply_markup=main_markup())
    logger.debug(f"Отправлено сообщение с ID {msg.message_id}")


"""
Отправить сообщение
"""


async def check_bot_permissions(chat_id):
    try:
        member = await bot.get_chat_member(chat_id, bot.id)
        if hasattr(member, "can_send_messages"):
            return member.can_send_messages
        elif isinstance(member, types.ChatMemberAdministrator):
            return True  # Администраторы по умолчанию могут отправлять сообщения
        elif isinstance(member, types.ChatMemberRestricted):
            return member.can_send_messages
        else:
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке прав в группе с ID {chat_id}: {e}")
        return False


# Обработчик кнопки "Отправить сообщение"
@router.message(lambda message: message.text == "Отправить сообщение")
async def send_message_handler(message: types.Message):
    logger.info(
        f"Получена команда 'Отправить сообщение' от пользователя {message.from_user.id}"
    )
    await message.reply("Введите сообщение для отправки:")


@router.message(
    lambda message: message.reply_to_message
    and message.reply_to_message.text == "Введите сообщение для отправки:"
)
async def handle_message_input(message: types.Message):
    user_message = message.text
    logger.info(
        f"Получено сообщение для отправки: {user_message} от пользователя {message.from_user.id}"
    )

    groups = await db_initializer.get_groups()
    logger.debug(f"Отправка сообщения '{user_message}' в группы: {groups}")

    # Отправка сообщения в каждую группу
    for group_id, group_name in groups:
        sent = False  # Флаг, указывающий на успешность отправки сообщения

        # Попробовать отправить сообщение по group_id
        if group_id:
            chat_id = group_id
            try:
                if await check_bot_permissions(chat_id):
                    await bot.send_message(chat_id, user_message)
                    logger.info(
                        f"Сообщение '{user_message}' отправлено в группу с ID {chat_id}"
                    )
                    sent = True
                else:
                    logger.warning(
                        f"Бот не имеет прав на отправку сообщений в группу с ID {chat_id}"
                    )
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке сообщения в группу с ID {chat_id}: {e}"
                )

        # Если не удалось по group_id, попробовать по group_name
        if not sent and group_name:
            chat_id = group_name
            try:
                if await check_bot_permissions(chat_id):
                    await bot.send_message(chat_id, user_message)
                    logger.info(
                        f"Сообщение '{user_message}' отправлено в группу с именем {chat_id}"
                    )
                else:
                    logger.warning(
                        f"Бот не имеет прав на отправку сообщений в группу с именем {chat_id}"
                    )
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке сообщения в группу с именем {chat_id}: {e}"
                )

    await message.reply(
        "Сообщение отправлено во все группы, к которым у бота есть доступ."
    )


"""
Отправить сообщение
"""


"""
Список груп
"""


# Обработчик кнопки "Обновить список групп"
@router.message(lambda message: message.text == "Обновить список групп")
async def update_groups_handler(message: types.Message):
    logger.info(
        f"Получена команда 'Обновить список групп' от пользователя {message.from_user.id}"
    )
    await message.reply(
        "Введите ID и название группы для добавления, разделенные точкой (.), и несколько групп, разделяя их точкой с запятой (;)"
    )


# Обработчик для ввода ID или названия группы
@router.message(
    lambda message: message.reply_to_message
    and "Введите ID и название группы для добавления" in message.reply_to_message.text
)
async def add_group_handler(message: types.Message):
    logger.info(f"Обработка ввода групп от пользователя {message.from_user.id}")
    group_inputs = message.text.split(";")
    logger.info(
        f"Получено значение групп: {group_inputs} от пользователя {message.from_user.id}"
    )

    results = []
    for group_input in group_inputs:
        group_input = group_input.strip()
        if "." in group_input:
            group_id, group_name = group_input.split(".", 1)
            group_id = group_id.strip()
            group_name = group_name.strip()
            result = await db_initializer.add_group(group_id, group_name)
            results.append(result)
        else:
            results.append(f"Некорректный формат группы: {group_input}")
            logger.error(f"Некорректный формат группы: {group_input}")

    await message.reply("\n".join(results))


"""
Список груп
"""


# Обработчик кнопки "Сменить аккаунт"
@router.message(lambda message: message.text == "Сменить аккаунт")
async def change_account_handler(message: types.Message):
    logger.info(
        f"Получена команда 'Сменить аккаунт' от пользователя {message.from_user.id}"
    )
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute("SELECT account_name FROM accounts") as cursor:
            accounts = await cursor.fetchall()
            logger.debug("Получен список аккаунтов из базы данных")
            account_list = "\n".join([f"/account_{account[0]}" for account in accounts])
            await message.reply(f"Выберите аккаунт:\n{account_list}")


# Обработчик для выбора аккаунта
@router.message(lambda message: message.text.startswith("/account_"))
async def select_account_handler(message: types.Message):
    account_name = message.text.split("_", 1)[1]
    logger.info(f"Пользователь {message.from_user.id} выбрал аккаунт {account_name}")
    async with aiosqlite.connect(DATABASE) as db:
        async with db.execute(
            "SELECT api_id, api_hash FROM accounts WHERE account_name=?",
            (account_name,),
        ) as cursor:
            account = await cursor.fetchone()
            if account:
                bot.api_id = account[0]
                bot.api_hash = account[1]
                await message.reply(f"Аккаунт {account_name} выбран.")
                logger.info(
                    f"Аккаунт {account_name} выбран пользователем {message.from_user.id}"
                )
            else:
                await message.reply("Ошибка выбора аккаунта.")
                logger.error(
                    f"Ошибка выбора аккаунта {account_name} пользователем {message.from_user.id}"
                )


# Основная асинхронная функция
async def main():
    global db_initializer
    logger.info("Запуск основной функции")
    db_initializer = DatabaseInitializer()
    await db_initializer.init_db()
    logger.info("База данных инициализирована")
    dp.include_router(router)
    logger.info("Маршрутизатор зарегистрирован")
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Вебхук удален, начат polling")
    await dp.start_polling(bot)


# Запуск основной функции
if __name__ == "__main__":
    logger.info("Запуск бота")
    asyncio.run(main())
