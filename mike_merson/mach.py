# import json

# # Пути к файлам
# main_file_path = "jameda_de_13_12_.json"
# secondary_file_path = "doctolib_de.json"
# merged_file = "merged_file.json"


# def merge_json_data(main_file, secondary_file):
#     # Открываем основной файл
#     with open(main_file, "r", encoding="utf-8") as main_f:
#         main_data = json.load(main_f)

#     # Открываем второстепенный файл
#     with open(secondary_file, "r", encoding="utf-8") as secondary_f:
#         secondary_data = json.load(secondary_f)["data"]  # Извлекаем список врачей

#     # Создаем словарь для быстрого поиска по имени в основном файле
#     main_names = {entry["name"]: entry for entry in main_data}

#     # Проходим по каждому врачу из второстепенного файла
#     for secondary_entry in secondary_data:
#         secondary_name = secondary_entry.get("name")
#         secondary_url = secondary_entry.get("url_doctor")

#         if not secondary_name or not secondary_url:
#             continue  # Пропускаем записи без имени или URL

#         if secondary_name in main_names:
#             # Если врач уже есть в основном файле
#             main_entry = main_names[secondary_name]
#             # Добавляем URL в service_urls
#             main_entry.setdefault("service_urls", [])
#             if "url_doctor" in main_entry:
#                 if main_entry["url_doctor"] not in main_entry["service_urls"]:
#                     main_entry["service_urls"].append(main_entry["url_doctor"])
#                 del main_entry["url_doctor"]

#             if secondary_url not in main_entry["service_urls"]:
#                 main_entry["service_urls"].append(secondary_url)

#             # Добавляем focus-gesundheit.de
#             main_entry["focus-gesundheit.de"] = secondary_entry
#             del main_entry["focus-gesundheit.de"][
#                 "url_doctor"
#             ]  # Удаляем url_doctor из focus-gesundheit.de
#         else:
#             # Если врача нет в основном файле, добавляем его как новую запись
#             new_entry = {
#                 "focus-gesundheit.de": secondary_entry,
#                 "service_urls": [secondary_url],
#             }
#             del new_entry["focus-gesundheit.de"][
#                 "url_doctor"
#             ]  # Удаляем url_doctor из focus-gesundheit.de
#             main_data.append(new_entry)

#     # Сохраняем обновленный основной файл
#     with open(merged_file, "w", encoding="utf-8") as main_f:
#         json.dump(main_data, main_f, ensure_ascii=False, indent=4)

#     print(f"Данные успешно объединены и сохранены в {merged_file}")


# # Запуск функции
# merge_json_data(main_file_path, secondary_file_path)

# РАБОЧИЙ КОД ПОЛНОСТЬЮ
import json
import os

# Пути к файлам
main_file_path = "original_merged_file.json"
secondary_file_path = "dr-flex.de.json"
merged_file = "merged_file.json"
dictionary_name = "dr-flex.de"


def validate_secondary_entry(entry):
    """Проверяет наличие обязательных полей во второстепенных данных."""
    required_fields = ["name", "url_doctor"]
    return all(entry.get(field) for field in required_fields)


def merge_json_data(main_file, secondary_file):
    # Открываем основной файл
    with open(main_file, "r", encoding="utf-8") as main_f:
        main_data = json.load(main_f)

    # Открываем второстепенный файл
    with open(secondary_file, "r", encoding="utf-8") as secondary_f:
        secondary_data = json.load(secondary_f).get("data", [])

    # Создаем словарь для быстрого поиска по имени в основном файле
    main_names = {
        (entry.get("name", "") or "").strip(): entry
        for entry in main_data
        if entry.get("name") is not None
    }

    updated_data = main_data[:]

    for secondary_entry in secondary_data:
        if not validate_secondary_entry(secondary_entry):
            continue  # Пропускаем записи с отсутствующими полями

        secondary_name = secondary_entry["name"].strip()
        secondary_url = secondary_entry["url_doctor"]

        if secondary_name in main_names:
            # Если врач уже есть в основном файле
            main_entry = main_names[secondary_name]
            main_entry.setdefault("service_urls", [])

            # Добавляем URL, если он новый
            if secondary_url not in main_entry["service_urls"]:
                main_entry["service_urls"].append(secondary_url)

            # Добавляем focus-gesundheit.de как список словарей
            if dictionary_name not in main_entry:
                main_entry[dictionary_name] = []

            # Проверяем, чтобы запись была уникальной
            if secondary_entry not in main_entry[dictionary_name]:
                doctolib_copy = secondary_entry.copy()
                doctolib_copy.pop("url_doctor", None)  # Удаляем url_doctor
                main_entry[dictionary_name].append(doctolib_copy)
        else:
            # Если врача нет в основном файле
            new_entry = {
                "name": secondary_name,
                dictionary_name: [secondary_entry.copy()],
                "service_urls": [secondary_url],
            }
            new_entry[dictionary_name][0].pop("url_doctor", None)
            updated_data.append(new_entry)

    # Сохраняем результат
    with open(merged_file, "w", encoding="utf-8") as output_f:
        json.dump(updated_data, output_f, ensure_ascii=False, indent=4)

    print(f"Данные успешно объединены и сохранены в {merged_file}")


# Пути к файлам
merged_file = "merged_file.json"
output_folder = "output_parts"  # Папка для частей файла
chunk_size_mb = 200  # Размер каждой части в МБ


def split_json_file(input_file, output_dir, chunk_size_mb=None, num_parts=None):
    """
    Разделяет JSON файл на части, либо по размеру в МБ, либо по количеству частей.

    Args:
        input_file (str): Путь к входному JSON файлу.
        output_dir (str): Директория для сохранения частей.
        chunk_size_mb (int, optional): Размер каждой части в мегабайтах.
        num_parts (int, optional): Количество частей для разбиения.
    """
    # Читаем весь JSON файл
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Создаем папку для частей, если она не существует
    os.makedirs(output_dir, exist_ok=True)

    # Если указано количество частей, рассчитываем размер каждой части
    if num_parts:
        total_size = sum(
            len(json.dumps(entry, ensure_ascii=False).encode("utf-8")) for entry in data
        )
        chunk_size_bytes = total_size // num_parts
    elif chunk_size_mb:
        chunk_size_bytes = chunk_size_mb * 1024 * 1024
    else:
        raise ValueError("Необходимо указать либо chunk_size_mb, либо num_parts.")

    # Инициализация переменных
    current_chunk = []
    current_size = 0
    part_index = 1

    # Разделяем данные
    for entry in data:
        # Сериализуем текущую запись в строку и считаем её размер
        entry_bytes = json.dumps(entry, ensure_ascii=False).encode("utf-8")
        entry_size = len(entry_bytes)

        # Если текущий размер превышает лимит, сохраняем текущую часть
        if current_size + entry_size > chunk_size_bytes and part_index <= num_parts:
            output_file = os.path.join(output_dir, f"part_{part_index}.json")
            with open(output_file, "w", encoding="utf-8") as part_file:
                json.dump(current_chunk, part_file, ensure_ascii=False, indent=4)

            print(
                f"Сохранена часть {part_index} размером ~{current_size / (1024 * 1024):.2f} МБ"
            )
            # Начинаем новую часть
            current_chunk = []
            current_size = 0
            part_index += 1

        # Добавляем запись в текущую часть
        current_chunk.append(entry)
        current_size += entry_size

    # Сохраняем оставшиеся данные
    if current_chunk:
        output_file = os.path.join(output_dir, f"part_{part_index}.json")
        with open(output_file, "w", encoding="utf-8") as part_file:
            json.dump(current_chunk, part_file, ensure_ascii=False, indent=4)

        print(
            f"Сохранена часть {part_index} размером ~{current_size / (1024 * 1024):.2f} МБ"
        )

    print(f"Файл успешно разбит на {part_index} частей.")


if __name__ == "__main__":
    # объединение файлов
    # merge_json_data(main_file_path, secondary_file_path)
    # Разбиваем файл
    # split_json_file(merged_file, output_folder, chunk_size_mb)
    split_json_file("merged_file.json", "output_parts", num_parts=25)
