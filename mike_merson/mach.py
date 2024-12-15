import json

# Пути к файлам
main_file_path = "jameda_de.json"
secondary_file_path = "doctolib_de.json"
merged_file = "merged_file.json"


def merge_json_data(main_file, secondary_file):
    # Открываем основной файл
    with open(main_file, "r", encoding="utf-8") as main_f:
        main_data = json.load(main_f)

    # Открываем второстепенный файл
    with open(secondary_file, "r", encoding="utf-8") as secondary_f:
        secondary_data = json.load(secondary_f)["data"]  # Извлекаем список врачей

    # Создаем словарь для быстрого поиска по имени в основном файле
    main_names = {entry["name"]: entry for entry in main_data}

    # Проходим по каждому врачу из второстепенного файла
    for secondary_entry in secondary_data:
        secondary_name = secondary_entry.get("name")
        secondary_url = secondary_entry.get("url_doctor")

        if not secondary_name or not secondary_url:
            continue  # Пропускаем записи без имени или URL

        if secondary_name in main_names:
            # Если врач уже есть в основном файле
            main_entry = main_names[secondary_name]
            # Добавляем URL в service_urls
            main_entry.setdefault("service_urls", [])
            if "url_doctor" in main_entry:
                if main_entry["url_doctor"] not in main_entry["service_urls"]:
                    main_entry["service_urls"].append(main_entry["url_doctor"])
                del main_entry["url_doctor"]

            if secondary_url not in main_entry["service_urls"]:
                main_entry["service_urls"].append(secondary_url)

            # Добавляем doctolib_data
            main_entry["doctolib_data"] = secondary_entry
            del main_entry["doctolib_data"][
                "url_doctor"
            ]  # Удаляем url_doctor из doctolib_data
        else:
            # Если врача нет в основном файле, добавляем его как новую запись
            new_entry = {
                "doctolib_data": secondary_entry,
                "service_urls": [secondary_url],
            }
            del new_entry["doctolib_data"][
                "url_doctor"
            ]  # Удаляем url_doctor из doctolib_data
            main_data.append(new_entry)

    # Сохраняем обновленный основной файл
    with open(merged_file, "w", encoding="utf-8") as main_f:
        json.dump(main_data, main_f, ensure_ascii=False, indent=4)

    print(f"Данные успешно объединены и сохранены в {merged_file}")


# Запуск функции
merge_json_data(main_file_path, secondary_file_path)
