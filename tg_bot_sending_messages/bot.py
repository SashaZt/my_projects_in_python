import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from configuration.logger_setup import logger
from database import DatabaseInitializer
import os

"""
Комментарий по использованию сессий Telegram

При работе с TelegramClient важно правильно управлять сессиями, чтобы избежать блокировок.
- Инициализируйте клиента Telegram в начале каждой операции, где требуется подключение.
- Подключайтесь к Telegram в начале операции с помощью client.connect().
- Выполняйте необходимые действия (например, отправка сообщений или получение информации о каналах).
- После завершения всех операций обязательно отключайте клиента с помощью client.disconnect().

Закрытие сессии после каждого использования предотвращает блокировку файлов сессии,
обеспечивая корректное функционирование и доступ к данным аккаунта.
"""

# Инициализация aiogram бота и диспетчера
API_TOKEN = "6801516384:AAHybytgnyvBafSGJYjZbxuCNKjK_g4Ehhg"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создание экземпляра Router для обработки маршрутов
router = Router()

# Инициализация глобальной переменной для клиента Telethon
current_account = None


# Разметка для кнопок
def main_markup():
    buttons = [
        [types.KeyboardButton(text="Отправить сообщение")],
        [types.KeyboardButton(text="Обновить список групп")],
        [types.KeyboardButton(text="Сменить аккаунт")],
    ]
    markup = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return markup


# Функция для получения данных аккаунта из базы данных
async def get_account_info(account_id=None):
    logger.debug("Получение данных аккаунта из базы данных")
    connection = await db_initializer.pool.acquire()
    try:
        async with connection.cursor() as cursor:
            try:
                if account_id:
                    logger.debug(f"Получение данных для аккаунта с ID {account_id}")
                    await cursor.execute(
                        "SELECT api_id, api_hash, phone_number FROM accounts_for_messages WHERE id=%s",
                        (account_id,),
                    )
                else:
                    logger.debug("Получение данных для первого аккаунта")
                    await cursor.execute(
                        "SELECT api_id, api_hash, phone_number FROM accounts_for_messages LIMIT 1"
                    )
                result = await cursor.fetchone()
                logger.debug(f"Данные аккаунта получены: {result}")
                return result
            except Exception as e:
                logger.error(
                    f"Ошибка при выполнении запроса для получения данных аккаунта: {e}"
                )
                return None
    finally:
        connection.close()  # Закрываем соединение в блоке finally
        logger.debug(
            "Соединение с базой данных закрыто\nПолучили данных аккаунта из базы данных"
        )


# Функция для получения списка групп из базы данных
async def get_group_ids():
    logger.debug("Получение списка групп из базы данных")
    connection = await db_initializer.pool.acquire()
    try:
        async with connection.cursor() as cursor:
            try:
                await cursor.execute("SELECT group_id FROM groups_for_messages")
                groups = await cursor.fetchall()
                group_ids = [group_id[0] for group_id in groups]
                logger.debug(f"Получен список групп: {group_ids}")
                return group_ids
            except Exception as e:
                logger.error(f"Ошибка при выполнении запроса для получения групп: {e}")
                return []  # Возвращаем пустой список в случае ошибки
    finally:
        connection.close()  # Закрываем соединение в блоке finally
        logger.debug("Соединение с базой данных закрыто group_id")


# Функция для получения ID каналов и добавления их в базу данных
async def add_channels_from_file(api_id, api_hash, phone_number):
    logger.debug("Загрузка каналов из файла")
    file_path = "groups.txt"
    if not os.path.exists(file_path):
        logger.error("Файл groups.txt не найден")
        return

    # Инициализируем клиента Telegram
    client = TelegramClient(f"session_{phone_number}", api_id, api_hash)
    logger.debug(f"Клиент Telegram инициализирован для {phone_number}")

    try:
        logger.debug("Подключение к серверам Telegram")
        await client.connect()

        if not await client.is_user_authorized():
            logger.warning("Пользователь не авторизован, требуется ввод кода")
            await client.send_code_request(phone_number)
            # Код для авторизации

        with open(file_path, "r", encoding="utf-8") as file:
            channel_usernames = [line.strip() for line in file if line.strip()]

        for username in channel_usernames:
            try:
                logger.debug(f"Получение информации о канале {username}")
                full_channel = await client(GetFullChannelRequest(username))
                channel_id = full_channel.chats[0].id

                # Преобразуем channel_id в полный формат с префиксом -100
                full_channel_id = f"-100{abs(channel_id)}"
                logger.info(f"Получен ID для {username}: {full_channel_id}")

                # Добавляем в базу данных
                try:
                    logger.debug(f"Добавление канала {full_channel_id} в базу данных")
                    await db_initializer.add_group(full_channel_id)
                except Exception as e:
                    logger.error(
                        f"Ошибка при добавление канала {full_channel_id} в бд: {e}"
                    )

            except Exception as e:
                logger.error(f"Ошибка при получении ID для {username}: {e}")

    except Exception as e:
        logger.error(f"Ошибка при подключении к Telegram: {e}")

    finally:
        await client.disconnect()
        logger.debug("Клиент Telegram отключен после получения каналов")


# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(message: types.Message):
    global current_account
    logger.info("Обработка команды /start")
    # Получаем первый аккаунт из базы данных
    account_info = await get_account_info()
    if account_info:
        current_account = account_info
        api_id, api_hash, phone_number = current_account

        # Добавление каналов из файла
        await add_channels_from_file(api_id, api_hash, phone_number)

        await message.answer(
            f"Аккаунт с номером {phone_number} выбран по умолчанию.\nВыберите действие:",
            reply_markup=main_markup(),
        )
        logger.info(f"Аккаунт {phone_number} выбран по умолчанию при старте.")
    else:
        await message.answer(
            "Введите ваши данные для аккаунта в формате: api_id,api_hash,phone_number"
        )
        logger.error("Не удалось получить данные аккаунта при старте")


# Обработчик ввода данных аккаунта
@router.message(
    lambda message: message.reply_to_message
    and "Введите ваши данные для аккаунта" in message.reply_to_message.text
)
async def input_account_handler(message: types.Message):
    logger.info("Обработка ввода данных аккаунта")
    try:
        api_id, api_hash, phone_number = message.text.split(",")
        api_id = api_id.strip()
        api_hash = api_hash.strip()
        phone_number = phone_number.strip()
        logger.debug(f"Получены данные: api_id={api_id}, phone_number={phone_number}")

        # Сохраняем данные аккаунта в базе данных
        async with db_initializer.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                try:
                    await cursor.execute(
                        "INSERT INTO accounts_for_messages (api_id, api_hash, phone_number) VALUES (%s, %s, %s)",
                        (api_id, api_hash, phone_number),
                    )
                    logger.info(f"Аккаунт {phone_number} добавлен в базу данных")
                except Exception as e:
                    logger.error(f"Ошибка при добавлении аккаунта в базу данных: {e}")

    except ValueError:
        await message.reply(
            "Некорректный формат данных. Пожалуйста, введите в формате: api_id,api_hash,phone_number"
        )
        logger.error("Ошибка формата данных при вводе аккаунта")


@router.message(lambda message: message.text == "Отправить сообщение")
async def send_message_handler(message: types.Message):
    logger.info("Обработка запроса на отправку сообщения")
    await message.reply("Введите сообщение для отправки:")


## Пример обработчика для отправки сообщений
@router.message(
    lambda message: message.reply_to_message
    and message.reply_to_message.text == "Введите сообщение для отправки:"
)
async def handle_message_input(message: types.Message):
    global current_account
    user_message = message.text
    logger.info(f"Получено сообщение для отправки: {user_message}")

    # Получаем данные аккаунта из базы данных, если он не выбран
    account_info = await get_account_info()
    if account_info:
        current_account = account_info
        logger.info(f"Данные из БД {current_account}")
    else:
        await message.reply("Не удалось получить данные аккаунта.")
        logger.error("Ошибка получения данных аккаунта.")
        return

    api_id, api_hash, phone_number = current_account
    logger.info(
        f"api_id - {api_id}, api_hash - {api_hash}, phone_number - {phone_number}"
    )

    # Инициализируем клиента Telegram
    logger.debug(f"Создание клиента TelegramClient для {phone_number}")
    client = TelegramClient(f"session_{phone_number}", api_id, api_hash)
    logger.info(f"Клиент Telegram инициализирован: {client}")

    try:
        logger.debug("Подключение к серверам Telegram")
        await client.connect()
        logger.info("Подключение к Telegram установлено")

        # Получение списка групп
        group_ids = await get_group_ids()
        logger.info(f"Данные из БД  group_ids {group_ids}")

        logger.debug(f"Отправка сообщения '{user_message}' в группы: {group_ids}")

        # Отправка сообщения в каждую группу
        for group_id in group_ids:
            try:
                await client.send_message(group_id, user_message)
                logger.info(
                    f"Сообщение '{user_message}' отправлено в группу с ID {group_id}"
                )
            except Exception as e:
                logger.error(
                    f"Ошибка при отправке сообщения в группу с ID {group_id}: {e}"
                )

    except Exception as e:
        logger.error(f"Ошибка при подключении к Telegram: {e}")

    finally:
        await client.disconnect()
        logger.debug("Клиент Telegram отключен")

    await message.reply("Сообщение отправлено во все группы.")


@router.message(lambda message: message.text == "Обновить список групп")
async def update_groups_handler(message: types.Message):
    global current_account
    logger.info("Обработка обновления списка групп")

    # Получаем данные аккаунта для инициализации клиента
    account_info = await get_account_info()
    if account_info:
        current_account = account_info
        api_id, api_hash, phone_number = current_account
    else:
        await message.reply(
            "Не удалось получить данные аккаунта. Пожалуйста, добавьте новый аккаунт."
        )
        logger.error("Ошибка получения данных аккаунта для обновления списка групп.")
        return

    # Обновление списка групп
    await add_channels_from_file(api_id, api_hash, phone_number)
    await message.reply("Список групп обновлён.")
    logger.info("Список групп обновлён пользователем.")


@router.message(
    lambda message: message.reply_to_message
    and "Введите ID группы для добавления" in message.reply_to_message.text
)
async def add_group_handler(message: types.Message):
    logger.info("Обработка добавления группы")
    group_inputs = message.text.split(";")
    results = []
    for group_input in group_inputs:
        group_input = group_input.strip()
        try:
            group_id = int(group_input)
            result = await db_initializer.add_group(group_id)
            results.append(result)
        except ValueError:
            logger.error(f"Некорректный формат группы: {group_input}")
            results.append(f"Некорректный формат группы: {group_input}")
    await message.reply("\n".join(results))


@router.message(lambda message: message.text == "Сменить аккаунт")
async def change_account_handler(message: types.Message):
    logger.info("Обработка смены аккаунта")
    # Подключаемся к базе данных и получаем список аккаунтов
    async with db_initializer.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            try:
                await cursor.execute(
                    "SELECT id, phone_number FROM accounts_for_messages"
                )
                accounts = await cursor.fetchall()
                if accounts:
                    # Формируем список аккаунтов с их ID
                    account_list = "\n".join(
                        [f"{account[0]}: {account[1]}" for account in accounts]
                    )
                    await message.reply(
                        f"Доступные аккаунты:\n{account_list}\nВведите ID аккаунта, чтобы сделать его активным."
                    )
                else:
                    await message.reply(
                        "Нет доступных аккаунтов. Пожалуйста, добавьте новый аккаунт."
                    )
                    logger.warning("Нет доступных аккаунтов для смены")
            except Exception as e:
                logger.error(f"Ошибка при получении списка аккаунтов: {e}")


# Обработчик для выбора аккаунта по ID
@router.message(
    lambda message: message.reply_to_message
    and "Введите ID аккаунта" in message.reply_to_message.text
)
async def select_account_handler(message: types.Message):
    logger.info("Обработка выбора аккаунта")
    global current_account
    try:
        account_id = int(message.text.strip())
        logger.info(
            f"Пользователь {message.from_user.id} выбрал аккаунт с ID {account_id}"
        )

        # Получаем данные аккаунта из базы данных по ID
        account_info = await get_account_info(account_id)
        if account_info:
            current_account = (
                account_info  # Сохраняем текущий аккаунт для последующего использования
            )
            await message.reply(f"Аккаунт с номером {current_account[2]} выбран.")
            logger.info(
                f"Аккаунт с номером {current_account[2]} выбран пользователем {message.from_user.id}"
            )
        else:
            await message.reply(
                "Ошибка выбора аккаунта. Проверьте ID и попробуйте снова."
            )
            logger.error(
                f"Ошибка выбора аккаунта с ID {account_id} пользователем {message.from_user.id}"
            )
    except ValueError:
        await message.reply(
            "Некорректный ID. Пожалуйста, введите числовой ID аккаунта."
        )
        logger.error("Ошибка ввода ID аккаунта")


# Основная асинхронная функция
async def main():
    global db_initializer
    logger.info("Запуск основной функции")
    db_initializer = DatabaseInitializer()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
