import asyncio
import random
from asyncio import Lock

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup
from bot.authorization import authorize
from bot.group_manager import add_groups, get_groups, get_groups_with_subscription
from bot.subscription_manager import subscribe_to_groups
from config.config import API_TOKEN, PAUSE_MAX, PAUSE_MIN
from config.logger_setup import logger
from database import init_db

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
db_lock = Lock()


# Состояния для рассылки сообщений
class BroadcastStates(StatesGroup):
    waiting_for_message = State()


# Состояния для добавления групп
class GroupStates(StatesGroup):
    waiting_for_group_links = State()


# Настройка диспетчера с поддержкой FSM
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Добавить группу"),
        ],
        [
            KeyboardButton(text="Рассылка сообщений"),
            KeyboardButton(text="Подписаться на группы"),
        ],
    ],
    resize_keyboard=True,
)


@dp.message(F.text == "/start")
async def start_handler(message: Message):
    """
    Приветствие и главное меню.
    """
    logger.info(f"Команда '/start' вызвана пользователем {message.from_user.id}")

    await message.reply(
        "Добро пожаловать! Управляйте ботом через меню.", reply_markup=main_menu
    )


@dp.message(F.text == "Подписаться на группы")
async def subscribe_handler(message: Message):
    """
    Подписка на группы из базы данных.
    """
    logger.info(
        f"Кнопка 'Подписаться на группы' нажата пользователем {
            message.from_user.id}"
    )

    try:
        groups = get_groups()  # Получаем список групп из базы данных
        if not groups:
            await message.reply("В базе данных нет групп для подписки.")
            logger.info("Подписка не выполнена: список групп пуст.")
            return

        group_links = [group for group in groups]  # Извлекаем ссылки групп
        logger.info(f"Группы для подписки: {group_links}")

        # Подписываемся через Telethon
        await subscribe_to_groups(group_links)
        await message.reply("Подписка на группы завершена.")
    except Exception as e:
        logger.error(f"Ошибка при подписке на группы: {e}")
        await message.reply(f"Ошибка: {e}")


@dp.message(F.text == "Добавить группу")
async def add_group_handler(message: Message, state: FSMContext):
    """
    Начало процесса добавления групп.
    """
    logger.info(
        f"Кнопка 'Добавить группу' нажата пользователем {
                message.from_user.id}"
    )
    await message.reply(
        "Введите ссылки на группы, разделённые запятой (пример: https://t.me/group1, https://t.me/group2)."
    )
    await state.set_state(GroupStates.waiting_for_group_links)


@dp.message(GroupStates.waiting_for_group_links)
async def process_group_links(message: Message, state: FSMContext):
    """
    Обработка ввода ссылок на группы.
    """
    logger.info(
        f"Пользователь {
                message.from_user.id} вводит ссылки: {message.text}"
    )
    try:
        # Разделяем ссылки и добавляем в базу данных
        links = [link.strip() for link in message.text.split(",") if link.strip()]
        # Используем функцию add_groups для добавления
        add_groups(",".join(links))

        await message.reply("Группы успешно добавлены.")
        logger.info(f"Добавлены группы: {links}")
    except Exception as e:
        logger.error(f"Ошибка при добавлении групп: {e}")
        await message.reply(f"Ошибка: {e}")
    finally:
        await state.clear()


@dp.message(F.text == "Добавить сообщение")
async def add_message_handler(message: Message):
    """
    Добавление сообщения.
    """
    logger.info(
        f"Кнопка 'Добавить сообщение' нажата пользователем {message.from_user.id}"
    )

    await message.reply("Введите текст сообщения для добавления в базу данных:")


# # Рабочий код отправки сообщений
# @dp.message(BroadcastStates.waiting_for_message)
# async def process_broadcast_message(message: Message, state: FSMContext):
#     """
#     Выполнение рассылки сообщения от имени пользователя.
#     """
#     logger.info(f"Пользователь {message.from_user.id} вводит текст для рассылки: {message.text}")
#     try:
#         # async with db_lock:  # Синхронизация доступа к базе данных
#         #     groups = get_groups_with_subscription()
#         async with db_lock:
#             groups = await get_groups_with_subscription()
#         if not groups:
#             await message.reply("Нет подписанных групп для рассылки.")
#             await state.clear()
#             return

#         broadcast_message = message.text.strip()
#         if not broadcast_message:
#             await message.reply("Сообщение для рассылки не может быть пустым.")
#             await state.clear()
#             return

#         # Авторизация пользователя
#         client = await authorize()

#         # Рассылка сообщений
#         for group in groups:
#             try:
#                 await client.send_message(group[1], broadcast_message)
#                 logger.info(f"Сообщение отправлено в группу: {group[1]}")

#                 # Рандомная пауза с диапазоном из конфига
#                 pause_duration = random.uniform(PAUSE_MIN, PAUSE_MAX)
#                 logger.info(f"Ожидание {pause_duration:.2f} секунд перед следующей отправкой.")
#                 await asyncio.sleep(pause_duration)
#             except Exception as e:
#                 logger.error(f"Ошибка при отправке сообщения в группу {group[1]}: {e}")


#         await message.reply("Рассылка завершена.")
#     except Exception as e:
#         logger.error(f"Ошибка при рассылке: {e}")
#         await message.reply(f"Ошибка при рассылке: {e}")
#     finally:
#         await state.clear()
#         if client:
#             await client.disconnect()  # Отключаем клиента
@dp.message(BroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """
    Выполнение рассылки сообщения от имени пользователя с повторением через заданные интервалы.
    """
    logger.info(
        f"Пользователь {message.from_user.id} вводит текст для рассылки: {message.text}"
    )
    try:
        async with db_lock:
            groups = await get_groups_with_subscription()
        if not groups:
            await message.reply("Нет подписанных групп для рассылки.")
            await state.clear()
            return

        broadcast_message = message.text.strip()
        if not broadcast_message:
            await message.reply("Сообщение для рассылки не может быть пустым.")
            await state.clear()
            return

        # Запрашиваем количество повторений и интервал
        repetitions = 3  # Количество повторений
        interval = 2 * 60 * 60  # Интервал между рассылками в секундах (2 часа)

        for attempt in range(repetitions):
            logger.info(f"Начало рассылки {attempt + 1} из {repetitions}.")
            client = await authorize()  # Авторизация пользователя

            # Рассылка сообщений
            for group in groups:
                try:
                    await client.send_message(group[1], broadcast_message)
                    logger.info(f"Сообщение отправлено в группу: {group[1]}")

                    # Рандомная пауза с диапазоном из конфига
                    pause_duration = random.uniform(PAUSE_MIN, PAUSE_MAX)
                    logger.info(
                        f"Ожидание {pause_duration:.2f} секунд перед следующей отправкой."
                    )
                    await asyncio.sleep(pause_duration)
                except Exception as e:
                    logger.error(
                        f"Ошибка при отправке сообщения в группу {group[1]}: {e}"
                    )

            await client.disconnect()  # Отключаем клиента
            logger.info(f"Рассылка {attempt + 1} завершена.")

            # Если это не последняя итерация, ожидаем перед повторной рассылкой
            if attempt < repetitions - 1:
                logger.info(
                    f"Ожидание {interval // 3600} часов перед следующей рассылкой."
                )
                await asyncio.sleep(interval)

        await message.reply("Все рассылки завершены.")
    except Exception as e:
        logger.error(f"Ошибка при рассылке: {e}")
        await message.reply(f"Ошибка при рассылке: {e}")
    finally:
        await state.clear()


# РАБОЧИЙ
# async def process_broadcast_message(message: Message, state: FSMContext):
#     """
#     Выполнение рассылки сообщения от имени пользователя.
#     """
#     logger.info(
#         f"Пользователь {message.from_user.id} вводит текст для рассылки: {
#             message.text}"
#     )
#     try:
#         # Получаем группы с активной подпиской
#         groups = get_groups_with_subscription()
#         if not groups:
#             await message.reply("Нет подписанных групп для рассылки.")
#             await state.clear()
#             return

#         broadcast_message = message.text.strip()
#         if not broadcast_message:
#             await message.reply("Сообщение для рассылки не может быть пустым.")
#             await state.clear()
#             return

#         # Авторизация пользователя
#         client = await authorize()

#         # Рассылка сообщений
#         for group in groups:
#             try:
#                 await client.send_message(group[1], broadcast_message)
#                 logger.info(f"Сообщение отправлено в группу: {group[1]}")

#                 # Рандомная пауза с диапазоном из конфига
#                 pause_duration = random.uniform(PAUSE_MIN, PAUSE_MAX)
#                 logger.info(
#                     f"Ожидание {
#                         pause_duration:.2f} секунд перед следующей отправкой."
#                 )
#                 await asyncio.sleep(pause_duration)
#             except Exception as e:
#                 logger.error(f"Ошибка при отправке сообщения в группу {group[1]}: {e}")


#         await message.reply("Рассылка завершена.")
#     except Exception as e:
#         logger.error(f"Ошибка при рассылке: {e}")
#         await message.reply(f"Ошибка при рассылке: {e}")
#     finally:
#         await state.clear()
#         if client:
#             await client.disconnect()  # Отключаем клиента


@dp.message(
    F.text
    & ~F.text.in_(
        {
            "Рассылка сообщений",
            "Список сообщений",
            "Список групп",
            "Добавить сообщение",
            "Подписаться на группы",
        }
    )
)
@dp.message(F.text == "Список групп")
async def list_groups_handler(message: Message):
    """
    Отображение списка групп.
    """
    logger.info(
        f"Кнопка 'Список групп' нажата пользователем {
                message.from_user.id}"
    )

    groups = get_groups()
    if groups:
        group_list = "\n".join([f"{g[0]}: {g[1]}" for g in groups])
        await message.reply(f"Список групп:\n{group_list}")
    else:
        await message.reply("Групп пока нет.")


@dp.message(F.text == "Рассылка сообщений")
async def broadcast_handler(message: Message, state: FSMContext):
    """
    Начало обработки команды рассылки сообщения.
    """
    logger.info(
        f"Кнопка 'Рассылка сообщений' нажата пользователем {
            message.from_user.id}"
    )
    await message.reply("Введите текст сообщения для рассылки:")
    await state.set_state(
        BroadcastStates.waiting_for_message
    )  # Устанавливаем состояние


async def main():
    """
    Основная функция запуска бота.
    """
    await bot.delete_webhook(drop_pending_updates=True)  # Очищаем старые апдейты
    await dp.start_polling(bot)  # Запускаем бота


if __name__ == "__main__":
    init_db()
    asyncio.run(main())
