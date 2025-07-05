# client/main_check.py
import random
import time

from config import logger


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


def find_company_by_number(all_cars, number):
    """
    Ищет компанию по номеру в списке all_cars

    Args:
        all_cars (list): Список словарей с данными о перевозчиках
        number (str): Номер для поиска

    Returns:
        dict or None: Словарь с данными компании или None если не найдено
    """
    for car in all_cars:
        if car.get("number_or_vin") == number:
            return {
                "company_name": car.get("company_name"),
                "edrpou_code": car.get("edrpou_code"),
            }
    return None


def enrich_transport_data(transport_data, all_cars, get_custom_func):
    """
    Обогащает данные транспорта информацией о компании

    Args:
        transport_data (list): Список словарей с данными о транспорте
        all_cars (list): Список словарей с данными о перевозчиках из БД
        get_custom_func (function): Функция для получения данных по номеру

    Returns:
        list: Обновленный список словарей с добавленными данными компании
    """
    enriched_data = []

    for transport in transport_data:
        # Создаем копию исходного словаря
        enriched_transport = transport.copy()

        plate_number = transport.get("plate_number")
        semi_trailer_number = transport.get("semi_trailer_number")

        company_info = None

        # Шаг 1: Проверяем plate_number в all_cars
        if plate_number:
            company_info = find_company_by_number(all_cars, plate_number)
            if company_info:
                logger.info(
                    f"Найдена компания для {plate_number}: {company_info['company_name']}"
                )

        # Шаг 2: Если не найдено, проверяем semi_trailer_number
        if not company_info and semi_trailer_number:
            company_info = find_company_by_number(all_cars, semi_trailer_number)
            if company_info:
                logger.info(
                    f"Найдена компания для semi_trailer_number {semi_trailer_number}: {company_info['company_name']}"
                )

        # Шаг 3: Если все еще не найдено, используем get_custom
        if not company_info and plate_number:
            try:
                custom_result = get_custom_func(plate_number)
                random_pause(1, 5)

                # ДОБАВИТЬ ПРОВЕРКУ что custom_result это словарь
                if (
                    custom_result
                    and isinstance(custom_result, dict)
                    and "company_name" in custom_result
                    and "edrpou_code" in custom_result
                ):
                    company_info = {  # <-- ЭТА СТРОКА БЫЛА ПРОПУЩЕНА
                        "company_name": custom_result.get("company_name"),
                        "edrpou_code": custom_result.get("edrpou_code"),
                    }
                    logger.info(
                        f"Получена компания для {plate_number}: {company_info['company_name']}"
                    )
            except Exception as e:
                logger.error(f"Ошибка при вызове get_custom для {plate_number}: {e}")

        # Обновляем словарь данными компании
        if company_info:
            enriched_transport.update(company_info)
        else:
            logger.error(
                f"Не удалось найти компанию для транспорта: {plate_number} / {semi_trailer_number}"
            )
            # Добавляем пустые поля если ничего не найдено
            enriched_transport.update({"company_name": None, "edrpou_code": None})

        enriched_data.append(enriched_transport)

    return enriched_data
