import json
import re
from pathlib import Path


def extract_data_from_json(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Извлечение строки запроса
    query_string = data["json"]

    # Поиск taxNumber с помощью регулярного выражения
    match = re.search(r'"taxNumber"\s*:\s*"(\d+)"', query_string)
    search_term = match.group(1) if match else None
    # Извлечение taxNumber из клиентов
    if "clients" in data and data["clients"]:
        client = data["clients"][0]
        taxNumber = client.get("taxNumber")
        address = data["clients"][0]["address"]

        return {"edrpo": search_term, "taxNumber": taxNumber, "address": address}

    return None


def process_json_files(json_directory):
    results = []
    for json_file in json_directory.glob("*.json"):
        data = extract_data_from_json(json_file)
        if data:
            results.append(data)

    return results


def main():
    current_directory = Path.cwd()
    json_directory = current_directory / "json"

    processed_data = process_json_files(json_directory)

    # Запись всех данных в один JSON файл
    output_file = current_directory / "combined_data.json"
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(processed_data, outfile, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    main()
