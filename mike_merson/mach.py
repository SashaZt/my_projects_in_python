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

import json

# Пути к файлам
main_file_path = "original_merged_file.json"
secondary_file_path = "focus_gesundheit_de.json"
merged_file = "merged_file.json"
dictionary_name = "focus-gesundheit.de"


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


# Запуск функции
merge_json_data(main_file_path, secondary_file_path)
