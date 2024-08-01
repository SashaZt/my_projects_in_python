import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from telethon import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from configuration.logger_setup import logger
from database import DatabaseInitializer
import os

# Инициализация aiogram бота и диспетчера
API_TOKEN = "6801516384:AAHybytgnyvBafSGJYjZbxuCNKjK_g4Ehhg"
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Создание экземпляра Router для обработки маршрутов
router = Router()

# Инициализация глобальной переменной для клиента Telethon
client = None
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


# Функция для получения ID каналов и добавления их в базу данных
async def add_channels_from_file(client, db_initializer):
    file_path = "groups.txt"
    if not os.path.exists(file_path):
        logger.error("Файл groups.txt не найден")
        return

    with open(file_path, "r", encoding="utf-8") as file:
        channel_usernames = [line.strip() for line in file if line.strip()]

    for username in channel_usernames:
        try:
            # Получаем информацию о канале
            full_channel = await client(GetFullChannelRequest(username))
            channel_id = full_channel.chats[0].id

            # Преобразуем channel_id в полный формат с префиксом -100
            full_channel_id = f"-100{abs(channel_id)}"
            logger.info(f"Получен ID для {username}: {full_channel_id}")

            # Добавляем в базу данных
            await db_initializer.add_group(full_channel_id)
        except Exception as e:
            logger.error(f"Ошибка при получении ID для {username}: {e}")


# Обработчик команды /start
@router.message(Command("start"))
async def start_handler(message: types.Message):
    global current_account, client
    # Проверяем, есть ли аккаунты в базе данных
    async with db_initializer.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                "SELECT api_id, api_hash, phone_number FROM accounts_for_messages"
            )
            accounts = await cursor.fetchall()
            if accounts:
                # Выбираем первый аккаунт и делаем его текущим
                current_account = accounts[0]
                api_id, api_hash, phone_number = current_account
                client = TelegramClient(None, api_id, api_hash)  # Use memory session
                await client.start(phone_number)

                # Вызываем функцию для добавления каналов из файла
                await add_channels_from_file(client, db_initializer)

                await message.answer(
                    f"Аккаунт с номером {phone_number} выбран по умолчанию.\nВыберите действие:",
                    reply_markup=main_markup(),
                )
                logger.info(f"Аккаунт {phone_number} выбран по умолчанию при старте.")
            else:
                await message.answer(
                    "Введите ваши данные для аккаунта в формате: api_id,api_hash,phone_number"
                )


# Обработчик ввода данных аккаунта
@router.message(
    lambda message: message.reply_to_message
    and "Введите ваши данные для аккаунта" in message.reply_to_message.text
)
async def input_account_handler(message: types.Message):
    try:
        api_id, api_hash, phone_number = message.text.split(",")
        api_id = api_id.strip()
        api_hash = api_hash.strip()
        phone_number = phone_number.strip()

        # Сохраняем данные аккаунта в базе данных
        async with db_initializer.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO accounts_for_messages (api_id, api_hash, phone_number) VALUES (%s, %s, %s)",
                    (api_id, api_hash, phone_number),
                )

        global client
        client = TelegramClient(None, api_id, api_hash)  # Use memory session
        await client.start(phone_number)
        await message.reply(
            "Аккаунт добавлен и подключен. Выберите действие:",
            reply_markup=main_markup(),
        )
        logger.info(f"Аккаунт {phone_number} добавлен и подключен.")

    except ValueError:
        await message.reply(
            "Некорректный формат данных. Пожалуйста, введите в формате: api_id,api_hash,phone_number"
        )


@router.message(lambda message: message.text == "Отправить сообщение")
async def send_message_handler(message: types.Message):
    # Проверка наличия групп в базе данных
    groups = await db_initializer.get_groups()
    if not groups:
        await message.reply(
            "Нет доступных групп для отправки сообщений. Пожалуйста, добавьте группы."
        )
    else:
        await message.reply("Введите сообщение для отправки:")


# Обработчик для кнопки "Обновить список групп"
@router.message(lambda message: message.text == "Обновить список групп")
async def update_groups_handler(message: types.Message):
    global client
    if client is None:
        await message.reply(
            "Клиент Telegram не инициализирован. Пожалуйста, выберите аккаунт."
        )
        logger.error("Попытка обновления списка групп без инициализации клиента.")
        return

    # Вызываем функцию для обновления списка групп из файла
    await add_channels_from_file(client, db_initializer)
    await message.reply("Список групп обновлен.")
    logger.info("Список групп обновлен пользователем.")


# Пример обработчика для отправки сообщений
@router.message(
    lambda message: message.reply_to_message
    and message.reply_to_message.text == "Введите сообщение для отправки:"
)
async def handle_message_input(message: types.Message):
    global current_account
    user_message = message.text
    logger.info(f"Получено сообщение для отправки: {user_message}")

    # Получение списка групп
    groups = await db_initializer.get_groups()

    if not groups:
        await message.reply("Нет доступных групп для отправки сообщений.")
        logger.warning("Попытка отправки сообщения без доступных групп.")
        return

    # Проверка, что клиент инициализирован
    if current_account is None:
        await message.reply(
            "Аккаунт не выбран. Пожалуйста, выберите аккаунт для отправки сообщений."
        )
        logger.error("Попытка отправки сообщения с невыбранным аккаунтом.")
        return

    api_id, api_hash, phone_number = current_account
    client = TelegramClient(None, api_id, api_hash)  # Use memory session
    await client.start(phone_number)

    logger.debug(f"Отправка сообщения '{user_message}' в группы: {groups}")

    # Отправка сообщения в каждую группу
    for group_id in groups:
        try:
            await client.send_message(group_id, user_message)
            logger.info(
                f"Сообщение '{user_message}' отправлено в группу с ID {group_id}"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в группу с ID {group_id}: {e}")

    await client.disconnect()
    await message.reply("Сообщение отправлено во все группы.")


@router.message(
    lambda message: message.reply_to_message
    and "Введите ID группы для добавления" in message.reply_to_message.text
)
async def add_group_handler(message: types.Message):
    group_inputs = message.text.split(";")
    results = []
    for group_input in group_inputs:
        group_input = group_input.strip()
        try:
            group_id = int(group_input)
            result = await db_initializer.add_group(group_id)
            results.append(result)
        except ValueError:
            results.append(f"Некорректный формат группы: {group_input}")
    await message.reply("\n".join(results))


@router.message(lambda message: message.text == "Сменить аккаунт")
async def change_account_handler(message: types.Message):
    # Подключаемся к базе данных и получаем список аккаунтов
    async with db_initializer.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT id, phone_number FROM accounts_for_messages")
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


# Обработчик для выбора аккаунта по ID
@router.message(
    lambda message: message.reply_to_message
    and "Введите ID аккаунта" in message.reply_to_message.text
)
async def select_account_handler(message: types.Message):
    global current_account
    try:
        account_id = int(message.text.strip())
        logger.info(
            f"Пользователь {message.from_user.id} выбрал аккаунт с ID {account_id}"
        )

        # Получаем данные аккаунта из базы данных по ID
        async with db_initializer.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "SELECT api_id, api_hash, phone_number FROM accounts_for_messages WHERE id=%s",
                    (account_id,),
                )
                account = await cursor.fetchone()
                if account:
                    current_account = account  # Сохраняем текущий аккаунт для последующего использования
                    await message.reply(f"Аккаунт с номером {account[2]} выбран.")
                    logger.info(
                        f"Аккаунт с номером {account[2]} выбран пользователем {message.from_user.id}"
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
