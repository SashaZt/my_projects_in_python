import asyncio
import datetime
import json
import random
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import gspread
import schedule
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
from loguru import logger
from main_db import save_user_to_sqlite_online, save_users_to_sqlite
from main_sheets import export_unloaded_users_to_google_sheets, get_column_b_data
from rnet import Client, Impersonate

# Настройка директорий и логирования
# Настройка путей
current_directory = Path.cwd()
parent_directory = current_directory.parent

cookies_directory = parent_directory / "cookies"
cookies_file = cookies_directory / "cookies_important.json"

config_directory = current_directory / "config"

json_directory = current_directory / "json"
log_directory = current_directory / "log"
db_directory = current_directory / "db"


db_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)


output_json_file = json_directory / "output.json"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"
log_file_path = log_directory / "log_message.log"
db_path = db_directory / "tikleap_users.db"

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=1, i",
    "referer": "https://www.tikleap.com/country/kz",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

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
cookies = get_config(cookies_file)
cookies_dict = cookies["cookies"]

# countries = config["country"]


def get_random_pause(min_seconds, max_seconds):
    """
    Возвращает случайное число секунд для паузы в заданном диапазоне

    Args:
        min_seconds (int/float): Минимальное количество секунд
        max_seconds (int/float): Максимальное количество секунд

    Returns:
        float: Случайное число секунд для паузы

    Examples:
        >>> pause = get_random_pause(2, 5)
        >>> print(f"Пауза: {pause:.2f} секунд")

        >>> # Использование с time.sleep
        >>> time.sleep(get_random_pause(1, 3))

        >>> # Использование с asyncio.sleep
        >>> await asyncio.sleep(get_random_pause(0.5, 2.0))
    """
    if min_seconds > max_seconds:
        min_seconds, max_seconds = max_seconds, min_seconds
        logger.warning(f"⚠️ Поменял местами min и max: {min_seconds} - {max_seconds}")

    if min_seconds < 0:
        min_seconds = 0
        logger.warning(
            "⚠️ Минимальная пауза не может быть отрицательной, установлена в 0"
        )

    pause_duration = random.uniform(min_seconds, max_seconds)
    logger.debug(
        f"🎲 Случайная пауза: {pause_duration:.2f} секунд ({min_seconds}-{max_seconds})"
    )

    return pause_duration


async def async_random_pause(min_seconds, max_seconds):
    """
    Асинхронная функция: выполняет случайную паузу в заданном диапазоне

    Args:
        min_seconds (int/float): Минимальное количество секунд
        max_seconds (int/float): Максимальное количество секунд

    Examples:
        >>> await async_random_pause(1, 3)  # Асинхронная пауза от 1 до 3 секунд
        >>> await async_random_pause(2.5, 5.0)  # Асинхронная пауза от 2.5 до 5 секунд
    """
    pause_duration = get_random_pause(min_seconds, max_seconds)
    logger.info(f"😴 Асинхронная пауза {pause_duration:.2f} секунд...")
    await asyncio.sleep(pause_duration)


async def response_methods():
    """Основная функция для сбора данных"""
    client = Client(impersonate=Impersonate.Chrome137)
    all_users_data = []

    try:
        logger.info("Обновили данные из БД")
        export_unloaded_users_to_google_sheets()
        countries = get_column_b_data()
        logger.info(f"Начинаем обработку стран: {countries}")
        # Обрабатываем каждую страну
        for country in countries:
            logger.info(f"🌍 Обрабатываем страну: {country}")
            country_users = []

            # Обрабатываем страницы для текущей страны
            for page in range(1, 6):
                logger.info(f"📄 Загружаем страницу {page} для страны {country}")

                response = await client.get(
                    f"https://www.tikleap.com/country-load-more/{country}/{page}",
                    cookies=cookies_dict,
                    headers=headers,
                )
                if response.ok:
                    logger.info(f"Status Code: {response.status_code}")

                    json_content = await response.json()
                    # Сохраняем JSON файл для каждой страницы
                    file_name = json_directory / f"{country}_page_{page:02d}.json"
                    with open(file_name, "w", encoding="utf-8") as f:
                        json.dump(json_content, f, ensure_ascii=False, indent=4)
                    logger.success(f"💾 Сохранен файл: {file_name}")

                    # Парсим данные пользователей
                    page_users = parse_users_data(json_content, country)
                    for user in page_users:
                        save_user_to_sqlite_online(user, db_path)
                    country_users.extend(page_users)
                    all_users_data.extend(page_users)

                    logger.info(
                        f"✅ Страница {page}: найдено {len(page_users)} пользователей"
                    )

                    # Пауза между запросами
                    await async_random_pause(10, 15)
                else:
                    logger.info(response.status_code)
            # Пауза между странами
            logger.info(
                f"🏁 Завершена обработка страны {country}. Найдено {len(country_users)} пользователей"
            )
            await async_random_pause(15, 30)

        # Сохраняем все данные в один общий файл
        logger.info(f"💾 Сохраняем все данные в файл: {output_json_file}")
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump(all_users_data, f, ensure_ascii=False, indent=4)

        logger.success(
            f"🎉 Обработка завершена! Всего пользователей: {len(all_users_data)}"
        )
        # Записываем все данные сразу
        # save_users_to_sqlite(all_users_data)

        export_unloaded_users_to_google_sheets()
        return all_users_data

    except Exception as e:
        logger.error(f"💥 Критическая ошибка в response_methods: {e}")
        return []

    finally:
        # Закрываем клиент (если поддерживается)
        try:
            await client.close()
        except:
            pass


def parse_users_data(json_content, country_code):
    """
    Парсит данные пользователей из HTML-контента

    Args:
        json_content (dict): JSON-данные с HTML-контентом
        country_code (str): Код страны

    Returns:
        list: Список словарей с данными пользователей
    """
    users_data = []
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Извлекаем HTML из JSON
        html_content = json_content.get("html", "")
        if not html_content:
            logger.warning("HTML контент отсутствует в JSON")
            return users_data

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(html_content, "lxml")

        # Находим все строки таблицы рейтинга
        table_rows = soup.find_all("a", class_="ranklist-table-row")

        logger.info(f"Найдено {len(table_rows)} строк в таблице рейтинга")

        for row in table_rows:
            try:
                # Извлекаем ссылку на профиль
                profile_link = row.get("href", "")
                if not profile_link:
                    logger.warning("Пропуск строки - отсутствует ссылка на профиль")
                    continue
                # Находим место в рейтинге
                rank_element = row.select_one(".ranklist-place-wrapper span")
                if not rank_element:
                    logger.warning(
                        f"Пропуск профиля {profile_link} - отсутствует элемент ранга"
                    )
                    continue
                rank = rank_element.text.strip()

                # Находим заработок
                earning_element = row.select_one(".ranklist-earning-wrapper span.price")
                if not earning_element:
                    logger.warning(
                        f"Пропуск профиля {profile_link} - отсутствует элемент заработка"
                    )
                    continue

                # Извлекаем как отформатированное значение, так и оригинальное
                earning_display = earning_element.text.strip()

                # Создаем объект с данными пользователя
                user_data = {
                    "current_datetime": current_datetime,
                    "country_code": country_code,
                    "rank": int(rank) if rank.isdigit() else rank,
                    "profile_link": profile_link,
                    "earning": earning_display,
                }

                users_data.append(user_data)

            except Exception as e:
                logger.error(f"Ошибка при обработке строки таблицы: {e}")
                continue

    except Exception as e:
        logger.error(f"Критическая ошибка при парсинге данных: {e}")

    return users_data


if __name__ == "__main__":
    try:
        logger.info("🚀 Запуск сбора данных TikLeap...")
        result = asyncio.run(response_methods())

        if result and len(result) > 0:
            logger.success(
                f"✅ Сбор данных завершен успешно. Собрано {len(result)} записей"
            )
            sys.exit(0)  # Код 0 = успех
        else:
            logger.warning("⚠️ Данные не собраны или результат пустой")
            sys.exit(2)  # Код 2 = пустой результат, нужна повторная авторизация

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"❌ Ошибка при выполнении сбора данных: {e}")

        # Проверяем тип ошибки для определения действий
        if any(
            keyword in error_msg
            for keyword in [
                "is_decode error",
                "decode",
                "json",
                "cookies",
                "unauthorized",
                "forbidden",
                "authentication",
                "session",
                "token",
            ]
        ):
            logger.error(
                "🔐 Ошибка связана с авторизацией/сессией - нужна повторная авторизация"
            )
            sys.exit(3)  # Код 3 = нужна повторная авторизация
        elif any(
            keyword in error_msg
            for keyword in ["timeout", "connection", "network", "unreachable"]
        ):
            logger.error("🌐 Сетевая ошибка - попробуем позже")
            sys.exit(4)  # Код 4 = сетевая ошибка, повтор через время
        else:
            logger.error("💥 Общая ошибка")
            sys.exit(1)  # Код 1 = общая ошибка
