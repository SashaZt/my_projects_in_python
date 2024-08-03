import asyncio
import random
import schedule
from datetime import datetime, timedelta, time as dtime
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from telethon import TelegramClient
from telethon.tl.types import Channel
from telethon.tl.types import InputPeerEmpty
from configuration.logger_setup import logger
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest
from telethon.tl.types import ChannelParticipantSelf
from telethon.tl.types import ChannelParticipantsAdmins, InputPeerChannel, PeerChannel
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError
from telethon.tl.functions.channels import GetParticipantsRequest, JoinChannelRequest
from telethon.tl.types import ChannelParticipantsSearch, PeerChannel
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError
import schedule
import random
from datetime import datetime, timedelta, time as dtime


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
        [types.KeyboardButton(text="Старт")],  # Новая кнопка "Старт"
        [types.KeyboardButton(text="Отправить сообщение")],
        [types.KeyboardButton(text="Обновить список групп")],
        [types.KeyboardButton(text="Присоединиться к группе")],  #
        [types.KeyboardButton(text="Сменить аккаунт")],
    ]
    markup = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return markup


# Обработчик для кнопки "Старт"
@router.message(lambda message: message.text == "Старт")
async def start_button_handler(message: types.Message):
    logger.info("Обработка кнопки 'Старт'")
    await message.reply(
        "Добро пожаловать! Выберите действие на клавиатуре.", reply_markup=main_markup()
    )


# Обработчик для кнопки "Присоединиться к группе"
@router.message(lambda message: message.text == "Присоединиться к группе")
async def join_group_button_handler(message: types.Message):
    logger.info("Обработка кнопки 'Присоединиться к группе'")

    # Передаем db_initializer в join_groups
    await join_groups(db_initializer)

    await message.reply(
        "Вы успешно присоединились ко всем группам.", reply_markup=main_markup()
    )


# Функция для обновления списка групп и добавления новых в базу данных
async def update_groups_from_file(client, db_initializer):
    logger.debug("Загрузка каналов из файла")
    file_path = "groups.txt"
    if not os.path.exists(file_path):
        logger.error("Файл groups.txt не найден")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            channel_usernames = [line.strip() for line in file if line.strip()]

        existing_groups = await get_group_ids(
            db_initializer
        )  # Получаем текущий список групп из базы данных

        for username in channel_usernames:
            if username not in existing_groups:  # Проверяем наличие по названию группы
                try:
                    logger.debug(f"Получение информации о канале {username}")
                    full_channel = await client(GetFullChannelRequest(username))
                    channel_id = full_channel.chats[0].id

                    full_channel_id = f"-100{abs(channel_id)}"
                    logger.info(f"Получен ID для {username}: {full_channel_id}")

                    try:
                        await db_initializer.add_group(full_channel_id, username)
                        logger.info(f"Канал {full_channel_id} добавлен в базу данных")
                    except Exception as e:
                        logger.error(
                            f"Ошибка при добавлении канала {full_channel_id} в бд: {e}"
                        )
                except Exception as e:
                    logger.error(f"Ошибка при получении ID для {username}: {e}")
            else:
                logger.info(f"Канал {username} уже существует в базе данных")

    except Exception as e:
        logger.error(f"Ошибка при обработке файла групп: {e}")


# Обработчик для кнопки "Обновить список групп"
@router.message(lambda message: message.text == "Обновить список групп")
async def update_groups_handler(message: types.Message):
    logger.info("Обработка обновления списка групп")

    # Получаем данные аккаунта для инициализации клиента
    account_info = await get_account_info()
    if account_info:
        api_id, api_hash, phone_number = account_info
    else:
        await message.reply(
            "Не удалось получить данные аккаунта. Пожалуйста, добавьте новый аккаунт."
        )
        logger.error("Ошибка получения данных аккаунта для обновления списка групп.")
        return

    # Обновляем список групп из файла
    client = TelegramClient(f"session_{phone_number}", api_id, api_hash)
    await client.start(phone_number)
    await update_groups_from_file(client, db_initializer)
    await client.disconnect()

    await message.reply("Список групп обновлён.")
    logger.info("Список групп обновлён пользователем.")


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
async def get_group_ids(db_initializer):
    logger.debug("Получение списка групп из базы данных")
    connection = await db_initializer.pool.acquire()
    try:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT group_id, group_link FROM groups_for_messages")
            groups = await cursor.fetchall()
            group_dict = {
                group_link: group_id for group_id, group_link in groups
            }  # Создаем словарь
            logger.debug(f"Получен список групп: {group_dict}")
            return group_dict
    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса для получения групп: {e}")
        return {}  # Возвращаем пустой словарь в случае ошибки
    finally:
        if connection:
            connection.close()
        logger.debug("Соединение с базой данных закрыто group_id")


# Функция для отправки сообщения в конкретную группу
async def send_message_to_group(group_id, message):
    account_info = await get_account_info()
    if account_info:
        api_id, api_hash, phone_number = account_info
        client = TelegramClient(f"session_{phone_number}", api_id, api_hash)
        await client.connect()
        try:
            await client.send_message(group_id, message)
            logger.info(f"Сообщение отправлено в группу {group_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в группу {group_id}: {e}")
        finally:
            await client.disconnect()
            logger.debug("Клиент Telegram отключен после отправки сообщения")


# # Функция для получения ID каналов и добавления их в базу данных
# async def add_channels_from_file(client, db_initializer):
#     logger.debug("Загрузка каналов из файла")
#     file_path = "groups.txt"

#     if not os.path.exists(file_path):
#         logger.error("Файл groups.txt не найден")
#         return

#     try:
#         with open(file_path, "r", encoding="utf-8") as file:
#             channel_usernames = [line.strip() for line in file if line.strip()]

#         for username in channel_usernames:
#             try:
#                 logger.debug(f"Получение информации о канале {username}")
#                 full_channel = await client(GetFullChannelRequest(username))
#                 channel_id = full_channel.chats[0].id

#                 full_channel_id = f"-100{abs(channel_id)}"
#                 logger.info(f"Получен ID для {username}: {full_channel_id}")

#                 try:
#                     logger.debug(
#                         f"Проверка и добавление канала {full_channel_id} в базу данных"
#                     )
#                     existing_groups = (
#                         await get_group_ids()
#                     )  # Получаем текущий список групп из базы данных
#                     if full_channel_id not in existing_groups:
#                         # Добавляем канал в базу данных
#                         await db_initializer.add_group(full_channel_id, username)
#                         logger.info(f"Канал {full_channel_id} добавлен в базу данных")
#                     else:
#                         logger.info(
#                             f"Канал {full_channel_id} уже существует в базе данных"
#                         )
#                 except Exception as e:
#                     logger.error(
#                         f"Ошибка при добавлении канала {full_channel_id} в бд: {e}"
#                     )

#             except Exception as e:
#                 # Логируем ошибку и записываем в файл ошибок
#                 logger.error(f"Ошибка при получении ID для {username}: {e}")

#     except Exception as e:
#         logger.error(f"Ошибка при обработке файла групп: {e}")


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

        # Сообщение пользователю без проверки групп
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


# Обработчик команды "Отправить сообщение"
@router.message(lambda message: message.text == "Отправить сообщение")
async def send_message_handler(message: types.Message):
    logger.info("Обработка запроса на отправку сообщения")

    # Запросите у пользователя текст сообщения для отправки
    await message.reply("Введите текст сообщения для отправки:")


# Обработчик следующего сообщения от пользователя
@router.message(
    lambda m: m.reply_to_message
    and m.reply_to_message.text == "Введите текст сообщения для отправки:"
)


# Обработчик следующего сообщения от пользователя
@router.message(
    lambda m: m.reply_to_message
    and m.reply_to_message.text == "Введите текст сообщения для отправки:"
)
async def receive_message_text(m: types.Message):
    user_message = m.text
    logger.info(f"Получено сообщение для отправки: {user_message}")

    # Получаем данные аккаунта для инициализации клиента
    account_info = await get_account_info()
    if account_info:
        api_id, api_hash, phone_number = account_info
        # Запуск расписания для отправки сообщений
        await setup_scheduler(api_id, api_hash, phone_number, user_message)
        await m.reply("Расписание для отправки сообщений настроено.")
    else:
        await m.reply("Ошибка получения данных аккаунта.")
        logger.error("Ошибка получения данных аккаунта.")


# async def handle_message_input(message: types.Message):
#     global current_account
#     user_message = message.text
#     logger.info(f"Получено сообщение для отправки: {user_message}")

#     # Получаем данные аккаунта из базы данных, если он не выбран
#     account_info = await get_account_info()
#     if account_info:
#         current_account = account_info
#         logger.info(f"Данные из БД {current_account}")
#     else:
#         await message.reply("Не удалось получить данные аккаунта.")
#         logger.error("Ошибка получения данных аккаунта.")
#         return

#     api_id, api_hash, phone_number = current_account
#     logger.info(
#         f"api_id - {api_id}, api_hash - {api_hash}, phone_number - {phone_number}"
#     )

#     # Инициализируем клиента Telegram
#     logger.debug(f"Создание клиента TelegramClient для {phone_number}")
#     client = TelegramClient(f"session_{phone_number}", api_id, api_hash)
#     logger.info(f"Клиент Telegram инициализирован: {client}")

#     try:
#         logger.debug("Подключение к серверам Telegram")
#         await client.connect()
#         logger.info("Подключение к Telegram установлено")

#         # Получение списка групп
#         group_ids = await get_group_ids()
#         logger.info(f"Данные из БД  group_ids {group_ids}")

#         logger.debug(f"Отправка сообщения '{user_message}' в группы: {group_ids}")

#         # Отправка сообщения в каждую группу с паузой между отправками
#         for group_id in group_ids:
#             try:
#                 await client.send_message(group_id, user_message)
#                 logger.info(
#                     f"Сообщение '{user_message}' отправлено в группу с ID {group_id}"
#                 )
#                 await asyncio.sleep(random.randint(180, 300))  # Пауза от 3 до 5 минут
#             except Exception as e:
#                 logger.error(
#                     f"Ошибка при отправке сообщения в группу с ID {group_id}: {e}"
#                 )

#     except Exception as e:
#         logger.error(f"Ошибка при подключении к Telegram: {e}")

#     finally:
#         await client.disconnect()
#         logger.debug("Клиент Telegram отключен после отправки сообщений")

#     await message.reply("Сообщение отправлено во все группы.")


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


# Функция для отправки сообщений с паузой между отправками
async def send_messages_with_pause(user_message, api_id, api_hash, phone_number):
    group_ids = await get_group_ids()  # Получение ID групп из базы данных
    logger.info(f"Начало отправки сообщений в группы: {group_ids}")

    for group_id in group_ids:
        client = TelegramClient(f"session_{phone_number}", api_id, api_hash)
        try:
            logger.debug(
                f"Подключение к Telegram для проверки и отправки в группу {group_id}"
            )
            await client.connect()

            try:
                entity = await client.get_entity(group_id)
                # Проверка, является ли аккаунт администратором или имеет права на отправку сообщений
                if isinstance(entity, (Channel, Chat)):
                    participant = await client(GetParticipantRequest(group_id, "me"))
                    if isinstance(participant.participant, ChannelParticipantSelf):
                        logger.info(
                            f"Аккаунт подписан и имеет права на отправку сообщений в группе с ID {group_id}"
                        )
                    else:
                        logger.warning(
                            f"Аккаунт не имеет прав на отправку сообщений в группе с ID {group_id}"
                        )
                        continue
            except Exception as e:
                # Если не подписан или возникла ошибка, пытаемся подписаться
                logger.warning(
                    f"Проблемы с подпиской или правами в группе с ID {group_id}, проверка и подписка..."
                )
                try:
                    await client(JoinChannelRequest(group_id))
                    logger.info(f"Успешно подписан на группу с ID {group_id}")
                except Exception as join_error:
                    logger.error(
                        f"Не удалось подписаться на группу с ID {group_id}: {join_error}"
                    )
                    continue  # Переходим к следующей группе

            # Отправка сообщения в группу
            await client.send_message(group_id, user_message)
            logger.info(f"Сообщение отправлено в группу с ID {group_id}")

            # Логирование времени отправки сообщения
            logger.info(
                f"Сообщение '{user_message}' отправлено в {datetime.now().strftime('%H:%M:%S')}"
            )

        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в группу с ID {group_id}: {e}")

        finally:
            # Отключение клиента Telegram после каждой отправки
            await client.disconnect()
            logger.debug(f"Клиент Telegram отключен после отправки в группу {group_id}")

        # Пауза между отправками
        pause_duration = random.randint(180, 300)  # Пауза от 3 до 5 минут
        logger.info(f"Пауза перед следующим сообщением: {pause_duration // 60} минут")
        await asyncio.sleep(pause_duration)


async def setup_scheduler(api_id, api_hash, phone_number, user_message):
    logger.info("Настройка расписания для отправки сообщений")
    group_ids = await get_group_ids()
    total_groups = len(group_ids)
    logger.debug(f"Общее количество групп для отправки: {total_groups}")

    # Отправка сообщений сразу с паузой
    await send_messages_with_pause(user_message, api_id, api_hash, phone_number)

    # Настройка отправки только в будние дни
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        schedule.every().__getattribute__(day).at("08:00").do(
            lambda: asyncio.create_task(
                send_messages_with_pause(user_message, api_id, api_hash, phone_number)
            )
        )

    logger.info("Расписание для отправки сообщений настроено.")

    # Запуск цикла планировщика
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)


# # Функция для настройки расписания
# async def setup_scheduler(api_id, api_hash, phone_number, user_message):
#     logger.info("Настройка расписания для отправки сообщений")
#     group_ids = await get_group_ids()
#     total_groups = len(group_ids)
#     logger.debug(f"Общее количество групп для отправки: {total_groups}")

#     # Вычисление интервала отправки
#     work_start = 8
#     work_end = 18
#     total_minutes = (work_end - work_start) * 60
#     interval_between_messages = total_minutes // total_groups
#     logger.debug(f"Интервал между отправками: {interval_between_messages} минут")

#     current_time = datetime.now()
#     send_times = []

#     for i in range(total_groups):
#         next_send_time = current_time + timedelta(minutes=interval_between_messages * i)
#         if next_send_time.time() > dtime(work_end, 0):
#             logger.debug(f"Выход за пределы рабочего времени, остановка планирования")
#             break  # Останавливаемся, если выходим за пределы рабочего времени
#         send_times.append(next_send_time.time())
#         schedule.every().monday.at(next_send_time.strftime("%H:%M")).do(
#             lambda: asyncio.create_task(
#                 send_message_to_group(group_ids[i], user_message)
#             )
#         )
#         schedule.every().tuesday.at(next_send_time.strftime("%H:%M")).do(
#             lambda: asyncio.create_task(
#                 send_message_to_group(group_ids[i], user_message)
#             )
#         )
#         schedule.every().wednesday.at(next_send_time.strftime("%H:%M")).do(
#             lambda: asyncio.create_task(
#                 send_message_to_group(group_ids[i], user_message)
#             )
#         )
#         schedule.every().thursday.at(next_send_time.strftime("%H:%M")).do(
#             lambda: asyncio.create_task(
#                 send_message_to_group(group_ids[i], user_message)
#             )
#         )
#         schedule.every().friday.at(next_send_time.strftime("%H:%M")).do(
#             lambda: asyncio.create_task(
#                 send_message_to_group(group_ids[i], user_message)
#             )
#         )

#     for send_time in send_times:
#         logger.info(f"Запланировано отправка сообщения в {send_time}")

#     logger.info("Расписание для отправки сообщений настроено.")


#     # Запуск цикла планировщика
#     while True:
#         schedule.run_pending()
#         await asyncio.sleep(1)


# Функция для присоединения к группам
# Функция для присоединения к группам
async def join_groups(db_initializer, account_id=None):
    logger.debug("Начинаем процесс присоединения к группам")

    # Получаем данные аккаунта из базы данных
    account_info = await get_account_info(account_id)
    if not account_info:
        logger.error("Не удалось получить данные аккаунта")
        return

    api_id, api_hash, phone_number = account_info

    # Получаем список групп из базы данных
    existing_groups = await get_group_ids(db_initializer)
    if not existing_groups:
        logger.error("Список групп пуст или не удалось его получить")
        return

    # Создаем клиент Telethon
    async with TelegramClient(phone_number, api_id, api_hash) as client:
        await client.start()

        joined_count = 0  # Счетчик успешно присоединившихся групп
        pause_duration = 600  # Начальная продолжительность паузы

        for group_link, group_id in existing_groups.items():
            try:
                # Проверяем, присоединился ли аккаунт к группе по ID
                try:
                    # Получаем объект канала
                    channel = await client.get_entity(PeerChannel(int(group_id)))
                    # Получаем информацию о пользователях в канале
                    async for user in client.iter_participants(
                        channel, filter=ChannelParticipantsSearch("")
                    ):
                        if user.id == (await client.get_me()).id:
                            logger.info(f"Уже присоединены к группе с ID {group_id}")
                            break
                    else:
                        # Пытаемся присоединиться к группе по group_id
                        await client(JoinChannelRequest(channel))
                        logger.info(f"Успешно присоединились к группе с ID {group_id}")
                        joined_count += 1
                except UserAlreadyParticipantError:
                    logger.info(f"Уже присоединены к группе с ID {group_id}")

            except Exception as e:
                # Если не удалось присоединиться по ID, пытаемся по ссылке
                if "Could not find the input entity" in str(e):
                    try:
                        # Получаем объект канала по ссылке
                        channel = await client.get_entity(group_link)
                        # Проверяем, является ли пользователь участником
                        async for user in client.iter_participants(
                            channel, filter=ChannelParticipantsSearch("")
                        ):
                            if user.id == (await client.get_me()).id:
                                logger.info(f"Уже присоединены к группе {group_link}")
                                break
                        else:
                            # Пытаемся присоединиться к группе по group_link
                            await client(JoinChannelRequest(channel))
                            logger.info(
                                f"Успешно присоединились к группе с ссылкой {group_link}"
                            )
                            joined_count += 1
                    except UserAlreadyParticipantError:
                        logger.info(f"Уже присоединены к группе с ссылкой {group_link}")
                    except Exception as link_error:
                        # Обрабатываем ситуацию, когда запрос на присоединение уже отправлен
                        if "You have successfully requested to join" in str(link_error):
                            logger.warning(
                                f"Запрос на присоединение к группе {group_link} уже отправлен и ожидает одобрения."
                            )
                        else:
                            logger.error(
                                f"Ошибка при присоединении к группе {group_link}: {link_error}"
                            )
                else:
                    # Обрабатываем ситуацию, когда запрос на присоединение уже отправлен
                    if "You have successfully requested to join" in str(e):
                        logger.warning(
                            f"Запрос на присоединение к группе {group_id} уже отправлен и ожидает одобрения."
                        )
                    else:
                        # Логируем другие ошибки
                        logger.error(
                            f"Ошибка при присоединении к группе {group_id}: {e}"
                        )

            # Делаем паузу после успешного присоединения к 10 группам
            if joined_count >= 10:
                logger.info(
                    f"Пауза {pause_duration} секунд после присоединения к 10 группам"
                )
                await asyncio.sleep(pause_duration)  # Пауза
                pause_duration += 600
                joined_count = 0  # Сброс счетчика

    logger.debug("Завершен процесс присоединения к группам")


async def main():
    global db_initializer
    logger.info("Starting main function")
    db_initializer = DatabaseInitializer()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)

    # Получаем данные аккаунта для инициализации клиента
    # account_info = await get_account_info()
    # if account_info:
    #     api_id, api_hash, phone_number = account_info
    #     # Запуск планировщика
    #     await setup_scheduler(api_id, api_hash, phone_number)
    # else:
    #     logger.error("Ошибка получения данных аккаунта.")
    # Старт поллинга
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
