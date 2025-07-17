import json
from pathlib import Path

import pandas as pd
from config.logger import logger


def load_json_file(file_path):
    """
    Читает JSON файл и возвращает данные
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info(f"Успешно загружен файл {file_path}: {len(data)} записей")
        return data
    except FileNotFoundError:
        logger.error(f"Файл не найден: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка при парсинге JSON файла {file_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        return []


def merge_json_data(file1_path, file2_path, key_field="ИНН организации"):
    """
    Объединяет два JSON файла по указанному ключу
    """
    # Загружаем данные
    data1 = load_json_file(file1_path)
    data2 = load_json_file(file2_path)

    if not data1 and not data2:
        logger.error("Оба файла пусты или не удалось их загрузить")
        return []

    # Создаём словарь для объединения данных
    merged_data = {}

    # Счетчики для отладки
    count_file1_with_inn = 0
    count_file1_without_inn = 0
    count_file2_with_inn = 0
    count_file2_without_inn = 0

    # Обрабатываем первый файл
    for item in data1:
        inn = item.get(key_field)
        if inn and inn.strip():  # Проверяем, что ИНН не пустой
            merged_data[inn] = item.copy()
            count_file1_with_inn += 1
        else:
            count_file1_without_inn += 1
            logger.warning(f"Запись без ИНН в файле {file1_path}: {item}")

    # Обрабатываем второй файл и объединяем
    for item in data2:
        inn = item.get(key_field)
        if inn and inn.strip():  # Проверяем, что ИНН не пустой
            if inn in merged_data:
                # Объединяем словари, данные из второго файла имеют приоритет при конфликтах
                merged_data[inn] = {**merged_data[inn], **item}
                logger.info(f"Объединены данные для ИНН: {inn}")
            else:
                merged_data[inn] = item.copy()
            count_file2_with_inn += 1
        else:
            count_file2_without_inn += 1
            logger.warning(f"Запись без ИНН в файле {file2_path}: {item}")

    # Логируем статистику
    logger.info(
        f"Файл {file1_path}: {count_file1_with_inn} записей с ИНН, {count_file1_without_inn} без ИНН"
    )
    logger.info(
        f"Файл {file2_path}: {count_file2_with_inn} записей с ИНН, {count_file2_without_inn} без ИНН"
    )

    # Преобразуем в список
    result = list(merged_data.values())
    logger.info(f"Объединено {len(result)} записей")
    return result


def save_to_excel(data, output_file="merged_organizations.xlsx"):
    """
    Сохраняет объединённые данные в Excel файл
    """
    if not data:
        logger.error("Нет данных для сохранения в Excel")
        return False

    try:
        # Создаём DataFrame напрямую из данных
        df = pd.DataFrame(data)

        # Сортируем по ИНН для удобства
        if "ИНН организации" in df.columns:
            df = df.sort_values("ИНН организации")

        # Сохраняем в Excel
        df.to_excel(output_file, index=False, engine="openpyxl")
        logger.info(f"✓ Сохранено {len(data)} записей в файл {output_file}")

        # Выводим информацию о колонках
        logger.info(f"Колонки в файле: {list(df.columns)}")

        return True
    except Exception as e:
        logger.error(f"✗ Ошибка при сохранении в Excel: {e}")
        return False


def analyze_data_structure(data, filename):
    """
    Анализирует структуру данных для отладки
    """
    logger.info(f"Анализ структуры данных из {filename}:")
    if not data:
        logger.info("Данные пусты")
        return

    logger.info(f"Количество записей: {len(data)}")

    # Анализируем первую запись
    if data:
        first_record = data[0]
        logger.info(f"Ключи в первой записи: {list(first_record.keys())}")
        logger.info(f"Первая запись: {first_record}")

    # Подсчитываем записи с ИНН
    records_with_inn = sum(1 for item in data if item.get("ИНН организации"))
    logger.info(f"Записей с ИНН: {records_with_inn}")


def main():
    """
    Основная функция для объединения JSON файлов и записи в Excel
    """
    file1_path = "okmot_companies.json"
    file2_path = "organization_data.json"
    output_file = "merged_organizations.xlsx"

    # Проверяем существование файлов
    if not Path(file1_path).exists():
        logger.error(f"Файл {file1_path} не найден")
        return

    if not Path(file2_path).exists():
        logger.error(f"Файл {file2_path} не найден")
        return

    # Загружаем и анализируем данные
    data1 = load_json_file(file1_path)
    data2 = load_json_file(file2_path)

    analyze_data_structure(data1, file1_path)
    analyze_data_structure(data2, file2_path)

    # Объединяем данные
    merged_data = merge_json_data(file1_path, file2_path)

    if merged_data:
        # Сохраняем в Excel
        if save_to_excel(merged_data, output_file):
            logger.info(
                f"✓ Операция завершена успешно. Результат сохранён в {output_file}"
            )
        else:
            logger.error("✗ Не удалось сохранить данные в Excel")
    else:
        logger.error("✗ Нет данных для сохранения")


if __name__ == "__main__":
    main()
