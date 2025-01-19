import asyncio
import json
import os

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import InputFile, KeyboardButton, Message, ReplyKeyboardMarkup
from configuration.logger_setup import logger
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
# BOT_TOKEN = "7299947082:AAF1tvJn9Jl5Op2Co-FQx0KRMlNHtz-CW1k"
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = os.getenv("TABLE_NAME")
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY")
CHANNEL_ID_Models_Free = os.getenv("LOCAL_DIRECTORY")
# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logger.info(BOT_TOKEN)
logger.info(bot)
logger.info(dp)

# Обновлённые кнопки
buttons = [
    "Пост Models FREE",
    "Пост Models PRO",
    "Пост Materials Free",
    "Пост Materials Pro",
    "Загрузить данные",
]


# Функция для создания клавиатуры
def create_main_menu(buttons, row_width=2):
    keyboard = [buttons[i : i + row_width] for i in range(0, len(buttons), row_width)]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=btn) for btn in row] for row in keyboard],
        resize_keyboard=True,
    )


main_menu = create_main_menu(buttons)


@dp.message(Command("start"))
async def start_handler(message: Message):
    logger.info(f"Received message: {message.text}")
    logger.info(f"Команда '/start' вызвана пользователем {message.from_user.id}")
    await message.reply("Привет! Меню доступно.", reply_markup=main_menu)


async def fetch_all_items():
    """
    Извлекает все записи из базы данных.
    :return: Список словарей с данными.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        query = f"""
        SELECT id, base_name, image_name, archive_name, slug, style_en, tags, local_file_search, posting_telegram, title
        FROM {TABLE_NAME}
        """
        async with db.execute(query) as cursor:
            rows = await cursor.fetchall()
            if rows:
                # Преобразуем в список словарей
                return [
                    {
                        "id": row[0],
                        "base_name": row[1],
                        "image_name": row[2],
                        "archive_name": row[3],
                        "slug": row[4],
                        "style_en": row[5],
                        "tags": row[6],
                        "local_file_search": row[7],
                        "posting_telegram": row[8],
                        "title": row[9],
                    }
                    for row in rows
                ]
            return []


def save_to_json(data, filename="temp_data.json"):
    """
    Сохраняет данные в JSON-файл.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Данные успешно записаны в файл {filename}")
    except Exception as e:
        logger.error(f"Ошибка при записи данных в файл: {e}")


@dp.message(lambda message: message.text == "Загрузить данные")
async def load_data_handler(message: Message):
    """
    Обработчик кнопки 'Загрузить данные'.
    Извлекает данные из базы и записывает их в файл.
    """
    logger.info(
        f"Кнопка 'Загрузить данные' нажата пользователем {message.from_user.id}"
    )

    try:
        # Получаем данные из базы данных
        data = await fetch_all_items()
        # logger.info(data)
        if not data:
            logger.info("Нет записей для загрузки.")
            return

        # Сохраняем данные в файл
        temp_file = "temp_data.json"
        save_to_json(data, temp_file)
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")


@dp.message(Command("post_models_free"))
async def handle_post_models_free(message: Message):
    """Пост в группу Models Free."""
    logger.info(
        f"Команда 'post_models_free' вызвана пользователем {message.from_user.id}"
    )
    item = await fetch_next_item()
    if item:
        await post_item_to_channel(item, CHANNEL_ID_Models_Free)
    else:
        await message.reply("Нет доступных записей для публикации.")


@dp.message(Command("post_models_pro"))
async def post_to_models_pro_group_handler(message: Message):
    """
    Обработчик команды для публикации в группе PRO.
    """
    logger.info(
        f"Кнопка 'Пост в группу Models Pro' нажата пользователем {message.from_user.id}"
    )
    await message.reply("Выполняется публикация в группе Models Pro")
    # Здесь добавьте логику для публикации в группу PRO
    await asyncio.sleep(1)  # Имитация работы
    await message.reply("Публикация в группе Models Pro завершена!")


@dp.message(lambda message: message.text == "Пост в группе Models Free")
async def free_group_button_handler(message: Message):
    """
    Обработчик кнопки 'Пост в группе Models Free'.
    """
    logger.info(
        f"Кнопка 'Пост в группе Models Free' нажата пользователем {message.from_user.id}"
    )
    await post_to_models_free_group_handler(message)


@dp.message(lambda message: message.text == "Пост в группе Models PRO")
async def pro_group_button_handler(message: Message):
    """
    Обработчик кнопки 'Пост в группе Models PRO'.
    """
    logger.info(
        f"Кнопка 'Пост в группе Models PRO' нажата пользователем {message.from_user.id}"
    )
    await post_to_models_pro_group_handler(message)


@dp.message(Command("post_materials_free"))
async def post_to_materials_free_group_handler(message: Message):
    """
    Обработчик команды для публикации в группе Materials Free
    """
    logger.info(
        f"Кнопка 'Пост в группу Materials Free' нажата пользователем {message.from_user.id}"
    )
    await message.reply("Выполняется публикация в группе Materials Free")
    # Здесь добавьте логику для публикации в группу Materials Free
    await asyncio.sleep(1)  # Имитация работы
    await message.reply("Публикация в группе Materials Free завершена!")


@dp.message(Command("post_materials_pro"))
async def post_to_materials_pro_group_handler(message: Message):
    """
    Обработчик команды для публикации в группе PRO.
    """
    logger.info(
        f"Кнопка 'Пост в группу Materials Pro' нажата пользователем {message.from_user.id}"
    )
    await message.reply("Выполняется публикация в группе Materials Pro")
    # Здесь добавьте логику для публикации в группу Materials PRO
    await asyncio.sleep(1)  # Имитация работы
    await message.reply("Публикация в группе Materials Pro завершена!")


@dp.message(lambda message: message.text == "Пост в группе Materials Free")
async def materials_free_group_button_handler(message: Message):
    """
    Обработчик кнопки 'Пост в группе Materials Free'.
    """
    logger.info(
        f"Кнопка 'Пост в группе Materials Free' нажата пользователем {message.from_user.id}"
    )
    await materials_free_group_button_handler(message)


@dp.message(lambda message: message.text == "Пост в группе Materials PRO")
async def materials_pro_group_button_handler(message: Message):
    """
    Обработчик кнопки 'Пост в группе Materials PRO'.
    """
    logger.info(
        f"Кнопка 'Пост в группе Materials PRO' нажата пользователем {message.from_user.id}"
    )
    await materials_pro_group_button_handler(message)


# Функция для поста
async def post_item_to_channel(item, channel_id):
    """
    Публикует фото в канал с подписью, если файл найден и posting_telegram = False.

    :param item: Словарь с данными для публикации.
    :param channel_id: ID канала для публикации.
    """
    try:
        if item["posting_telegram"]:
            logger.info(f"Запись {item['id']} уже опубликована. Пропускаем.")
            return

        # Формируем путь к изображению
        image_path = os.path.join(LOCAL_DIRECTORY, item["image_name"])

        # Проверяем, существует ли файл
        if not os.path.exists(image_path):
            logger.error(f"Файл изображения не найден: {image_path}")
            return

        # Создаём подпись для поста
        caption = f"{item['title']}\n\nСтиль: {item['style_en']}\nТеги: {item['tags']}"

        # Публикуем фото в канал
        photo = InputFile(image_path)
        await bot.send_photo(chat_id=channel_id, photo=photo, caption=caption)

        # Отмечаем запись как опубликованную (обновление в базе данных)
        await mark_as_posted(item["id"])
        logger.info(f"Запись {item['id']} опубликована в канале.")

    except Exception as e:
        logger.error(f"Ошибка при публикации записи {item['id']}: {e}")


# Функция для обновление в БД о посте
async def mark_as_posted(record_id):
    """
    Отмечает запись как опубликованную в базе данных.

    :param record_id: ID записи для обновления.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        query = f"UPDATE {TABLE_NAME} SET posting_telegram = 1 WHERE id = ?"
        await db.execute(query, (record_id,))
        await db.commit()
        logger.info(f"Запись с ID {record_id} отмечена как опубликованная.")


async def main():
    """
    Основная функция запуска бота.
    """
    await bot.delete_webhook(drop_pending_updates=True)  # Очищаем старые апдейты
    logger.info("Бот запускается...")
    await dp.start_polling(bot)  # Запускаем бота


if __name__ == "__main__":
    asyncio.run(main())
