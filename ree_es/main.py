import json
import random
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()

json_voltage_directory = current_directory / "json_voltage"
json_node_directory = current_directory / "json_node"
configuration_directory = current_directory / "configuration"

json_voltage_directory.mkdir(parents=True, exist_ok=True)
json_node_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

all_node_json_file = json_voltage_directory / "all_node.json"
config_txt_file = configuration_directory / "config.txt"
result_json_file = current_directory / "all_combined_data.json"


def random_pause(min_seconds=30, max_seconds=60):
    pause_duration = random.uniform(min_seconds, max_seconds)
    time.sleep(pause_duration)
    return pause_duration


def get_cookies():
    # Чтение строки curl из файла
    with open(config_txt_file, "r", encoding="utf-8") as f:
        curl_text = f.read()

    # Инициализация словарей для заголовков и кук
    headers = {}
    cookies = {}

    # Извлечение всех заголовков из параметров `-H`
    header_matches = re.findall(r"-H '([^:]+):\s?([^']+)'", curl_text)
    for header, value in header_matches:
        if header.lower() == "cookie":
            # Обработка куки отдельно, разделяя их по `;`
            cookies = {
                k.strip(): v
                for pair in value.split("; ")
                if "=" in pair
                for k, v in [pair.split("=", 1)]
            }
        else:
            headers[header] = value

    return headers, cookies


def get_json_node():
    node_values = get_all_node()
    all_node = int(len(node_values))
    headers, cookies = get_cookies()

    params = {
        "_wrapper_format": "drupal_ajax",
    }
    for node in node_values:

        data = {
            "group": "GI",
            "zone": "NODES",
            "ccaa": "",
            "node": node,
            "_drupal_ajax": "1",
            "ajax_page_state[theme]": "ree",
            "ajax_page_state[theme_token]": "",
            "ajax_page_state[libraries]": "eJyNk1t24yAMQDdEzNeshyNAxiQYcZCcxrP6ymmS5jFt5scHLteSJWSIUQjqauGyGMZOVYxHEewOT40Yoxtz0S3bhBU7FOOJhKVDcyxrQbatLCnXwUM4pE5LjS5QoT74JZf4s0494nvp5HiCSB9vxBn62f9ValporumNxaFTKQ7HEYPwG1nwJA5KTnXGKv8j3_cmUEdbqc8a4S-asLDQ7CAEZHap52hf0dUKE3RhJ0z2hdwcokNGT2JL9h366j7Qd7xliiBQYMVun8GLcXnzRXyKiEdtA9uH3fUs15E8FQb7DK5Ggw6B5kb1HCUV8lB2G03azemmLb7kAJKp3lLdM_Ndl8cJjpk6m0SUCjqBZJM-nvcD7OH0CGejMWgRFzMHOmJfrX6Y3p8pCGNBcTp1B-yh6CdorgvdPVBTQRCP5Fqn_TZQ-lK7Vqajlps26FdHR0iH1ty6wDb2pUEZvsmw1HP9PGE02y15YPxaXEfxz27Pu6J5WM4HT9E3NOuIQUI2jNDD5KBlB4vQdiNaF9ofuOG8LVyjtjTnC4UD238wwxQyFDdjzOA07aa9oEEmnDXmqt2bvwoRr0IC_cMWez4d7sgnT87m7g",
        }
        json_file = json_node_directory / f"node_{node}.json"

        # Пропускаем, если файл уже существует
        if json_file.exists():
            logger.info(f"Пропускаем node_{node}.json")
            continue
        response = requests.post(
            "https://www.ree.es/access_grid/getdata",
            params=params,
            cookies=cookies,
            headers=headers,
            data=data,
            timeout=60,
        )

        # Проверка кода ответа
        if response.status_code == 200:
            json_data = response.json()

            # Записываем данные в файл
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            logger.info(f"Файл сохранен: {f'node_{node}.json'}")

            # Подсчитываем количество файлов в папке
            file_count = len(list(json_node_directory.glob("*.json")))
            balance_count = all_node - file_count
            logger.info(f"Осталось файлов: {balance_count}")
            pause = random_pause(30, 60)  # Пауза в диапазоне 30-60 секунд
            logger.info(f"Пауза {pause:.2f} сек")
        else:
            logger.error(f"Ошибка: {response.status_code} для узла {node}")


# def extract_data():
#     combined_data = []

#     with open(all_node_json_file, "r", encoding="utf-8") as file:
#         all_nodes = json.load(file)


#     for json_file in json_node_directory.glob("node_*.json"):
#         with open(json_file, "r", encoding="utf-8") as file:
#             data = json.load(file)

#         main_data = {}

#         for item in data:
#             html_data = item.get("data")
#             soup = BeautifulSoup(html_data, "html.parser")

#             province_tag = soup.select_one(".ree-acceso-red-modal-province")
#             province = province_tag.text.strip() if province_tag else "Unknown"
#             if province not in main_data:
#                 main_data[province] = {}

#             # Разделение на секции данных (категории узлов)
#             node_categories = [
#                 "Datos de capacidad de acceso de instalaciones (MW)",
#                 "Datos de potencia instalada de módulos (MW)",
#             ]
#             node_texts = [
#                 span.text.strip()
#                 for span in soup.find_all("span")
#                 if span.text.strip() in node_categories
#             ]

#             graphs = soup.select("div[class^='ree-acceso-red-modal-graph-']")
#             midpoint = len(graphs) // 2
#             graph_groups = [graphs[:midpoint], graphs[midpoint:]]

#             for category_index, node_text in enumerate(node_texts):
#                 if node_text not in main_data[province]:
#                     main_data[province][node_text] = {}

#                 related_graphs = (
#                     graph_groups[category_index]
#                     if category_index < len(graph_groups)
#                     else []
#                 )

#                 for graph in related_graphs:
#                     section_tag = graph.select_one(".graph-label")
#                     section = section_tag.text.strip() if section_tag else "Unknown"

#                     if section not in main_data[province][node_text]:
#                         main_data[province][node_text][section] = []

#                     table_section = graph.select_one(
#                         "div[class^='table-subgraph']")
#                     if table_section:
#                         cells = [
#                             cell.text.strip() for cell in table_section.select("td")
#                         ]
#                         extracted_data = {}

#                         # Проверяем и пропускаем первую строку таблицы, если она содержит заголовки "RdT" и "RdD"
#                         if cells[:3] == ["", "RdT", "RdD"]:
#                             # Убираем первую строку с заголовками
#                             cells = cells[3:]

#                         # Ожидается структура с 3 столбцами на каждую строку (категория, RdT, RdD)
#                         for i in range(0, len(cells), 3):
#                             if i + 2 < len(cells):
#                                 category = cells[i]
#                                 rdt_value = cells[i + 1]
#                                 rdd_value = cells[i + 2]

#                                 extracted_data[f"{category} RdT"] = rdt_value
#                                 extracted_data[f"{category} RdD"] = rdd_value

#                         main_data[province][node_text][section].append(
#                             extracted_data)

#                 # Логирование для проверки да
#         logger.info(main_data)

#         combined_data.append(main_data)

#     save_to_json(combined_data)

def extract_data():
    combined_data = []

    # Загрузка all_nodes из файла
    with open(all_node_json_file, "r", encoding="utf-8") as file:
        all_nodes = json.load(file)

    # Создаем словарь для быстрого доступа к координатам по названию
    node_coordinates = {node["title"]: {
        "lat": node["lat"], "lng": node["lng"]} for node in all_nodes}

    for json_file in json_node_directory.glob("node_*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        main_data = {}

        for item in data:
            html_data = item.get("data")
            soup = BeautifulSoup(html_data, "html.parser")

            province_tag = soup.select_one(".ree-acceso-red-modal-province")
            province = province_tag.text.strip() if province_tag else "Unknown"

            # Если province не в main_data, создаем структуру данных
            if province not in main_data:
                main_data[province] = {}

                # Проверяем, есть ли координаты для province в node_coordinates
                if province in node_coordinates:
                    main_data[province]["lat"] = node_coordinates[province]["lat"]
                    main_data[province]["lng"] = node_coordinates[province]["lng"]
                else:
                    main_data[province]["lat"] = "Unknown"
                    main_data[province]["lng"] = "Unknown"

            # Разделение на секции данных (категории узлов)
            node_categories = [
                "Datos de capacidad de acceso de instalaciones (MW)",
                "Datos de potencia instalada de módulos (MW)",
            ]
            node_texts = [
                span.text.strip()
                for span in soup.find_all("span")
                if span.text.strip() in node_categories
            ]

            graphs = soup.select("div[class^='ree-acceso-red-modal-graph-']")
            midpoint = len(graphs) // 2
            graph_groups = [graphs[:midpoint], graphs[midpoint:]]

            for category_index, node_text in enumerate(node_texts):
                if node_text not in main_data[province]:
                    main_data[province][node_text] = {}

                related_graphs = (
                    graph_groups[category_index]
                    if category_index < len(graph_groups)
                    else []
                )

                for graph in related_graphs:
                    section_tag = graph.select_one(".graph-label")
                    section = section_tag.text.strip() if section_tag else "Unknown"

                    if section not in main_data[province][node_text]:
                        main_data[province][node_text][section] = []

                    table_section = graph.select_one(
                        "div[class^='table-subgraph']")
                    if table_section:
                        cells = [cell.text.strip()
                                 for cell in table_section.select("td")]
                        extracted_data = {}

                        # Проверяем и пропускаем первую строку таблицы, если она содержит заголовки "RdT" и "RdD"
                        if cells[:3] == ["", "RdT", "RdD"]:
                            # Убираем первую строку с заголовками
                            cells = cells[3:]

                        # Ожидается структура с 3 столбцами на каждую строку (категория, RdT, RdD)
                        for i in range(0, len(cells), 3):
                            if i + 2 < len(cells):
                                category = cells[i]
                                rdt_value = cells[i + 1]
                                rdd_value = cells[i + 2]

                                extracted_data[f"{category} RdT"] = rdt_value
                                extracted_data[f"{category} RdD"] = rdd_value

                        main_data[province][node_text][section].append(
                            extracted_data)

            # Логирование для проверки данных

        combined_data.append(main_data)

    save_to_json(combined_data)


def save_to_json(data):
    """
    Сохраняет данные в JSON-файл с форматированием.
    :param data: Словарь данных для сохранения
    """
    with open(result_json_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"Данные успешно сохранены в {result_json_file}")


def save_json_all_node():

    headers, cookies = get_cookies()
    vols = [66, 132, 220, 400]
    for vol in vols:
        params = {
            "vol": vol,
            "group": "GI",
        }

        response = requests.get(
            "https://www.ree.es/es/access_grid/getnodes",
            params=params,
            headers=headers,
            timeout=60,
        )
        if response.status_code == 200:
            json_data = response.json()
            json_csv_file = json_voltage_directory / f"voltage_{vol}.json"
            with open(json_csv_file, "w", encoding="utf-8") as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
            logger.info(json_csv_file)
            # Генерирует случайную паузу между 30 и 60 секундами
            pause = random_pause(30, 60)
            time.sleep(pause)  # Пауза на случайное время
        else:
            logger.error(response.status_code)


def get_all_node_voltage():
    combined_data = []

    for json_file in json_voltage_directory.glob("voltage_*.json"):

        # Извлечение нужных полей из каждого файла
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            for item in data.values():
                combined_data.append(
                    {"nudo": item["nudo"], "title": item["title"], "lat": item["lat"], "lng": item["lng"]})

    # Сохранение объединённых данных в файл all_node.json
    with open(all_node_json_file, "w", encoding="utf-8") as output_file:
        json.dump(combined_data, output_file, ensure_ascii=False, indent=4)
    logger.info(len(combined_data))


def get_all_node():
    with open(all_node_json_file, "r", encoding="utf-8") as file:
        data = json.load(file)
        node_list = [item["nudo"] for item in data]
    return node_list


def main_loop():
    """Основной цикл программы для обработки пользовательских команд.

    Функция выводит меню команд, запрашивает у пользователя действие и выполняет
    соответствующие задачи, такие как загрузка sitemap, HTML файлов, парсинг,
    скачивание изображений и сохранение результатов. Ввод проверяется на корректность,
    и при ошибках программа повторно запрашивает команду.

    Available commands:
        1: Запустить полный процесс
        2: Получить весь список Node
        3: Скачать все файлы Node
        4: Сформировать файл с результатом
        0: Завершить программу
    """
    while True:
        print(
            "\nВыберите действие:\n"
            "1 - Запустить полный процесс\n"
            "2 - Получить весь список Node\n"
            "3 - Скачать все файлы Node\n"
            "4 - Сформировать файл с результатом\n"
            "0 - Завершить программу"
        )

        # Проверка ввода от пользователя
        try:
            user_input = int(input("Введите номер действия: "))
            if user_input not in range(5):
                raise ValueError
        except ValueError:
            print("Ошибка: Введите корректное число от 0 до 4.")
            continue

        if user_input == 1:
            save_json_all_node()
            get_all_node_voltage()
            get_json_node()
            extract_data()

        elif user_input == 2:
            save_json_all_node()
            get_all_node_voltage()

        elif user_input == 3:
            get_json_node()

        elif user_input == 4:
            extract_data()

        elif user_input == 0:
            print("Программа завершена.")
            break  # Завершение программы


if __name__ == "__main__":
    main_loop()
