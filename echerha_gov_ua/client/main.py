import json
import random
import re
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from scrap import create_excel_from_customs_data

from config import Config, logger, paths

all_customs = paths.data / "all_customs.json"
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


@contextmanager
def timer(name="Код"):
    start_time = time.perf_counter()
    try:
        yield
    finally:
        end_time = time.perf_counter()
        logger.info(f"{name} выполнился за {end_time - start_time:.4f} секунд")


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


def get_all_customs() -> bool:
    """Получает список всех таможенных пунктов и сохраняет в файл"""
    try:
        url = "https://back.echerha.gov.ua/api/v4/workload/1"
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Проверка на HTTP ошибки

        data = response.json()
        with open(all_customs, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Сохранил {all_customs}")
        return True
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе списка таможен: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при получении списка таможен: {e}")
        return False


def get_custom(id_checkpoint: int) -> bool:
    """Получает детальную информацию о таможенном пункте"""
    try:
        url = f"https://back.echerha.gov.ua/api/v4/workload/1/checkpoints/{id_checkpoint}/details/1/30"
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()

        data = response.json()
        # Трансформируем данные перед сохранением
        keys_to_remove = ["links", "meta", "checkpoint", "title"]
        cleaned_data = remove_keys_from_dict(data, keys_to_remove)

        # Трансформируем данные перед сохранением
        transformed_data = transform_customs_data(cleaned_data)

        file_name = paths.json / f"custom_{id_checkpoint}_01.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(transformed_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Сохранил {file_name}")

        # Получаем количество страниц и загружаем остальные если есть
        total_pages = count_pages(data)
        if total_pages and total_pages > 1:
            get_custom_pages(total_pages, id_checkpoint)

        return True
    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе данных таможни {id_checkpoint}: {e}")
        return False
    except Exception as e:
        logger.error(
            f"Неожиданная ошибка при получении данных таможни {id_checkpoint}: {e}"
        )
        return False


def get_current_year() -> int:
    """
    Получает текущий год

    Returns:
        int: Текущий год
    """
    return datetime.now().year


def parse_ukrainian_datetime(datetime_str: str, year: int = None) -> Tuple[str, str]:
    """
    Парсит украинскую дату и время, разделяет на дату и время

    Args:
        datetime_str: Строка вида "27 червня 17:10"
        year: Год для формирования полной даты (по умолчанию текущий год)

    Returns:
        Tuple[str, str]: (дата в формате DD.MM.YYYY, время в формате HH:MM)
    """
    if not datetime_str or not isinstance(datetime_str, str):
        return "", ""

    # Если год не передан, используем текущий
    if year is None:
        year = get_current_year()

    # Словарь украинских месяцев
    ukrainian_months = {
        "січня": "01",
        "січень": "01",
        "лютого": "02",
        "лютий": "02",
        "березня": "03",
        "березень": "03",
        "квітня": "04",
        "квітень": "04",
        "травня": "05",
        "травень": "05",
        "червня": "06",
        "червень": "06",
        "липня": "07",
        "липень": "07",
        "серпня": "08",
        "серпень": "08",
        "вересня": "09",
        "вересень": "09",
        "жовтня": "10",
        "жовтень": "10",
        "листопада": "11",
        "листопад": "11",
        "грудня": "12",
        "грудень": "12",
    }

    try:
        # Паттерн для парсинга: число + месяц + время
        pattern = r"(\d{1,2})\s+(\w+)\s+(\d{1,2}:\d{2})"
        match = re.search(pattern, datetime_str.strip())

        if not match:
            # Если не удалось распарсить, возвращаем пустые строки
            return "", ""

        day = match.group(1).zfill(2)  # Добавляем ведущий ноль если нужно
        month_name = match.group(2).lower()
        time_part = match.group(3)

        # Находим номер месяца
        month_num = ukrainian_months.get(month_name)
        if not month_num:
            # Если месяц не найден, возвращаем пустые строки
            return "", ""

        # Формируем дату в формате DD.MM.YYYY
        date_formatted = f"{day}.{month_num}.{year}"

        # Время оставляем как есть, но проверяем формат
        time_formatted = format_time(time_part)

        return date_formatted, time_formatted

    except Exception as e:
        # В случае любой ошибки возвращаем пустые строки
        return "", ""


def format_time(time_str: str) -> str:
    """
    Форматирует время, добавляя ведущие нули если нужно

    Args:
        time_str: Время в формате "H:MM" или "HH:MM"

    Returns:
        Время в формате "HH:MM"
    """
    try:
        if ":" not in time_str:
            return ""

        parts = time_str.split(":")
        if len(parts) != 2:
            return ""

        hours = parts[0].zfill(2)
        minutes = parts[1].zfill(2)

        # Проверяем валидность времени
        if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
            return ""

        return f"{hours}:{minutes}"

    except (ValueError, IndexError):
        return ""


def transform_customs_data(data: dict) -> dict:
    """
    Трансформирует данные о транспорте в нужный формат

    Args:
        data: Исходные данные из API

    Returns:
        dict: Трансформированные данные с измененной структурой
    """
    if not isinstance(data, dict) or "data" not in data:
        logger.warning("Некорректная структура данных для трансформации")
        return data

    original_items = data.get("data", [])
    transformed_items = []

    for item in original_items:
        try:

            # Тягач
            plate_number = item.get("plate_number", "")
            if plate_number is not None:
                plate_number = plate_number.replace(" ", "")
            # Причіп
            semi_trailer_number = item.get("semi_trailer_number", "")
            if semi_trailer_number is not None:
                semi_trailer_number = semi_trailer_number.replace(" ", "")

            estimated_time = item.get("estimated_time", "")
            date, time_date = parse_ukrainian_datetime(estimated_time)
            # Формируем новую структуру
            transformed_item = {
                "plate_number": plate_number,
                "semi_trailer_number": semi_trailer_number,
                "date": date,
                "time": time_date,
                "confirmed_at": item.get("confirmed_at", ""),
                "position_number": item.get("position_number", ""),
            }

            transformed_items.append(transformed_item)

        except Exception as e:
            logger.error(f"Ошибка при трансформации элемента {item}: {e}")
            continue

    # Возвращаем данные в том же формате, но с измененной структурой data
    result = data.copy()
    result["data"] = transformed_items

    # logger.info(
    #     f"Трансформировано {len(transformed_items)} из {len(original_items)} записей"
    # )
    return result


def remove_keys_from_dict(data, keys_to_remove):
    """
    Удаляет указанные ключи из словаря

    Args:
        data: Словарь или структура данных
        keys_to_remove: Список ключей для удаления

    Returns:
        Очищенные данные
    """
    if isinstance(data, dict):
        # Создаем новый словарь без нежелательных ключей
        return {
            k: remove_keys_from_dict(v, keys_to_remove)
            for k, v in data.items()
            if k not in keys_to_remove
        }
    elif isinstance(data, list):
        # Рекурсивно обрабатываем элементы списка
        return [remove_keys_from_dict(item, keys_to_remove) for item in data]
    else:
        # Возвращаем значение как есть
        return data


def get_custom_pages(total_pages: int, id_checkpoint: int) -> None:
    """Получает данные со всех страниц для конкретной таможни"""
    for page in range(2, total_pages + 1):  # Начинаем с 2-й страницы
        try:
            params = {"page": page}
            url = f"https://back.echerha.gov.ua/api/v4/workload/1/checkpoints/{id_checkpoint}/details/1/30"
            response = requests.get(
                url, params=params, headers=headers, timeout=timeout
            )
            response.raise_for_status()

            data = response.json()

            keys_to_remove = ["links", "meta", "checkpoint", "title"]
            cleaned_data = remove_keys_from_dict(data, keys_to_remove)

            # Трансформируем данные перед сохранением
            transformed_data = transform_customs_data(cleaned_data)

            # Формат номера страницы с ведущими нулями
            file_name = paths.json / f"custom_{id_checkpoint}_{page:02d}.json"
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(transformed_data, f, ensure_ascii=False, indent=4)

            logger.info(f"Сохранил страницу {page}/{total_pages}: {file_name}")
            random_pause(5, 10)

        except requests.RequestException as e:
            logger.error(
                f"Ошибка при запросе страницы {page} для таможни {id_checkpoint}: {e}"
            )
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке страницы {page}: {e}")


def load_json_file(file_path) -> Optional[Dict[str, Any]]:
    """Загрузка данных из JSON файла"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при парсинге JSON из {file_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных из {file_path}: {e}")
        return None


def count_pages(data: Dict[str, Any]) -> Optional[int]:
    """Подсчитывает общее количество страниц на основе метаданных"""
    try:
        total = data.get("meta", {}).get("total", 0)
        per_page = data.get("meta", {}).get("per_page", 20)  # По умолчанию 30

        if total > per_page:
            pages = (total + per_page - 1) // per_page  # Округление вверх
            logger.info(f"Найдено {total} записей, будет загружено {pages} страниц")
            return pages
        else:
            logger.info(
                f"Найдено {total} записей, загрузка дополнительных страниц не требуется"
            )
            return 1
    except Exception as e:
        logger.error(f"Ошибка при подсчете страниц: {e}")
        return None


def process_all_customs() -> None:
    """Основная функция для обработки всех таможенных пунктов"""
    # Сначала получаем список всех таможен
    if not get_all_customs():
        logger.error("Не удалось получить список таможен")
        return

    # Загружаем список таможен
    customs_data = load_json_file(all_customs)
    if not customs_data or "data" not in customs_data:
        logger.error("Не удалось загрузить данные о таможнях")
        return

    customs = customs_data["data"]
    logger.info(f"Найдено {len(customs)} таможенных пунктов")

    # Обрабатываем каждую таможню
    for i, custom in enumerate(customs, 1):
        id_checkpoint = custom.get("id")
        if not id_checkpoint:
            logger.warning(f"Пропускаем таможню без ID: {custom}")
            continue

        custom_name = custom.get("name", f"Таможня {id_checkpoint}")
        logger.info(
            f"Обрабатываем {i}/{len(customs)}: {custom_name} (ID: {id_checkpoint})"
        )

        success = get_custom(id_checkpoint)
        if success:
            logger.info(f"Успешно обработана таможня {id_checkpoint}")
        else:
            logger.error(f"Ошибка при обработке таможни {id_checkpoint}")

        # Пауза между обработкой разных таможен
        if i < len(customs):  # Не делаем паузу после последней
            time.sleep(2)


if __name__ == "__main__":
    with timer("Мой блок кода"):
        # Полный запуск
        process_all_customs()
        create_excel_from_customs_data()

    # Вариант 2: Обработать конкретную таможню (раскомментируйте при необходимости)
