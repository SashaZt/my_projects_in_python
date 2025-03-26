import asyncio
import csv
import glob
import json
import os
import re
import sys
import time

import aiomysql
import mysql.connector
import pdfplumber

current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
search_key_bat_path = os.path.join(temp_path, "search_key_bat")
search_key_building_path = os.path.join(temp_path, "search_key_building")
search_key_capacity_path = os.path.join(temp_path, "search_key_capacity")
search_key_element_path = os.path.join(temp_path, "search_key_element")
search_key_info_path = os.path.join(temp_path, "search_key_info")
search_key_ty_path = os.path.join(temp_path, "search_key_ty")
search_results_path = os.path.join(temp_path, "search_results")
pdf_path = os.path.join(temp_path, "pdf")


def create_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [
        temp_path,
        search_key_bat_path,
        search_key_building_path,
        search_key_capacity_path,
        search_key_element_path,
        search_key_info_path,
        search_key_ty_path,
        search_results_path,
        pdf_path,
    ]:
        if not os.path.exists(folder):
            os.makedirs(folder)


def get_pdf():
    pass


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

    return config


# Функция для разбиения строки на подстроки и удаления пустых элементов
def split_and_clean(cell_content):
    # Проверяем, не является ли содержимое ячейки None
    if cell_content is not None:
        return [item.strip() for item in cell_content.split("\n") if item]
    else:
        return []  # Возвращаем пустой список, если содержимое ячейки None


def pars_pdf():
    folder_pdf = os.path.join(pdf_path, "*.pdf")

    files_pdf = glob.glob(folder_pdf)
    for item in files_pdf:
        # pdf_path = "K001880N40156410.pdf"
        # Открываем PDF-файл с помощью PDFPlumber

        with pdfplumber.open(item) as pdf:
            # Получаем первую страницу документа
            # index_page = 0
            # for page in pdf.pages:
            # index_page += 1
            for page_index, page in enumerate(pdf.pages):

                # first_page = pdf.pages
                # image = first_page[page_index].to_image()
                page_index = page_index + 1
                # image.debug_tablefinder()
                # image.save(f"analis_{page_index}.png")

                values_list_search_key_bat = []
                values_list_search_key_element = []
                values_list_search_key_building = []
                values_list_search_key_capacity = []
                values_list_search_key_info = []
                # Используем регулярное выражение для поиска "Key: " за которым следуют цифры
                # card_index = index
                page_text = page.extract_text()
                match = re.search(r"Key:\s*(\d+)", page_text)

                # Если совпадение найдено, извлекаем и печатаем число
                if match:
                    key_number = match.group(1)
                else:
                    print("Ключ не найден.")
                vertical_lines = [330, 430]  # Пример координат X для вертикальных линий
                horizontal_lines = [
                    190,
                    199,
                    205,
                    213,
                    221,
                    233,
                ]  # Пример координат Y для горизонтальных линий

                table_settings = {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": vertical_lines,
                    "horizontal_strategy": "explicit",
                    "explicit_horizontal_lines": horizontal_lines,
                }
                table_land = page.extract_tables(table_settings)
                result_dict = {}
                for row in table_land[
                    0
                ]:  # Предполагаем, что интересующая нас таблица - первая в списке
                    content = row[0].split(
                        " ", 1
                    )  # Разделяем строку на название и значение
                    if len(content) == 2:
                        # Если есть и название, и значение
                        key, value = content
                    else:
                        # Если значение отсутствует, ключу присваивается None или пустая строка
                        key = content[0]
                        value = None  # Или используйте None

                    # Удаляем запятые из числовых значений для унификации
                    # Добавляем в словарь
                    result_dict[key] = value

                values_list_search_key_info.append(result_dict)

                tables = page.extract_tables()

                for table in tables:

                    # # search_key_bat(key_number, table_index + 1, table)
                    #     for row in table:
                    #         print(row)
                    #     search_key_bat(key_number, index, table)

                    headers_first = table[0]  # Заголовки таблицы
                    search_headers_first = [
                        "CURRENT OWNER",
                        "PARCEL ID",
                        "LOCATION",
                        "CLASS",
                        "DESCRIPTION",
                        "BN",
                        "CARD",
                    ]
                    dict_search_key_info = {}
                    dict_search_key_info_02 = {}
                    dict_search_key_info_03 = {}
                    dict_search_key_info_04 = {}

                    for header_first in search_headers_first:
                        if header_first in headers_first:
                            index = headers_first.index(
                                header_first
                            )  # Получаем индекс нужной колонки

                            for row in table[1:2]:
                                # print(row)
                                value_first = row[index]  # Извлекаем значение ячейки
                                dict_search_key_info[header_first] = value_first
                    values_list_search_key_info.append(dict_search_key_info)

                    for dict_item in values_list_search_key_info:

                        # Проверяем наличие ключа 'CURRENT OWNER' и его разделение на части
                        if (
                            "CURRENT OWNER" in dict_item
                            and dict_item["CURRENT OWNER"].count("\n") == 3
                        ):
                            owner_parts = dict_item["CURRENT OWNER"].split("\n", 3)
                            dict_item["owner_data1"] = owner_parts[0]
                            dict_item["owner_data2"] = owner_parts[1]
                            dict_item["owner_data3"] = owner_parts[2]
                            dict_item["owner_data5"] = owner_parts[3]
                        elif (
                            "CURRENT OWNER" in dict_item
                            and dict_item["CURRENT OWNER"].count("\n") == 4
                        ):
                            owner_parts = dict_item["CURRENT OWNER"].split("\n", 4)
                            dict_item["owner_data1"] = owner_parts[0]
                            dict_item["owner_data2"] = owner_parts[1]
                            dict_item["owner_data3"] = owner_parts[2]
                            dict_item["owner_data4"] = owner_parts[3]
                            dict_item["owner_data5"] = owner_parts[4]
                        elif (
                            "CURRENT OWNER" in dict_item
                            and dict_item["CURRENT OWNER"].count("\n") == 2
                        ):
                            owner_parts = dict_item["CURRENT OWNER"].split("\n", 2)
                            dict_item["owner_data1"] = owner_parts[0]
                            # Если условие истинно, выполняем необходимые действия
                            # Например, присваиваем значение переменной owner_data3
                            if re.match(r"^\d", owner_parts[1]) or owner_parts[
                                1
                            ].startswith("PO BOX"):

                                dict_item["owner_data3"] = owner_parts[1]
                                dict_item["owner_data5"] = owner_parts[2]
                            else:
                                dict_item["owner_data3"] = owner_parts[1]
                                dict_item["owner_data5"] = owner_parts[2]
                            # dict_item["owner_data3"] = owner_parts[2]
                            # dict_item["owner_data4"] = owner_parts[3]
                            # dict_item["owner_data5"] = owner_parts[4]

                            # Удаление исходного ключа 'CURRENT OWNER'
                            del dict_item["CURRENT OWNER"]

                    headers_second = table[2]  # Заголовки таблицы

                    search_headers_second = [
                        "TRANSFER HISTORY",
                        "DOS",
                        "T",
                        "SALE PRICE",
                        "BK-PG (Cert)",
                    ]
                    for header_second in search_headers_second:
                        if header_second in headers_second:
                            index = headers_second.index(
                                header_second
                            )  # Получаем индекс нужной колонки
                            # Проходим по всем строкам, начиная со второй
                            for row in table[3:4]:
                                value_second = row[index].split("\n")[0]
                                dict_search_key_info_02[header_second] = value_second
                    values_list_search_key_info.append(dict_search_key_info_02)

                    headers_third = table[7]
                    search_headers = ["TOTAL", "ONING"]

                    for search_header in search_headers:
                        if search_header in headers_third:
                            header_index = headers_third.index(
                                search_header
                            )  # Находим индекс заголовка
                            target_index = (
                                header_index + 3
                            )  # Предполагается, что целевая ячейка через две клетки от заголовка

                            for row in table[7:8]:  # Обрабатывается только одна строка
                                if target_index < len(row):
                                    target_value = (
                                        row[target_index].replace("Z", "").strip()
                                    )
                                    dict_search_key_info_03[search_header] = (
                                        target_value  # Используем search_header как ключ
                                    )

                    values_list_search_key_info.append(dict_search_key_info_03)

                    headers_cell_15 = table[15][0]  # Заголовки в 27-й ячейке
                    values_cell_15 = table[15][5]  # Значения в 31-й ячейке
                    headers_15 = split_and_clean(headers_cell_15)
                    values_15 = split_and_clean(values_cell_15)
                    # Обработка данных из таблицы 9

                    for header, value in zip(headers_15[:-1], values_15[:-1]):
                        dict_search_key_info_04[header] = value
                    values_list_search_key_info.append(dict_search_key_info_04)
                    filename_key_info = os.path.join(
                        search_key_info_path, f"{key_number}_{page_index}.json"
                    )
                    """Переименовать"""
                    keys_mapping = {
                        "PARCEL ID": "parcel_id",
                        "LOCATION": "location",
                        "CLASS": "class",
                        "DESCRIPTION": "description",
                        "CARD": "card_info",
                        "BN": "card",
                        "TRANSFER HISTORY": "transfer_history",
                        "DOS": "dos",
                        "SALE PRICE": "sale_price",
                        "BK-PG (Cert)": "bk_pg_cert",
                        "TOTAL": "acres",
                        "ONING": "zoming",
                        "LAND": "assesed_land",
                        "BUILDING": "assesed_building",
                        "DETACHED": "assesed__detached",
                        "OTHER": "assesed_other",
                        "YEAR BLT": "year_blt",
                        "NET AREA": "net_area",
                    }

                    # Итерация по списку словарей
                    for item in values_list_search_key_info:
                        for old_key, new_key in keys_mapping.items():
                            if old_key in item:
                                item[new_key] = item.pop(
                                    old_key
                                )  # Удаление старого ключа и добавление нового с сохранением значения

                    for item in values_list_search_key_info:
                        item["Keyno"] = key_number
                    for item in values_list_search_key_info:
                        item["card"] = page_index

                    # Создаем один словарь из списка словарей
                    combined_dict = {}
                    for single_dict in values_list_search_key_info:
                        combined_dict.update(single_dict)
                    list_with_one_dict = [combined_dict]
                    with open(filename_key_info, "w", encoding="utf-8") as f:
                        json.dump(list_with_one_dict, f, ensure_ascii=False, indent=4)

                    # headers_cell_8 = table[8][27]  # Заголовки в 27-й ячейке
                    # values_cell_8 = table[8][31]  # Значения в 31-й ячейке
                    # headers_8 = split_and_clean(headers_cell_8)
                    # values_8 = split_and_clean(values_cell_8)

                    # # Инициализируем словарь с пустыми строками для каждого заголовка
                    # values_dict = {header: "" for header in ["LAND", "BUILDING", "DETACHED", "OTHER"]}

                    # # Заполняем словарь данными
                    # for header in values_dict.keys():
                    #     if header in headers_8:
                    #         # Получаем индекс заголовка в headers_8
                    #         index = headers_8.index(header)
                    #         # Если соответствующее значение существует, заполняем его
                    #         if index < len(values_8):
                    #             values_dict[header] = values_8[index]
                    #         else:
                    #             # Если значение отсутствует, оставляем пустую строку
                    #             values_dict[header] = ""
                    #     else:
                    #         # Если заголовок отсутствует, оставляем пустую строку
                    #         values_dict[header] = ""

                    # # Выводим значения по каждому заголовку
                    # for header, value in values_dict.items():
                    #     print(f"{header}: {value}")

                    # # Обработка данных из таблицы 9
                    # total_value_9 = table[9][31]  # Общая сумма в 32-й ячейке
                    # # Выводим общую сумму
                    # print(f"TOTAL: {total_value_9}")

                    """search_key_building"""
                    headers_cell_14 = table[14][0]  # Заголовки в 27-й ячейке
                    values_cell_14 = table[14][4]  # Значения в 31-й ячейке
                    values_cell_02_14 = table[14][8]  # Значения в 31-й ячейке
                    headers_14 = split_and_clean(headers_cell_14)
                    values_14 = split_and_clean(values_cell_14)
                    values_02_14 = split_and_clean(values_cell_02_14)

                    # Сопоставляем заголовки и значения
                    for header, value, value_02 in zip(
                        headers_14, values_14, values_02_14
                    ):
                        dict_search_key_building = {
                            "Keyno": key_number,
                            "card": page_index,
                            "bld_type": header,
                            "cd": value,
                            "bld_desc": value_02,
                        }
                        values_list_search_key_building.append(dict_search_key_building)
                    filename_key_buildin = os.path.join(
                        search_key_building_path, f"{key_number}_{page_index}.json"
                    )
                    with open(filename_key_buildin, "w", encoding="utf-8") as f:
                        json.dump(
                            values_list_search_key_building,
                            f,
                            ensure_ascii=False,
                            indent=4,
                        )

                    #     print(f"{header}: {value}")

                    """search_key_element"""
                    headers_cell_16 = table[16][16]  # Заголовки в 27-й ячейке
                    values_cell_16 = table[16][23]  # Значения в 31-й ячейке
                    values_02_cell_16 = table[16][24]  # Значения в 31-й ячейке
                    values_02_cell_16 = table[16][24]  # Значения в 31-й ячейке
                    headers_16 = split_and_clean(headers_cell_16)
                    values_16 = split_and_clean(values_cell_16)
                    values_02_16 = split_and_clean(values_02_cell_16)

                    # Обработка данных из таблицы 9

                    # Сопоставляем заголовки и значения
                    for header, value, value_02 in zip(
                        headers_16, values_16, values_02_16
                    ):

                        current_dict_search_key_element = {
                            "Keyno": key_number,
                            "card": page_index,
                            "el_type": header,
                            "el_code": value,
                            "el_desc": value_02,
                        }
                        values_list_search_key_element.append(
                            current_dict_search_key_element
                        )
                    filename_key_element = os.path.join(
                        search_key_element_path, f"{key_number}_{page_index}.json"
                    )
                    with open(filename_key_element, "w", encoding="utf-8") as f:
                        json.dump(
                            values_list_search_key_element,
                            f,
                            ensure_ascii=False,
                            indent=4,
                        )  # Записываем в файл

                    """search_key_bat"""
                    headers_cell_17 = table[16][33]  # Заголовки в 27-й ячейке
                    values_cell_17 = table[16][34]  # Значения в 31-й ячейке
                    values_02_cell_17 = table[16][35]  # Значения в 31-й ячейке
                    values_03_cell_17 = table[16][36]  # Значения в 31-й ячейке
                    values_04_cell_17 = table[16][39]  # Значения в 31-й ячейке

                    headers_17 = split_and_clean(headers_cell_17)
                    values_17 = split_and_clean(values_cell_17)
                    values_02_17 = split_and_clean(values_02_cell_17)
                    values_03_17 = split_and_clean(values_03_cell_17)
                    values_04_17 = split_and_clean(values_04_cell_17)

                    # Определяем максимальную длину среди всех списков
                    max_length = max(
                        len(headers_17),
                        len(values_17),
                        len(values_02_17),
                        len(values_03_17),
                        len(values_04_17),
                    )

                    # Дополняем каждый список до максимальной длины, если это необходимо
                    headers_17 += [None] * (max_length - len(headers_17))
                    values_17 += [None] * (max_length - len(values_17))
                    values_02_17 += [None] * (max_length - len(values_02_17))
                    values_03_17 += [None] * (max_length - len(values_03_17))
                    values_04_17 += [None] * (max_length - len(values_04_17))

                    # Теперь вы можете безопасно итерировать по спискам, используя zip, без риска получить ошибку
                    for header, value, value_02, value_03, value_04 in zip(
                        headers_17, values_17, values_02_17, values_03_17, values_04_17
                    ):
                        header_str = (
                            "" if header is None else header.replace("None", "")
                        )

                        current_dict_search_key_bat = {
                            "Keyno": key_number,
                            "card": page_index,
                            "bat": f"{header_str} {value}",
                            "bat_t": value_02,
                            "bat_desc": value_03,
                            "bat_units": (
                                value_04.replace(",", "")
                                if value_04 is not None
                                else None
                            ),
                        }
                        values_list_search_key_bat.append(current_dict_search_key_bat)
                    filename_key_bat = os.path.join(
                        search_key_bat_path, f"{key_number}_{page_index}.json"
                    )
                    with open(filename_key_bat, "w", encoding="utf-8") as f:
                        json.dump(
                            values_list_search_key_bat, f, ensure_ascii=False, indent=4
                        )  # Записываем в файл

                    """search_key_capacity"""
                    headers_cell_18 = table[19][0]  # Заголовки в 27-й ячейке
                    values_cell_18 = table[19][9]  # Значения в 31-й ячейке
                    headers_18 = split_and_clean(headers_cell_18)
                    values_18 = split_and_clean(values_cell_18)
                    # Сопоставляем заголовки и значения
                    for header, value in zip(headers_18, values_18):

                        current_dict_search_key_capacity = {
                            "Keyno": key_number,
                            "card": page_index,
                            "cap_type": header,
                            "cap_units": value,
                        }
                        values_list_search_key_capacity.append(
                            current_dict_search_key_capacity
                        )
                    filename_key_capacity = os.path.join(
                        search_key_capacity_path, f"{key_number}_{page_index}.json"
                    )
                    with open(filename_key_capacity, "w", encoding="utf-8") as f:
                        json.dump(
                            values_list_search_key_capacity,
                            f,
                            ensure_ascii=False,
                            indent=4,
                        )  # Записываем в файл


def get_table_names():
    config = load_config()
    db_config = config["db_config"]
    """Получение списка имен таблиц из базы данных."""
    table_names = []
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        cursor.execute("SHOW TABLES;")
        table_names = [table_name[0] for table_name in cursor.fetchall()]
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()
    return table_names


def check_data_exists(table_name, keyno, card):
    config = load_config()
    db_config = config["db_config"]
    """Проверка наличия данных в таблице по Keyno и card."""
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        query = f"SELECT COUNT(*) FROM {table_name} WHERE Keyno = %s AND card = %s"
        cursor.execute(query, (keyno, card))
        (count,) = cursor.fetchone()
        return count > 0
    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


def insert_data_into_table(table_name, data):
    config = load_config()
    db_config = config["db_config"]

    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()

        # Получение списка колонок для таблицы
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns_info = cursor.fetchall()
        # Создаем словарь для проверки, можно ли колонку оставить пустой (если может быть NULL)
        column_can_be_null = {col[0]: (col[2] == "YES") for col in columns_info}

        for record in data:
            # Фильтруем запись JSON, оставляя только те поля, которые существуют в SQL таблице
            filtered_record = {
                k: v for k, v in record.items() if k in column_can_be_null
            }
            # Строим список колонок и соответствующих значений для вставки
            columns_str = ", ".join(filtered_record.keys())
            placeholders = ", ".join(["%s"] * len(filtered_record))
            values = tuple(filtered_record.values())
            # Если после фильтрации не осталось колонок для вставки, пропускаем эту запись
            if not columns_str:
                continue

            # Составление и выполнение запроса на вставку
            insert_query = (
                f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            )
            cursor.execute(insert_query, values)

        cnx.commit()
        print(f"Данные успешно вставлены в таблицу {table_name}.")

    except mysql.connector.Error as err:
        print(f"Ошибка при вставке данных в {table_name}: {err}")

    finally:
        if cnx.is_connected():
            cursor.close()
            cnx.close()


# def insert_data_into_table(table_name, data):
#     config = load_config()
#     db_config = config["db_config"]
#     """Вставка данных из JSON файла в соответствующую таблицу базы данных."""
#     try:
#         cnx = mysql.connector.connect(**db_config)
#         cursor = cnx.cursor()
#         cursor.execute(f"SHOW COLUMNS FROM {table_name}")
#         columns_info = cursor.fetchall()
#         sql_columns = [col[0] for col in columns_info]

#         for record in data:
#         # Дополнение record значениями None для отсутствующих полей
#             for col in sql_columns:
#                 if col not in record:
#                     record[col] = None  # или другое значение по умолчанию, например 0 или ''

#             common_columns = [col for col in sql_columns if col in record]
#             values = [record[col] for col in common_columns]

#             if not common_columns:
#                 continue

#             columns_str = ", ".join(common_columns)
#             placeholders = ", ".join(["%s"] * len(common_columns))
#             insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
#             cursor.execute(insert_query, values)


#         cnx.commit()
#     finally:
#         if cnx.is_connected():
#             cursor.close()
#             cnx.close()


def process_json_files():
    """Чтение JSON файлов из папок, соответствующих именам таблиц и вставка в БД."""
    table_names = get_table_names()
    for table_name in table_names:
        folder_path = os.path.join(temp_path, table_name)
        for json_file_path in glob.glob(f"{folder_path}/*.json"):
            filename = os.path.basename(json_file_path)
            keyno, card = filename.rstrip(".json").split("_")
            try:
                if check_data_exists(table_name, keyno, card):
                    continue
            except:
                print(f"Данные успешно вставлены в таблицу {table_name}")
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                insert_data_into_table(table_name, data)


def insert_data_into_csv(table_name, data):
    """
    Вставка данных из JSON файла в CSV-файл.

    Args:
        table_name (str): Имя таблицы (будет использовано как часть имени файла)
        data (list): Список словарей с данными для вставки
    """
    # Создаем директорию для CSV-файлов, если она не существует
    csv_path = os.path.join(os.getcwd(), "csv_output")
    if not os.path.exists(csv_path):
        os.makedirs(csv_path)

    # Формируем путь к файлу CSV
    csv_file_path = os.path.join(csv_path, f"{table_name}.csv")

    # Определяем, существует ли уже файл (для добавления заголовков)
    file_exists = os.path.isfile(csv_file_path)

    # Если данные пустые, не выполняем запись
    if not data:
        print(f"Нет данных для записи в {table_name}.csv")
        return

    # Собираем все возможные заголовки из всех записей
    fieldnames = set()
    for record in data:
        fieldnames.update(record.keys())

    # Преобразуем в список и сортируем для последовательности
    fieldnames = sorted(list(fieldnames))

    # Открываем файл в режиме добавления или записи
    mode = "a" if file_exists else "w"
    with open(csv_file_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # Записываем заголовки только если файл создается впервые
        if not file_exists:
            writer.writeheader()

        # Записываем данные
        for record in data:
            # Заполняем пустые поля значением None
            for field in fieldnames:
                if field not in record:
                    record[field] = None
            writer.writerow(record)

    print(f"Данные успешно записаны в файл {csv_file_path}")


def process_json_files_to_csv():
    """
    Чтение JSON файлов из папок и запись данных в CSV-файлы
    вместо вставки в базу данных.
    """
    # Получаем все поддиректории temp_path
    folders = [
        f for f in os.listdir(temp_path) if os.path.isdir(os.path.join(temp_path, f))
    ]

    # Фильтруем только те директории, которые начинаются с "search_key_"
    table_folders = [f for f in folders if f.startswith("search_key_")]

    for folder_name in table_folders:
        folder_path = os.path.join(temp_path, folder_name)
        table_name = folder_name  # Используем имя папки как имя таблицы

        # Обрабатываем все JSON файлы в папке
        json_files = glob.glob(os.path.join(folder_path, "*.json"))

        for json_file_path in json_files:
            try:
                with open(json_file_path, "r", encoding="utf-8") as json_file:
                    data = json.load(json_file)
                    insert_data_into_csv(table_name, data)
            except Exception as e:
                print(f"Ошибка при обработке файла {json_file_path}: {e}")


if __name__ == "__main__":
    create_folders()
    pars_pdf()
    # process_json_files()
    process_json_files_to_csv()
