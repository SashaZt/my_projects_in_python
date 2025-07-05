import asyncio
import datetime
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger
from rnet import Client, Impersonate

# Настройка директорий и логирования
# Настройка путей
current_directory = Path.cwd()

json_directory = current_directory / "json"
log_directory = current_directory / "log"

json_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"


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
headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.stubhub.com",
    "priority": "u=1, i",
    "referer": "https://www.stubhub.com",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}


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
    logger.debug(f"🎲 Случайная пауза: {pause_duration:.2f} секунд")

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


def get_request_data(page=1):
    """Возвращает данные для запроса"""
    return {
        "ShowAllTickets": True,
        "HideDuplicateTicketsV2": False,
        "Quantity": 4,
        "IsInitialQuantityChange": False,
        "PageVisitId": "1D000C0A-9A16-4FD3-9CDB-612FAB2C79AE",
        "PageSize": 20,
        "CurrentPage": page,
        "SortBy": "CUSTOM_RANKING",
        "SortDirection": 1,
        "Sections": "",
        "Rows": "",
        "Seats": "",
        "SeatTypes": "",
        "TicketClasses": "",
        "ListingNotes": "",
        "PriceRange": "0,100",
        "InstantDelivery": False,
        "EstimatedFees": True,
        "BetterValueTickets": True,
        "PriceOption": "",
        "HasFlexiblePricing": False,
        "ExcludeSoldListings": False,
        "RemoveObstructedView": False,
        "NewListingsOnly": False,
        "PriceDropListingsOnly": False,
        "ConciergeTickets": False,
        "Favorites": False,
        "Method": "IndexSh",
    }


async def extract_items_data(json_data):
    """
    Извлекает id и price из JSON данных

    Args:
        json_data (dict): JSON данные с ключом "items"

    Returns:
        list: Список словарей с id и price
    """
    try:
        items = json_data.get("items", [])

        if not items:
            logger.warning("⚠️ Нет элементов в 'items' или ключ отсутствует")
            return []

        extracted_data = []

        for item in items:
            item_data = {
                "id": item.get("id"),
                "price": item.get("price").replace("UAH", ""),
            }

            # Проверяем, что оба поля присутствуют
            if item_data["id"] is not None and item_data["price"] is not None:
                extracted_data.append(item_data)
            else:
                logger.warning(
                    f"⚠️ Пропущен элемент с неполными данными: id={item_data['id']}, price={item_data['price']}"
                )

        logger.success(
            f"✅ Извлечено {len(extracted_data)} элементов из {len(items)} общих"
        )
        return extracted_data

    except Exception as e:
        logger.error(f"❌ Ошибка при извлечении данных: {e}")
        return []


async def fetch_page_data(client, url, page):
    """Получает данные одной страницы"""
    try:
        json_data = get_request_data(page)
        response = await client.post(url, headers=headers, json=json_data)

        if response.ok:
            logger.info(f"📄 Страница {page}: Status Code {response.status_code}")
            json_content = await response.json()
            return json_content
        else:
            logger.error(f"❌ Ошибка запроса страницы {page}: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при получении страницы {page}: {e}")
        return None


async def total_page(json_data):
    """Вычисляет общее количество страниц"""
    totalCount = int(json_data.get("totalCount", 0))
    pageSize = int(json_data.get("pageSize", 20))
    count_pages = (totalCount + pageSize - 1) // pageSize
    return count_pages


async def collect_all_data(url, file_name):
    """
    Собирает все данные со всех страниц и сохраняет в один файл

    Args:
        url (str): URL для запросов
        file_name (str): Базовое имя файла

    Returns:
        bool: True если успешно, False если ошибка
    """
    client = Client(impersonate=Impersonate.Chrome137)
    all_items = []

    try:
        # Получаем первую страницу
        logger.info("🚀 Начинаем сбор данных с первой страницы...")
        json_content = await fetch_page_data(client, url, 1)

        if not json_content:
            logger.error("❌ Не удалось получить данные с первой страницы")
            return False

        # Извлекаем данные с первой страницы
        page_items = await extract_items_data(json_content)
        all_items.extend(page_items)

        # Определяем общее количество страниц
        total_pages = await total_page(json_content)
        logger.info(f"📊 Всего страниц: {total_pages}")

        # Обрабатываем остальные страницы
        if total_pages > 1:
            for page in range(2, total_pages + 1):
                await async_random_pause(1, 5)

                logger.info(f"📄 Обрабатываем страницу {page}/{total_pages}")
                json_content = await fetch_page_data(client, url, page)

                if json_content:
                    page_items = await extract_items_data(json_content)
                    all_items.extend(page_items)
                    logger.info(f"📈 Собрано элементов: {len(all_items)}")
                else:
                    logger.warning(f"⚠️ Пропускаем страницу {page} из-за ошибки")

        # Сохраняем все данные в один файл
        output_file = json_directory / f"{file_name}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_items, f, ensure_ascii=False, indent=4)

        logger.success(
            f"🎉 Успешно сохранено {len(all_items)} элементов в файл: {output_file}"
        )
        return True

    except Exception as e:
        logger.error(f"❌ Ошибка при сборе всех данных: {e}")
        return False


# Обновленная главная функция
async def response_methods(url, file_name):
    """
    Основная функция - собирает данные со всех страниц в один файл

    Args:
        url (str): URL для запросов
        file_name (str): Базовое имя файла
    """
    success = await collect_all_data(url, file_name)

    if success:
        logger.success("✅ Сбор данных завершен успешно!")
    else:
        logger.error("❌ Сбор данных завершен с ошибками")


if __name__ == "__main__":
    try:
        urls = [
            "https://www.stubhub.com/soccer-world-cup-east-rutherford-tickets-7-19-2026/event/153020449/",
            "https://www.stubhub.com/super-bowl-santa-clara-tickets-2-8-2026/event/157245215/",
        ]
        for url in urls:
            name_event = url.split("/")[-4].replace("-", "_")
            event = url.split("/")[-2]
            file_name = f"{name_event}_{event}"
            asyncio.run(response_methods(url, file_name))

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"❌ Ошибка при выполнении сбора данных: {e}")
