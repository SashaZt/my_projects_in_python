import json
import re
from pathlib import Path
import os


def extract_data_from_json_file(json_file_path):
    """Извлекает данные из JSON-файла"""
    try:
        # Сначала проверяем, что файл не пустой
        if os.path.getsize(json_file_path) == 0:
            print(f"Файл {json_file_path} пуст.")
            return None

        # Проверяем содержимое файла
        with open(json_file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                print(f"Файл {json_file_path} содержит только пробельные символы.")
                return None

            # Печать первых 100 символов для диагностики
            print(
                f"Первые 100 символов файла {json_file_path}: {content[:100].replace('\n', '\\n')}"
            )

            # Пытаемся загрузить JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Ошибка декодирования JSON в файле {json_file_path}: {e}")
                return None

        # Дальнейшая обработка данных
        return extract_data_from_json_object(data)

    except Exception as e:
        print(f"Ошибка при обработке файла {json_file_path}: {e}")
        return None


def extract_data_from_json_object(data):
    """Обрабатывает JSON-объект после его загрузки"""
    try:
        # Извлечение строки запроса
        if "json" not in data:
            print("В данных отсутствует ключ 'json'")
            return None

        query_string = data["json"]

        # Поиск taxNumber с помощью регулярного выражения
        match = re.search(r'"taxNumber"\s*:\s*"(\d+)"', query_string)
        search_term = match.group(1) if match else None

        # Проверка на наличие клиентов
        if "clients" not in data or not data["clients"]:
            print("В данных отсутствуют клиенты")
            return None

        # Извлечение данных из первого клиента (или можно обработать всех клиентов)
        client = data["clients"][0]
        taxNumber = client.get("taxNumber")
        address = client.get("address")

        return {"edrpo": search_term, "taxNumber": taxNumber, "address": address}

    except Exception as e:
        print(f"Ошибка при извлечении данных из JSON: {e}")
        return None


def process_json_files(json_directory):
    """Обрабатывает все JSON-файлы в указанной директории"""
    results = []

    # Проверка существования директории
    if not json_directory.exists():
        print(f"Директория {json_directory} не существует.")
        return results

    # Печать списка файлов для диагностики
    print(f"Файлы в директории {json_directory}:")
    for file_path in json_directory.iterdir():
        print(f" - {file_path}")

    # Обработка только JSON-файлов
    for json_file in json_directory.glob("*.json"):
        print(f"Обработка файла: {json_file}")
        data = extract_data_from_json_file(json_file)
        if data:
            results.append(data)

    return results


def main():
    # Вывод текущей директории для диагностики
    current_directory = Path.cwd()
    print(f"Текущая рабочая директория: {current_directory}")

    # Путь к директории с JSON-файлами
    json_directory = current_directory / "json"
    print(f"Путь к директории с JSON: {json_directory}")

    # Обработка файлов
    processed_data = process_json_files(json_directory)
    print(f"Обработано файлов: {len(processed_data)}")

    # Запись результатов
    if processed_data:
        output_file = current_directory / "combined_data.json"
        with open(output_file, "w", encoding="utf-8") as outfile:
            json.dump(processed_data, outfile, ensure_ascii=False, indent=4)
        print(f"Результаты сохранены в файл: {output_file}")
    else:
        print("Нет данных для сохранения.")


# Альтернативная функция для обработки строки JSON, предоставленной пользователем
def process_json_string(json_string):
    try:
        data = json.loads(json_string)
        return extract_data_from_json_object(data)
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")
        return None
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        return None


if __name__ == "__main__":
    # Можно выбрать, какую функцию использовать
    # 1. Обработка файлов в директории
    main()

    # 2. Или обработка предоставленного JSON-строки
    # json_string = '''{"json": "..."}'''  # Вставьте ваш JSON сюда
    # result = process_json_string(json_string)
    # if result:
    #     print(json.dumps(result, ensure_ascii=False, indent=4))
