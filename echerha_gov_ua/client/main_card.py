import random
import sqlite3
import time

import requests
from bs4 import BeautifulSoup

from config import Config, logger, paths

all_customs = paths.data / "all_customs.json"
db_path = paths.db / "carriers.db"
config = Config.load()
timeout = config.client.timeout
headers = {
    "accept": "application/json",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://echerha.gov.ua",
    "priority": "u=1, i",
    "referer": "https://echerha.gov.ua/",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "x-client-locale": "uk",
    "x-user-agent": "UABorder/3.4.3 Web/1.1.0 User/guest",
}


def create_database():
    """
    Создает базу данных и таблицу для хранения данных о перевозчиках
    """
    if not db_path.exists():
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS carriers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number_or_vin TEXT,
                company_name TEXT,
                manager TEXT,
                email TEXT,
                edrpou_code TEXT,
                license_status TEXT,
                license_issued TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()


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
    # logger.debug(
    #     f"🎲 Случайная пауза: {pause_duration:.2f} секунд ({min_seconds}-{max_seconds})"
    # )

    return pause_duration


def random_pause(min_seconds, max_seconds):
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
    # logger.info(f"😴 Асинхронная пауза {pause_duration:.2f} секунд...")
    time.sleep(pause_duration)


def get_custom(v: str):
    """Получает детальную информацию о таможенном пункте"""
    try:
        url = "https://shlyah.dsbt.gov.ua/xtr"
        params = {
            "v": v,
            "by": "num",
        }

        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.text
        # Трансформируем данные перед сохранением
        result = scrap_html(data)

        # Сохраняем в БД
        save_to_database(result)

        # ВОЗВРАЩАЕМ СЛОВАРЬ, а не bool
        return result

    except requests.RequestException as e:
        # logger.error(e)
        return {}  # Возвращаем пустой словарь вместо False


def scrap_html(content):
    """
    Парсит HTML контент и возвращает словарь с данными о перевозчике
    """
    soup = BeautifulSoup(content, "lxml")

    # Найти таблицу с данными
    table = soup.find("table")
    if not table:
        return {}

    # Извлечь все строки таблицы
    rows = table.find_all("tr")

    data = {}

    for row in rows:
        cells = row.find_all("td")
        if len(cells) == 2:
            # Очистить ключ от лишних пробелов и символов
            key = cells[0].get_text(strip=True).replace("\xa0", " ")
            value = cells[1].get_text(strip=True)

            # Нормализовать ключи для удобства работы (используем украинские варианты)
            if "№ або VIN" in key:
                data["number_or_vin"] = value
            elif "Назва перевізника" in key:
                data["company_name"] = value
            elif "Керівник" in key:
                data["manager"] = value
            elif "e-mail" in key:
                data["email"] = value
            elif "Код ЄДРПОУ" in key:
                data["edrpou_code"] = value
            elif "Статус ліцензії" in key:
                data["license_status"] = value
            elif "Ліцензія видана" in key:
                data["license_issued"] = value

    return data


def save_to_database(data_dict):
    """
    Сохраняет словарь с данными в базу данных SQLite

    Args:
        data_dict (dict): Словарь с данными о перевозчике

    Returns:
        bool: True если запись успешна, False в случае ошибки
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Подготовить данные для вставки
        insert_data = (
            data_dict.get("number_or_vin", ""),
            data_dict.get("company_name", ""),
            data_dict.get("manager", ""),
            data_dict.get("email", ""),
            data_dict.get("edrpou_code", ""),
            data_dict.get("license_status", ""),
            data_dict.get("license_issued", ""),
        )

        # Выполнить вставку
        cursor.execute(
            """
            INSERT INTO carriers 
            (number_or_vin, company_name, manager, email, edrpou_code, license_status, license_issued)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            insert_data,
        )

        conn.commit()
        conn.close()

        # logger.info(
        #     f"Данные успешно сохранены: {data_dict.get('company_name', 'Неизвестная компания')}"
        # )
        return True

    except sqlite3.Error as e:
        logger.error(f"Ошибка при работе с базой данных: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return False


def get_all_carriers():
    """
    Получает все записи из базы данных

    Returns:
        list: Список словарей с данными о перевозчиках
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT number_or_vin, company_name, edrpou_code FROM carriers ORDER BY created_at DESC;"
        )
        results = cursor.fetchall()

        # Преобразуем кортежи в словари
        carriers_list = []
        for row in results:
            carrier_dict = {
                "number_or_vin": row[0],
                "company_name": row[1],
                "edrpou_code": row[2],
            }
            carriers_list.append(carrier_dict)

        conn.close()
        return carriers_list

    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении данных: {e}")
        return []
