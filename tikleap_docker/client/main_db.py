import json
import sqlite3
import sys
from pathlib import Path

from loguru import logger

# Настройка директорий и логирования
# Настройка путей
current_directory = Path.cwd()

config_directory = current_directory / "config"

json_directory = current_directory / "json"
db_directory = current_directory / "db"
log_directory = current_directory / "log"

db_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)


output_json_file = json_directory / "output.json"
config_file = config_directory / "config.json"
log_file_path = log_directory / "log_message.log"
db_path = db_directory / "tikleap_users.db"


logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)


# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


def get_config(file):
    """Загружает конфигурацию из JSON файла."""
    with open(file, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


# Загрузка конфигурации
config = get_config(config_file)


def save_users_to_sqlite(users_data):
    """
    Функция для сохранения данных о пользователях в SQLite базу данных

    Args:
        users_data (list): Список словарей с данными пользователей
        db_path (str or Path, optional): Путь к файлу базы данных
    """
    try:
        if not users_data:
            logger.warning("Нет данных для сохранения в базу данных")
            return
        logger.info(f"Сохранение данных в базу данных: {db_path}")

        # Подключаемся к БД
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Создаем таблицу, если она не существует
        cursor.execute(
            """
        CREATE TABLE IF NOT EXISTS tikleap_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_datetime TEXT,
            country_code TEXT,
            profile_link TEXT UNIQUE,
            rank INTEGER,
            earning TEXT,
            loading_table BOOLEAN DEFAULT 0
        )
        """
        )

        # Добавляем или обновляем данные пользователей
        added_count = 0
        updated_count = 0

        for user in users_data:
            try:
                # Проверяем валидность данных
                if not user.get("profile_link"):
                    logger.warning("Пропуск записи: отсутствует profile_link")
                    continue

                # Преобразуем rank в int с обработкой ошибок
                try:
                    rank = int(user.get("rank", 0))
                except (ValueError, TypeError):
                    logger.warning(
                        f"Неверный формат rank для {user.get('profile_link')}, устанавливаем 0"
                    )
                    rank = 0

                # Проверяем, существует ли уже такой пользователь
                cursor.execute(
                    "SELECT * FROM tikleap_users WHERE profile_link = ?",
                    (user["profile_link"],),
                )
                existing_user = cursor.fetchone()

                if existing_user:
                    # Обновляем информацию о пользователе
                    cursor.execute(
                        """
                    UPDATE tikleap_users SET 
                        current_datetime = ?,
                        country_code = ?,
                        rank = ?,
                        earning = ?
                    WHERE profile_link = ?
                    """,
                        (
                            user["current_datetime"],
                            user["country_code"],
                            rank,
                            user["earning"],
                            user["profile_link"],
                        ),
                    )
                    updated_count += 1
                else:
                    # Добавляем нового пользователя
                    cursor.execute(
                        """
                    INSERT INTO tikleap_users 
                    (current_datetime, country_code, profile_link, rank, earning, loading_table) 
                    VALUES (?, ?, ?, ?, ?, 0)
                    """,
                        (
                            user["current_datetime"],
                            user["country_code"],
                            user["profile_link"],
                            rank,
                            user["earning"],
                        ),
                    )
                    added_count += 1
            except Exception as e:
                logger.error(
                    f"Ошибка при обработке пользователя {user.get('profile_link', 'Unknown')}: {e}"
                )

        # Сохраняем изменения
        conn.commit()

        # Выводим статистику
        logger.success(
            f"Данные успешно сохранены в БД: добавлено {added_count}, обновлено {updated_count} записей"
        )

        # Получаем общее количество записей в базе
        cursor.execute("SELECT COUNT(*) FROM tikleap_users")
        total_count = cursor.fetchone()[0]
        logger.info(f"Всего записей в базе данных: {total_count}")

        # Получаем количество записей, готовых к выгрузке
        cursor.execute("SELECT COUNT(*) FROM tikleap_users WHERE loading_table = 0")
        unloaded_count = cursor.fetchone()[0]
        logger.info(f"Ожидают выгрузки в Google Sheets: {unloaded_count} записей")

        # Закрываем соединение с БД
        conn.close()

    except Exception as e:
        logger.error(f"Ошибка при сохранении данных в базу данных: {e}")
        logger.exception("Подробная информация об ошибке:")


def save_user_to_sqlite_online(user, db_path=None):
    """
    Функция для сохранения одного пользователя в SQLite базу данных (онлайн режим)

    Args:
        user (dict): Словарь с данными пользователя
        db_path (str or Path, optional): Путь к файлу базы данных
    """
    try:
        if not user:
            logger.warning("Нет данных для сохранения в базу данных")
            return

        # logger.debug(
        #     f"Сохранение пользователя в БД: {user.get('profile_link', 'Unknown')}"
        # )

        # Подключаемся к БД
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Создаем таблицу если не существует (упрощенная версия для совместимости)
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tikleap_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                current_datetime TEXT,
                country_code TEXT,
                rank INTEGER,
                profile_link TEXT UNIQUE,
                earning TEXT,
                loading_table BOOLEAN DEFAULT 0
            )
            """
        )

        # Проверяем валидность данных
        if not user.get("profile_link"):
            logger.warning("Пропуск записи: отсутствует profile_link")
            return

        # Преобразуем rank в int с обработкой ошибок
        try:
            rank = int(user.get("rank", 0))
        except (ValueError, TypeError):
            logger.warning(
                f"Неверный формат rank для {user.get('profile_link')}, устанавливаем 0"
            )
            rank = 0

        # Проверяем, существует ли уже такой пользователь
        cursor.execute(
            "SELECT id FROM tikleap_users WHERE profile_link = ?",
            (user["profile_link"],),
        )
        existing_user = cursor.fetchone()

        if existing_user:
            # Обновляем информацию о пользователе
            cursor.execute(
                """
                UPDATE tikleap_users SET 
                    current_datetime = ?,
                    country_code = ?,
                    rank = ?,
                    earning = ?
                WHERE profile_link = ?
                """,
                (
                    user.get("current_datetime", ""),
                    user.get("country_code", ""),
                    rank,
                    user.get("earning", ""),  # Исправлено: было user["earning"]
                    user["profile_link"],
                ),
            )
            # logger.debug(f"Обновлен пользователь: {user['profile_link']}")
        else:
            # Добавляем нового пользователя
            cursor.execute(
                """
                INSERT INTO tikleap_users 
                (current_datetime, country_code, profile_link, rank, earning, loading_table) 
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (
                    user.get("current_datetime", ""),
                    user.get("country_code", ""),
                    user["profile_link"],
                    rank,
                    user.get("earning", ""),  # Исправлено: было user["earning"]
                ),
            )
            logger.debug(f"Добавлен новый пользователь: {user['profile_link']}")

        # Сохраняем изменения
        conn.commit()

        # Закрываем соединение с БД
        conn.close()

    except Exception as e:
        logger.error(
            f"Ошибка при сохранении пользователя {user.get('profile_link', 'Unknown')}: {e}"
        )
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
