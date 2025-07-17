import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests
from config.logger import logger
from config import Config
from get_domain import (
    create_sajt_text_to_value_mapping,
    extract_domain_from_utm_page,
    find_sajt_value_by_domain,
)
config = Config.load()
SALESDRIVE_API = config.client.salesdrive_api
CRM_FORM_ID = config.client.crm_form_id
TIMEOUT = config.client.timeout
INTERVAL_MINUTES = config.client.parser_interval_minutes

current_directory = Path.cwd()
file_sajt = current_directory / "sajt.json"
file_orders = current_directory / "orders.json"

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

    return pause_duration


def random_pause(min_seconds, max_seconds):
    """
    Cинхронная функция: выполняет случайную паузу в заданном диапазоне

    Args:
        min_seconds (int/float): Минимальное количество секунд
        max_seconds (int/float): Максимальное количество секунд

    Examples:
        >>> await async_random_pause(1, 3)  # Асинхронная пауза от 1 до 3 секунд
        >>> await async_random_pause(2.5, 5.0)  # Асинхронная пауза от 2.5 до 5 секунд
    """
    pause_duration = get_random_pause(min_seconds, max_seconds)
    time.sleep(pause_duration)


def extract_and_save_sajt_options():
    """
    Функция для извлечения опций sajt из API и сохранения в файл
    """
    try:
        url = "https://zubr.salesdrive.me/api/order/list/"
        headers = {"Form-Api-Key": SALESDRIVE_API}
        params = {
            "page": 1,
            "limit": 1,  # Нужен только один результат для получения мета-данных
        }

        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)

        if response.status_code == 200:
            data = response.json()

            # Извлекаем опции sajt из мета-данных
            sajt_options = (
                data.get("meta", {})
                .get("fields", {})
                .get("sajt", {})
                .get("options", [])
            )

            # Создаем массив словарей с value и text
            sajt_mapping = []
            for option in sajt_options:
                sajt_mapping.append(
                    {"value": option.get("value"), "text": option.get("text")}
                )

            # Сохраняем в файл
            with open(file_sajt, "w", encoding="utf-8") as f:
                json.dump(sajt_mapping, f, ensure_ascii=False, indent=4)

            logger.info(f"Сохранено {len(sajt_mapping)} опций sajt в файл sajt.json")
            return sajt_mapping

        else:
            logger.error(f"Ошибка при запросе: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при извлечении опций sajt: {e}")
        return None


def load_sajt_options():
    """
    Загружает опции sajt из файла
    """
    try:
        if file_sajt.exists():
            with open(file_sajt, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            logger.error(
                "Файл sajt.json не найден. Сначала выполните extract_and_save_sajt_options()"
            )
            return None
    except Exception as e:
        logger.error(f"Ошибка при загрузке sajt.json: {e}")
        return None


def get_salesdrive_orders(date_from=None, date_to=None):
    try:
        # Если даты не указаны, используем последние 24 часа
        if not date_from or not date_to:
            date_to = datetime.now()
            date_from = date_to - timedelta(days=1)
            date_to = date_to.replace(hour=23, minute=59, second=59)
            date_from = date_from.replace(hour=0, minute=0, second=0)

        # Форматируем даты
        date_from_str = date_from.strftime("%Y-%m-%d %H:%M:%S")
        date_to_str = date_to.strftime("%Y-%m-%d %H:%M:%S")

        url = "https://zubr.salesdrive.me/api/order/list/"
        headers = {"Form-Api-Key": SALESDRIVE_API}
        params = {
            "filter[orderTime][from]": date_from_str,
            "filter[orderTime][to]": date_to_str,
            "page": 1,
            "limit": 100,
        }

        response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)

        if response.status_code == 200:
            data = response.json()

            # Сохраняем в файл
            with open(file_orders, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            # Загружаем маппинг для sajt (text -> value)
            sajt_mapping = create_sajt_text_to_value_mapping()
            matched_orders = []

            # Обрабатываем каждую заявку
            for order in data.get("data", []):
                sajt_value = order.get("sajt")
                utm_page = order.get("utmPage")
                id_order = order.get("id")

                # Проверяем только заявки где sajt = null
                if sajt_value is None and utm_page:
                    # Извлекаем домен из utmPage
                    domain = extract_domain_from_utm_page(utm_page)

                    if domain:
                        # Ищем соответствующий value в sajt.json
                        found_sajt_value = find_sajt_value_by_domain(
                            domain, sajt_mapping
                        )

                        if found_sajt_value:
                            # Добавляем в результат
                            result = {
                                "id_order": id_order,
                                "utm_page": utm_page,
                                "extracted_domain": domain,
                                "found_sajt_value": found_sajt_value,
                            }
                            matched_orders.append(result)

                            logger.info(
                                f"Заявка {id_order}: domain '{domain}' -> sajt value {domain}"
                            )
                        else:
                            logger.warning(
                                f"Заявка {id_order}: домен '{domain}' не найден в sajt.json"
                            )

            # Сохраняем результат в файл
            with open("matched_orders.json", "w", encoding="utf-8") as f:
                json.dump(matched_orders, f, ensure_ascii=False, indent=4)

            logger.info(
                f"Найдено {len(matched_orders)} заявок с sajt=null и найденным доменом"
            )
            return matched_orders
        else:
            logger.error(f"Ошибка при получении заявок: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Ошибка при получении заявок: {e}")
        return None


def update_order_sajt(orders_data):
    """
    Обновляет sajt для списка заявок

    Args:
        orders_data (list): Список словарей с данными заявок

    Returns:
        list: Список результатов обновления для каждой заявки
    """
    results = []

    try:
        url = "https://zubr.salesdrive.me/api/order/update/"
        headers = {
            "Form-Api-Key": SALESDRIVE_API,
            "Content-Type": "application/json",
        }

        for order_data in orders_data:
            try:
                order_id = order_data.get("id_order")
                sajt_value = order_data.get("found_sajt_value")
                extracted_domain = order_data.get("extracted_domain")

                payload = {
                    "form": CRM_FORM_ID,
                    "id": order_id,
                    "data": {
                        "sajt": extracted_domain,
                    },
                }

                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=TIMEOUT,
                )

                if response.status_code == 200:
                    logger.info(f"Обновлена заявка {order_id}: sajt = {sajt_value}")
                    results.append(
                        {
                            "id": order_id,
                            "status": "success",
                            "sajt_value": extracted_domain,
                        }
                    )
                    random_pause(1, 5)
                else:
                    logger.error(
                        f"Ошибка при обновлении заявки {order_id}: {response.status_code}"
                    )
                    results.append(
                        {
                            "id": order_id,
                            "status": "error",
                            "error": f"HTTP {response.status_code}",
                        }
                    )

            except requests.exceptions.Timeout:
                logger.error(
                    f"Timeout при запросе к API для заявки {order_data['id_order']}"
                )
                results.append(
                    {
                        "id": order_data["id_order"],
                        "status": "error",
                        "error": "Timeout error",
                    }
                )
            except Exception as e:
                logger.error(
                    f"Ошибка при обновлении заявки {order_data['id_order']}: {e}"
                )
                results.append(
                    {
                        "id": order_data["id_order"],
                        "status": "error",
                        "error": str(e),
                    }
                )

    except Exception as e:
        logger.error(f"Критическая ошибка при обновлении заявок: {e}")
        raise

    return results
def main():
    matched_orders = get_salesdrive_orders()
    update_order_sajt(matched_orders)

if __name__ == "__main__":
    while True:
        main()
        logger.info("Пауза на 1 час!!!")
        time.sleep(60 * INTERVAL_MINUTES )

