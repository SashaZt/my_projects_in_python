import asyncio
import json
import os
import re
from pathlib import Path

import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import FSInputFile, KeyboardButton, Message, ReplyKeyboardMarkup
from configuration.logger_setup import logger
from dotenv import load_dotenv

env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = os.getenv("TABLE_NAME")
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY")

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
temp_data_file = current_directory / "temp_data.json"

# Создаём бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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
    logger.info(f"Команда '/start' вызвана пользователем {message.from_user.id}")
    await message.reply("Привет! Меню доступно.", reply_markup=main_menu)


async def fetch_all_items():
    """
    Извлекает все записи из базы данных.
    :return: Список словарей с данными.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        query = f"""
            SELECT id, base_name, image_name, archive_name, slug, style_en, tags, local_file_search, posting_telegram, title, category
            FROM {TABLE_NAME}
            WHERE posting_telegram = 0
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
                        "category": row[10],
                    }
                    for row in rows
                ]
            return []


def save_to_json(data, filename):
    """
    Сохраняет данные в JSON-файл.
    :param data: Данные для сохранения.
    :param filename: Путь к файлу.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Данные успешно записаны в файл {filename}")
    except Exception as e:
        logger.error(f"Ошибка при записи данных в файл {filename}: {e}")


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
        data_items = await fetch_all_items()
        # logger.info(data)
        if not data_items:
            if temp_data_file.exists():
                temp_data_file.unlink()  # Удаляем файл, если он существует
                logger.info("Нет записей для загрузки.")
                return
        # Логируем количество загруженных записей
        logger.info(f"Загружено {len(data_items)} записей.")

        # Сохраняем данные в файл
        save_to_json(data_items, temp_data_file)
        logger.info("Данные успешно сохранены в JSON.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")


@dp.message(lambda message: message.text.startswith("Пост "))
async def universal_post_handler(message: Message):
    """
    Универсальный обработчик кнопок публикации.
    Определяет канал и публикует данные на основе выбора.
    """

    # Карта каналов и данных
    channel_map = {
        "Пост Models FREE": {
            "channel_id": os.getenv("CHANNEL_ID_MODELS_FREE"),
            "filter": lambda item: not item[
                "posting_telegram"
            ],  # Фильтруем только по posting_telegram
        },
        "Пост Models PRO": {
            "channel_id": os.getenv("CHANNEL_ID_MODELS_PRO"),
            "filter": lambda item: not item[
                "posting_telegram"
            ],  # Фильтруем только по posting_telegram
        },
        "Пост Materials Free": {
            "channel_id": os.getenv("CHANNEL_ID_MATERIALS_FREE"),
            "filter": lambda item: not item[
                "posting_telegram"
            ],  # Фильтруем только по posting_telegram
        },
        "Пост Materials Pro": {
            "channel_id": os.getenv("CHANNEL_ID_MATERIALS_PRO"),
            "filter": lambda item: not item[
                "posting_telegram"
            ],  # Фильтруем только по posting_telegram
        },
    }

    # Определяем канал и фильтр по тексту команды
    channel_data = channel_map.get(message.text)
    if not channel_data:
        await message.reply("Неизвестная команда.")
        logger.error(f"Не удалось определить канал для команды: {message.text}")
        return

    channel_id = channel_data["channel_id"]
    data_filter = channel_data["filter"]

    logger.info(f"Публикация в канал {channel_id} начата...")

    # Загружаем данные из JSON
    data = fetch_json()
    if not data:
        await message.reply("Нет доступных записей для публикации.")
        return

    # Фильтруем данные
    items_to_post = [item for item in data if data_filter(item)]
    if not items_to_post:
        await message.reply("Нет записей, соответствующих критериям публикации.")
        return

    # Публикуем записи
    for item in items_to_post:
        await post_item_to_channel(item, channel_id)

    # Сохраняем обновления в JSON
    await message.reply("Публикация завершена.")


def fetch_json():
    """Считывает данные из JSON-файла."""
    try:
        with open(temp_data_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            logger.info("Данные успешно загружены из JSON.")
            return data
    except Exception as e:
        logger.error(f"Ошибка чтения JSON-файла: {e}")
        return []


def save_json(data):
    """Сохраняет данные в JSON-файл."""
    try:
        with open(temp_data_file, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            logger.info("Данные успешно сохранены в JSON.")
    except Exception as e:
        logger.error(f"Ошибка сохранения JSON-файла: {e}")


async def post_item_to_channel(item, channel_id):
    """Публикует фото в канал с подписью."""
    try:
        """
        Работа с изображением
        """
        # Формируем и нормализуем путь к изображению
        image_path = os.path.normpath(os.path.join(LOCAL_DIRECTORY, item["image_name"]))

        logger.info(f"Путь к файлу: {image_path}")

        # Проверяем существование файла
        if not os.path.exists(image_path):
            logger.error(f"Файл изображения не найден: {image_path}")
            return
        base_name = item["base_name"]
        title = item["title"]
        style_en = f'#{item["style_en"]}'
        # logger.info(item["category"])
        category = " ".join(
            f"#{word.strip()}"
            for word in re.split(r"[^\w]+", item["category"])
            if word.strip()
        )

        tags = (
            " ".join(
                f"#{tag.strip().replace(' ', '_')}" for tag in item["tags"].split(",")
            )
            if isinstance(item["tags"], str)
            else ""
        )

        base_tags = "#3dsky #3ddd"
        # Формируем подпись для поста
        caption = f"{base_name}\n{title}\n{style_en}\n{category}\n{tags}\n{base_tags}"

        # Публикуем фото в канал
        photo = FSInputFile(image_path)  # Используем FSInputFile для локальных файлов
        await bot.send_photo(chat_id=channel_id, photo=photo, caption=caption)

        # Формируем и нормализуем путь к архиву
        archive_path = os.path.normpath(
            os.path.join(LOCAL_DIRECTORY, item["archive_name"])
        )
        """
        Работа с архивом
        """
        # Формируем и нормализуем путь к архиву
        archive_path = os.path.normpath(
            os.path.join(LOCAL_DIRECTORY, item["archive_name"])
        )

        # logger.info(f"Путь к файлу: {archive_path}")

        # Проверяем существование файла
        if not os.path.exists(archive_path):
            logger.error(f"Файл архива не найден: {archive_path}")
            return

        # Публикуем архив в канал
        archive = FSInputFile(
            archive_path
        )  # Используем FSInputFile для локальных файлов
        await bot.send_document(chat_id=channel_id, document=archive)

        # Отмечаем запись как опубликованную
        await update_posting_telegram(base_name, True)
        # item["posting_telegram"] = True
        # logger.info(f"Запись {item['id']} опубликована в канале {channel_id}.")

    except Exception as e:
        logger.error(f"Ошибка при публикации записи {item['id']}: {e}")


async def update_posting_telegram(base_name: str, posting_telegram: bool):
    """
    Обновляет поле posting_telegram для строки с указанным base_name.

    :param base_name: Значение base_name для поиска записи.
    :param posting_telegram: Новое значение для поля posting_telegram.
    """
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            query = f"""
                UPDATE {TABLE_NAME}
                SET posting_telegram = ?
                WHERE base_name = ?
            """
            await db.execute(query, (posting_telegram, base_name))
            await db.commit()
            # logger.info(
            #     f"Запись с base_name = {base_name} обновлена: posting_telegram = {posting_telegram}"
            # )
    except Exception as e:
        logger.error(f"Ошибка при обновлении записи: {e}")


async def main():
    """
    Основная функция запуска бота.
    """
    await bot.delete_webhook(drop_pending_updates=True)  # Очищаем старые апдейты
    logger.info("Бот запускается...")
    await dp.start_polling(bot)  # Запускаем бота


if __name__ == "__main__":
    asyncio.run(main())
