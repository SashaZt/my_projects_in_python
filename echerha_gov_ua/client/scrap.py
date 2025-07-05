import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from main_card import get_all_carriers, get_custom
from main_check import enrich_transport_data

from config import Config, logger, paths

config = Config.load()

all_customs = paths.data / "all_customs.json"


def sanitize_sheet_name(name: str) -> str:
    """
    Очищает название листа Excel от недопустимых символов

    Args:
        name: Исходное название

    Returns:
        Очищенное название листа
    """
    # Недопустимые символы для названий листов Excel: / \ ? * [ ] :
    # Также ограничение в 31 символ

    # Заменяем недопустимые символы на подчеркивание
    sanitized = re.sub(r"[( /\\?*\[\]:≥)]", "_", name)

    # Убираем множественные подчеркивания
    sanitized = re.sub(r"_+", "_", sanitized)

    # Убираем подчеркивания в начале и конце
    sanitized = sanitized.strip("_")

    # Ограничиваем длину до 31 символа (лимит Excel)
    if len(sanitized) > 31:
        sanitized = sanitized[:31].rstrip("_")

    return sanitized


def get_customs_files_by_id(customs_id: int) -> List[Path]:
    """
    Находит все JSON файлы для конкретной таможни

    Args:
        customs_id: ID таможни

    Returns:
        Список путей к файлам
    """
    if not paths.json.exists():
        logger.warning(f"Директория {paths.json} не найдена")
        return []

    # Ищем файлы по паттерну custom_{id}_*.json
    pattern = f"custom_{customs_id}_*.json"
    files = list(paths.json.glob(pattern))

    # Сортируем файлы по номеру страницы
    files.sort(key=lambda x: x.name)

    logger.info(f"Найдено {len(files)} файлов для таможни {customs_id}")
    return files


def collect_transport_data(customs_id: int) -> List[Dict]:
    """
    Собирает все данные о транспорте для конкретной таможни

    Args:
        customs_id: ID таможни

    Returns:
        Список данных о транспорте
    """
    files = get_customs_files_by_id(customs_id)
    all_transport_data = []

    for file_path in files:
        try:
            data = load_json_file(file_path)
            if data and "data" in data:
                transport_items = data["data"]
                all_transport_data.extend(transport_items)

        except Exception as e:
            logger.error(f"Ошибка при чтении файла {file_path}: {e}")

    return all_transport_data


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


def create_empty_excel_sheet(
    customs_id: int, customs_title: str, output_file: Path = None
) -> bool:
    """
    Создает пустой Excel файл только с заголовками для таможни без данных

    Args:
        customs_id: ID таможни
        customs_title: Название таможни
        output_file: Путь к выходному файлу

    Returns:
        True если успешно, False если ошибка
    """
    try:
        # Путь к выходному файлу
        if output_file is None:
            safe_name = sanitize_sheet_name(customs_title)
            output_file = paths.data / f"customs_{customs_id}_{safe_name}_empty.xlsx"

        # Маппинг колонок (только заголовки)
        column_mapping = {
            "plate_number": "Тягач",
            "semi_trailer_number": "Причіп",
            "date": "Орієнтовний дата в'їзду",
            "time": "Орієнтовний час в'їзду",
            "confirmed_at": "Реєстрація в черзі",
            "position_number": "Номер",
        }

        # Создаем пустой DataFrame только с колонками
        df = pd.DataFrame(columns=list(column_mapping.values()))

        # Очищаем название листа
        sheet_name = sanitize_sheet_name(customs_title)

        # Записываем в Excel
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Автоподбор ширины колонок для заголовков
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                # Для пустого листа используем длину заголовка
                for cell in column:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                # Минимальная ширина для заголовков
                adjusted_width = max(max_length + 2, 15)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        logger.info(f"Создан пустой Excel файл: {output_file}")
        logger.info(f"Лист '{sheet_name}' содержит только заголовки")
        return True

    except Exception as e:
        logger.error(
            f"Ошибка при создании пустого Excel файла для таможни {customs_id}: {e}"
        )
        return False


def create_excel_from_customs_data(output_file: Path = None) -> bool:
    """
    Создает Excel файл со всеми данными таможен

    Args:
        output_file: Путь к выходному Excel файлу

    Returns:
        True если успешно, False если ошибка
    """
    try:
        all_cars = get_all_carriers()
        # Путь к выходному файлу по умолчанию
        if output_file is None:
            output_file = paths.data / "customs_transport_data.xlsx"

        # Загружаем список всех таможен
        customs_data = load_json_file(all_customs)
        if not customs_data or "data" not in customs_data:
            logger.error("Не удалось загрузить данные о таможнях")
            return False

        customs_list = customs_data["data"]

        # Маппинг колонок
        column_mapping = {
            "plate_number": "Тягач",
            "semi_trailer_number": "Причіп",
            "date": "Орієнтовний дата в'їзду",
            "time": "Орієнтовний час в'їзду",
            "confirmed_at": "Реєстрація в черзі",
            "position_number": "Номер",
        }

        # Создаем ExcelWriter
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            processed_customs = 0

            for custom in customs_list:
                customs_id = custom.get("id")
                customs_title = custom.get("title", f"Таможня_{customs_id}")

                if not customs_id:
                    continue

                logger.info(f"Обрабатываем таможню: {customs_title} (ID: {customs_id})")

                # Собираем данные о транспорте
                transport_data = collect_transport_data(customs_id)
                result = enrich_transport_data(transport_data, all_cars, get_custom)
                if not result:
                    logger.warning(
                        f"Нет данных для таможни {customs_id}, создаем пустой лист с заголовками"
                    )
                    # Создаем пустой DataFrame только с заголовками
                    df = pd.DataFrame(columns=list(column_mapping.values()))

                # Создаем DataFrame
                df = pd.DataFrame(result)

                # Переименовываем колонки согласно маппингу
                df = df.rename(columns=column_mapping)

                # Очищаем название листа
                sheet_name = sanitize_sheet_name(customs_title)

                # Записываем в Excel
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                # Автоподбор ширины колонок
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter

                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass

                    adjusted_width = min(max_length + 2, 50)  # Максимум 50 символов
                    worksheet.column_dimensions[column_letter].width = adjusted_width

                processed_customs += 1
                logger.info(f"Записано {len(result)} записей для '{sheet_name}'")

        logger.info(f"Excel файл создан: {output_file}")
        logger.info(f"Обработано {processed_customs} таможен")
        return True

    except Exception as e:
        logger.error(f"Ошибка при создании Excel файла: {e}")
        return False


def create_excel_for_single_customs(customs_id: int, output_file: Path = None) -> bool:
    """
    Создает Excel файл для одной конкретной таможни

    Args:
        customs_id: ID таможни
        output_file: Путь к выходному файлу

    Returns:
        True если успешно, False если ошибка
    """
    try:
        all_cars = get_all_carriers()
        # Загружаем информацию о таможне
        customs_data = load_json_file(all_customs)
        if not customs_data or "data" not in customs_data:
            logger.error("Не удалось загрузить данные о таможнях")
            return False

        # Ищем таможню по ID
        customs_info = None
        for custom in customs_data["data"]:
            if custom.get("id") == customs_id:
                customs_info = custom
                break

        if not customs_info:
            logger.error(f"Таможня с ID {customs_id} не найдена")
            return False

        customs_title = customs_info.get("title", f"Таможня_{customs_id}")

        # Путь к выходному файлу
        if output_file is None:
            safe_name = sanitize_sheet_name(customs_title)
            output_file = paths.data / f"customs_{customs_id}_{safe_name}.xlsx"

        # Собираем данные о транспорте
        transport_data = collect_transport_data(customs_id)
        result = enrich_transport_data(transport_data, all_cars, get_custom)

        if not result:
            logger.warning(f"Нет данных для таможни {customs_id}")
            return False

        # Маппинг колонок
        column_mapping = {
            "plate_number": "Тягач",
            "semi_trailer_number": "Причіп",
            "date": "Орієнтовний дата в'їзду",
            "time": "Орієнтовний час в'їзду",
            "confirmed_at": "Реєстрація в черзі",
            "position_number": "Номер",
        }

        # Создаем DataFrame
        df = pd.DataFrame(result)
        df = df.rename(columns=column_mapping)

        # Очищаем название листа
        sheet_name = sanitize_sheet_name(customs_title)

        # Записываем в Excel
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Автоподбор ширины колонок
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        logger.info(f"Excel файл создан: {output_file}")
        logger.info(f"Записано {len(result)} записей для '{customs_title}'")
        return True

    except Exception as e:
        logger.error(f"Ошибка при создании Excel файла для таможни {customs_id}: {e}")
        return False


# Функция для массового создания Excel файлов (по одному на таможню)
def create_excel_files_for_all_customs() -> None:
    """Создает отдельный Excel файл для каждой таможни"""
    customs_data = load_json_file(all_customs)
    if not customs_data or "data" not in customs_data:
        logger.error("Не удалось загрузить данные о таможнях")
        return

    customs_list = customs_data["data"]
    success_count = 0

    for custom in customs_list:
        customs_id = custom.get("id")
        if customs_id and create_excel_for_single_customs(customs_id):
            success_count += 1

    logger.info(f"Создано {success_count} Excel файлов из {len(customs_list)} таможен")
