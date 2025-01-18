import os
import shutil
import sqlite3
from pathlib import Path

import requests
from configuration.logger_setup import logger
from dotenv import load_dotenv
from py7zr import FILTER_LZMA2, SevenZipFile

env_path = os.path.join(os.getcwd(), "configuration", ".env")
# Загружаем конфигурацию из .env
load_dotenv(env_path)
LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "./data")
ARCHIVE_FORMAT = "7z"  # Зафиксировали формат, чтобы избежать ошибок
DB_NAME = os.getenv("DB_NAME", "default.db")
TABLE_NAME = os.getenv("TABLE_NAME", "default_table")
cookies = {
    "besrv": "app56",
    "CookieConsent_en": "1%7C1766079412",
    "PHPSESSID": "b81c565f6d0e14a859e3fe6540cd7daf",
}
headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/json",
    "dnt": "1",
    "expires": "Sat, 01 Jan 2000 00:00:00 GMT",
    "origin": "https://3dsky.org",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://3dsky.org/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def find_first_file(directory, extensions):
    """
    Ищет первый файл в указанной директории с заданными расширениями.
    """
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(extensions):
                return os.path.join(root, file)
    return None


def archive_directory(directory):
    """
    Архивирует директорию в .7z с максимальным сжатием.
    """
    archive_path = f"{directory}.7z"
    try:
        compression_filters = [
            {
                "id": FILTER_LZMA2,  # Используем LZMA2 для .7z
                "preset": 0,  # Максимальный уровень сжатия
            }
        ]
        with SevenZipFile(archive_path, "w", filters=compression_filters) as seven_zip:
            seven_zip.writeall(directory)
        return archive_path
    except Exception as e:
        logger.error(f"Ошибка архивирования: {e}")
        return None


def process_all_files():
    """
    Проверяет все картинки в директории и их соответствующие архивы.
    Если архива нет, ищет папку с таким же именем и архивирует её.
    """
    image_extensions = (".jpg", ".png", ".jpeg")
    archive_extensions = (".zip", ".rar", ".7z")

    # Получаем список base_name из базы данных, где local_file_search = 1
    processed_base_names = get_processed_base_names()

    # Получаем список всех картинок
    images = [
        os.path.join(LOCAL_DIRECTORY, file)
        for file in os.listdir(LOCAL_DIRECTORY)
        if file.lower().endswith(image_extensions)
    ]
    if not images:
        logger.error("Картинки не найдены.")
        return

    for image_path in images:

        # Извлекаем имя файла без расширения
        base_name = Path(image_path).stem

        # Пропускаем обработку, если base_name уже в обработанных
        if base_name in processed_base_names:
            logger.info(f"Картинка с base_name {base_name} уже обработана. Пропускаем.")
            continue
        # Проверяем, существует ли архив
        archive_path = next(
            (
                os.path.join(LOCAL_DIRECTORY, f"{base_name}{ext}")
                for ext in (".zip", ".rar", ".7z")
                if os.path.exists(os.path.join(LOCAL_DIRECTORY, f"{base_name}{ext}"))
            ),
            None,
        )

        if archive_path:
            logger.info(f"Найден архив: {archive_path}")
            # Извлечение ссылку на продукт
            slug = fetch_slug_from_3dsky(base_name)
            if not slug:
                logger.warning(f"На сайте 3dsky.org нету данных на: {base_name}")
                continue
            # Извлечение стиль на продукт
            style_en = fetch_styles_from_3dsky(slug)
            # Извлечение теги продукта
            tags = fetch_tags_from_3dsky(base_name)
            # Если есть все три значения, записываем в БД
            if slug and style_en and tags:
                update_local_file_search(base_name, slug, style_en, tags)
            continue  # Переходим к следующей картинке
        else:
            # Если архива нет, проверяем, существует ли папка с таким именем
            folder_path = os.path.join(LOCAL_DIRECTORY, base_name)
            if os.path.isdir(folder_path):
                logger.info(f"Найдена папка для архивирования: {folder_path}")
                archive_path = archive_directory(folder_path)
                if archive_path:
                    logger.info(f"Создан архив: {archive_path}")
                    # Извлечение ссылку на продукт
                    slug = fetch_slug_from_3dsky(base_name)
                    if not slug:
                        logger.warning(f"Нету данных на: {base_name}")
                        continue
                    # Извлечение стиль на продукт
                    style_en = fetch_styles_from_3dsky(slug)
                    # Извлечение теги продукта
                    tags = fetch_tags_from_3dsky(base_name)
                    # Если есть все три значения, записываем в БД
                    if slug and style_en and tags:
                        update_local_file_search(base_name, slug, style_en, tags)
                else:
                    logger.error(f"Ошибка при архивировании папки: {folder_path}")
            else:
                logger.error(f"Папки и архива с именем {base_name} не найдена.")
        # # Проверяем, существует ли архив в любом формате
        # archive_found = any(
        #     os.path.exists(os.path.join(LOCAL_DIRECTORY, f"{base_name}{ext}"))
        #     for ext in archive_extensions
        # )

        # if archive_found:
        #     # Извлечение ссылку на продукт
        #     slug = fetch_slug_from_3dsky(base_name)
        #     if not slug:
        #         logger.warning(f"Нету данных на: {base_name}")
        #         continue
        #     # Извлечение стиль на продукт
        #     style_en = fetch_styles_from_3dsky(slug)
        #     # Извлечение теги продукта
        #     tags = fetch_tags_from_3dsky(base_name)
        #     # Если есть все три значения, записываем в БД
        #     if slug and style_en and tags:
        #         update_local_file_search(base_name, slug, style_en, tags)
        #     continue  # Переходим к следующей картинке

        # # Если архива нет, проверяем, существует ли папка с таким именем
        # folder_path = os.path.join(LOCAL_DIRECTORY, base_name)
        # if os.path.isdir(folder_path):
        #     logger.info(f"Найдена папка для архивирования: {folder_path}")
        #     archive_path = archive_directory(folder_path)
        #     if archive_path:
        #         logger.info(f"Создан архив: {archive_path}")
        #         # Извлечение ссылку на продукт
        #         slug = fetch_slug_from_3dsky(base_name)
        #         if not slug:
        #             logger.warning(f"Нету данных на: {base_name}")
        #             continue
        #         # Извлечение стиль на продукт
        #         style_en = fetch_styles_from_3dsky(slug)
        #         # Извлечение теги продукта
        #         tags = fetch_tags_from_3dsky(base_name)
        #         # Если есть все три значения, записываем в БД
        #         if slug and style_en and tags:
        #             update_local_file_search(base_name, slug, style_en, tags)
        #         continue  # Переходим к следующей картинке
        #     else:
        #         logger.error(f"Ошибка при архивировании папки: {folder_path}")
        # else:
        #     logger.error(f"Папка с именем {base_name} не найдена.")


def fetch_tags_from_3dsky(query):
    """
    Выполняет POST-запрос к API 3dsky.org и возвращает список title из data.

    :param slug: Идентификатор модели (значение для 'slug' в запросе)
    :return: Список значений title из data
    """
    json_data = {
        "query": query,
        "order": "relevance",
    }

    try:

        response = requests.post(
            "https://3dsky.org/api/tag_cloud",
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30,
        )

        response.raise_for_status()  # Проверяем на ошибки HTTP
        data = response.json()

        if data.get("status") == 200 and "data" in data:
            tags = data["data"].get("tagsEn", [])
            return tags
        else:
            raise ValueError(
                f"Ошибка в ответе API: {data.get('message', 'Неизвестная ошибка')}"
            )
    except requests.RequestException as e:
        logger.error(f"Ошибка выполнения запроса: {e}")
        return []
    except ValueError as e:
        logger.error(e)
        return []


def fetch_styles_from_3dsky(slug):
    """
    Выполняет POST-запрос к API 3dsky.org и возвращает список title из data.

    :param slug: Идентификатор модели (значение для 'slug' в запросе)
    :return: Список значений title из data
    """
    json_data = {
        "slug": slug,
    }
    logger.info(slug)
    try:
        response = requests.post(
            "https://models.3dsky.org/api/models/show",
            headers=headers,
            json=json_data,
            timeout=30,
        )

        response.raise_for_status()  # Проверяем на ошибки HTTP
        data = response.json()

        if data.get("success") and "data" in data:
            style_en = data["data"]["style_en"]
            return style_en
        else:
            raise ValueError(
                f"Ошибка в ответе API: {data.get('message', 'Неизвестная ошибка')}"
            )
    except requests.RequestException as e:
        logger.error(f"Ошибка выполнения запроса {slug}: {e}")
        return []
    except ValueError as e:
        logger.error(e)
        return []


def fetch_slug_from_3dsky(query):
    """
    Выполняет POST-запрос к API 3dsky.org и возвращает список title из data.

    :param slug: Идентификатор модели (значение для 'slug' в запросе)
    :return: Список значений title из data
    """
    json_data = {
        "query": query,
        "order": "relevance",
    }
    try:
        response = requests.post(
            "https://3dsky.org/api/models",
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30,
        )
        response.raise_for_status()  # Проверяем на ошибки HTTP
        data = response.json()
        if data.get("status") == 200 and "data" in data:
            data = data["data"]
            models = data.get("models", [])

            if models:
                model = models[0]  # Берем первую модель
                slug = model.get("slug")
                return slug
            # else:
            #     logger.warning("Список models пуст.")
        else:
            logger.error(
                f"Ошибка в ответе API: {data.get('message', 'Неизвестная ошибка')}"
            )
    except requests.RequestException as e:
        logger.error(f"Ошибка выполнения запроса: {e}")
        return []
    except ValueError as e:
        logger.error(e)
        return []


def update_local_file_search(base_name, slug, style_en, tags):
    """
    Обновляет запись в таблице: если запись с указанным base_name существует, обновляет её.
    Если записи нет, добавляет её с указанными данными.

    :param base_name: Имя для поиска записи (base_name).
    :param slug: Уникальный идентификатор модели (slug).
    :param style_en: Стиль модели (style_en).
    :param tags: Теги для модели (список).
    """
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Убедимся, что tags — это список, даже если пустой
        if not tags:
            tags = []
        elif not isinstance(tags, list):
            raise ValueError("Tags должны быть списком.")

        # Преобразуем список tags в строку
        tags_str = ",".join(tags)

        # Проверка существования записи с указанным base_name
        cursor.execute(
            f"""
        SELECT id FROM {TABLE_NAME}
        WHERE base_name = ?
        """,
            (base_name,),
        )

        record = cursor.fetchone()

        if record:
            # Если запись существует, обновляем её
            cursor.execute(
                f"""
            UPDATE {TABLE_NAME}
            SET slug = ?, style_en = ?, tags = ?, local_file_search = 1
            WHERE id = ?
            """,
                (slug, style_en, tags_str, record[0]),
            )
            conn.commit()
            logger.info(
                f"Обновлена запись с id = {record[0]}: base_name = {base_name}, slug = {slug}, style_en = {style_en}, tags = {tags_str}"
            )
        else:
            # Если записи нет, добавляем новую запись
            cursor.execute(
                f"""
            INSERT INTO {TABLE_NAME} (base_name, slug, style_en, tags, local_file_search, posting_telegram)
            VALUES (?, ?, ?, ?, 1, 0)
            """,
                (base_name, slug, style_en, tags_str),
            )
            conn.commit()
            logger.info(
                f"Добавлена новая запись: base_name = {base_name}, slug = {slug}, style_en = {style_en}, tags = {tags_str}"
            )
    except ValueError as ve:
        logger.error(f"Ошибка в переданных данных: {ve}")
    except sqlite3.Error as e:
        logger.error(f"Ошибка работы с базой данных: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Соединение с базой данных закрыто.")

            # logger.info("Соединение с базой данных закрыто.")


def get_processed_base_names():
    """
    Подключается к базе данных и извлекает все base_name, где local_file_search = 1.
    :return: Список base_name.
    """
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Извлекаем base_name, где local_file_search = 1
        cursor.execute(
            f"""
        SELECT base_name FROM {TABLE_NAME} WHERE local_file_search = 1
        """
        )
        records = cursor.fetchall()

        # Преобразуем результат в список
        processed_base_names = [record[0] for record in records]
        return processed_base_names
    except sqlite3.Error as e:
        logger.error(f"Ошибка при чтении базы данных: {e}")
        return []
    finally:
        if conn:
            conn.close()


def initialize_database():
    """
    Создаёт базу данных и таблицу, если они ещё не существуют.
    Структура таблицы:
        - id (INTEGER PRIMARY KEY AUTOINCREMENT)
        - base_name (TEXT)
        - slug (TEXT)
        - style_en (TEXT)
        - tags (TEXT)
        - local_file_search (BOOLEAN, default False)
        - posting_telegram (BOOLEAN, default False)
    """
    try:
        # Подключение к базе данных
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Создание таблицы, если она не существует
        cursor.execute(
            f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_name TEXT NOT NULL,
            slug TEXT,
            style_en TEXT,
            tags TEXT,
            local_file_search BOOLEAN DEFAULT 0,
            posting_telegram BOOLEAN DEFAULT 0
        )
        """
        )
        conn.commit()
        logger.info(
            f"База данных '{DB_NAME}' и таблица '{TABLE_NAME}' успешно инициализированы."
        )
    except sqlite3.Error as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    initialize_database()
    process_all_files()
