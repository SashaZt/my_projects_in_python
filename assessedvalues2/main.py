import pdfplumber
import re
import csv
import json


def get_pdf():
    pass


# Функция для разбиения строки на подстроки и удаления пустых элементов
def split_and_clean(cell_content):
    # Проверяем, не является ли содержимое ячейки None
    if cell_content is not None:
        return [item.strip() for item in cell_content.split("\n") if item]
    else:
        return []  # Возвращаем пустой список, если содержимое ячейки None


# def write_csv_search_key_bat():
#     values_list = search_key_bat()
#         # Определяем заголовки столбцов из ключей первого словаря в списке
#     headers = values_list[0].keys()

#     # Открываем файл для записи
#     with open(
#         "search_key_bat.csv", mode="a", newline="", encoding="utf-8"
#     ) as csv_file:
#         writer = csv.DictWriter(csv_file, fieldnames=headers, delimiter=";")

#         # Записываем заголовки столбцов
#         writer.writeheader()

#         # Записываем данные
#         for row in values_list:
#             writer.writerow(row)
    


def search_key_bat(key_number, table_index, table):
    values_list = []
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
        header_str = '' if header is None else header.replace('None', '')

        current_dict = {
            "Keyno": key_number,
            "card": table_index,
            "bat": f"{header_str} {value}",
            "bat_t": value_02,
            "bat_desc": value_03,
            "bat_units": value_04.replace(",", ""),  # Убираем запятые в 'bat_units'
        }
        values_list.append(current_dict)
    with open(f'0_{table_index}.json', 'w', encoding='utf-8') as f:
        json.dump(values_list, f, ensure_ascii=False, indent=4)  # Записываем в файл



def pars_pdf():
    pdf_path = "K000100N40157510.pdf"
    # Открываем PDF-файл с помощью PDFPlumber
    
    with pdfplumber.open(pdf_path) as pdf:
        # Получаем первую страницу документа
        # index_page = 0
        # for page in pdf.pages:
            # index_page += 1
        for page_index, page in enumerate(pdf.pages):
            page_index = page_index +1
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

            tables = page.extract_tables()
            
            for table in tables:
                
                # # search_key_bat(key_number, table_index + 1, table)
                #     for row in table:
                #         print(row)
            #     search_key_bat(key_number, index, table)

                headers_first = table[0]  # Заголовки таблицы
                search_headers_first = ["CURRENT OWNER", "PARCEL ID", "LOCATION", "CLASS",  "DESCRIPTION", "BN", "CARD"]
                dict_search_key_info = {}
                dict_search_key_info_02 = {}
                dict_search_key_info_03 = {}

                for header_first in search_headers_first:
                    if header_first in headers_first:
                        index = headers_first.index(header_first)  # Получаем индекс нужной колонки
                        # Проходим по всем строкам, начиная со второй
                        for row in table[1:2]:
                            value_first = row[index]  # Извлекаем значение ячейки
                            dict_search_key_info[header_first] = value_first
                values_list_search_key_info.append(dict_search_key_info)
                            
                for dict_item in values_list_search_key_info:
                    # Проверяем наличие ключа 'CURRENT OWNER' и его разделение на части
                    if 'CURRENT OWNER' in dict_item and dict_item['CURRENT OWNER'].count('\n') >= 3:
                        owner_parts = dict_item['CURRENT OWNER'].split('\n', 3)
                        dict_item['owner_data1'] = owner_parts[0]
                        dict_item['owner_data2'] = owner_parts[1]
                        dict_item['owner_data3'] = owner_parts[2]
                        dict_item['owner_data5'] = owner_parts[3]
                        
                        # Удаление исходного ключа 'CURRENT OWNER'
                        del dict_item['CURRENT OWNER']

 

                # Выводим обновленный список словарей
                
                            
                            # print(f"{header_first}: {value_first}")
                
                
            

                headers_second = table[2]  # Заголовки таблицы
                
                search_headers_second = ["TRANSFER HISTORY", "DOS", "T", "SALE PRICE", "BK-PG (Cert)"]
                for header_second in search_headers_second:
                    if header_second in headers_second:
                        index = headers_second.index(header_second)  # Получаем индекс нужной колонки
                        # Проходим по всем строкам, начиная со второй
                        for row in table[3:4]:
                            value_second = row[index].split('\n')[0]
                            dict_search_key_info_02[header_second] = value_second
                values_list_search_key_info.append(dict_search_key_info_02)
                            
                
                

                headers_third = table[7]
                search_headers = ["TOTAL", "ONING"]

                for search_header in search_headers:
                    if search_header in headers_third:
                        header_index = headers_third.index(search_header)  # Находим индекс заголовка
                        target_index = header_index + 3  # Предполагается, что целевая ячейка через две клетки от заголовка
                        
                        for row in table[7:8]:  # Обрабатывается только одна строка
                            if target_index < len(row):  # Убедимся, что индекс в пределах строки
                                target_value = row[target_index].replace('Z', '').strip()
                                dict_search_key_info_03[search_header] = target_value  # Используем search_header как ключ
                        
                values_list_search_key_info.append(dict_search_key_info_03)


                
                
                """Переименовать"""
                keys_mapping = {
                                    'PARCEL ID': 'parcel_id',
                                    'LOCATION': 'location',
                                    'CLASS': 'class',
                                    'DESCRIPTION': 'description',
                                    'CARD': 'card_info',
                                    'BN': 'card',
                                    'TRANSFER HISTORY':'transfer_history',
                                    'DOS':'dos',
                                    'SALE PRICE':'sale_price',
                                    'BK-PG (Cert)':'bk_pg_cert',
                                    'TOTAL':'acres',
                                    'ONING':'zoming'

                                }

                # Итерация по списку словарей
                for item in values_list_search_key_info:
                    for old_key, new_key in keys_mapping.items():
                        if old_key in item:
                            item[new_key] = item.pop(old_key)  # Удаление старого ключа и добавление нового с сохранением значения         

                # print(values_list_search_key_info)              
                


                                # print(f"{search_header} {target_value}")
                
                
                
                
                
                
   
               
                
                headers_cell_8 = table[8][27]  # Заголовки в 27-й ячейке
                values_cell_8 = table[8][31]  # Значения в 31-й ячейке
                headers_8 = split_and_clean(headers_cell_8)
                values_8 = split_and_clean(values_cell_8)

                # Обработка данных из таблицы 9
                total_value_9 = table[9][31]  # Общая сумма в 32-й ячейке

                # Сопоставляем заголовки и значения
                for header, value in zip(headers_8, values_8):
                    print(f"{header}: {value}")

                # Выводим общую сумму
                print(f"TOTAL: {total_value_9}")

                
                
                
                
                
                """search_key_building"""
                headers_cell_14 = table[14][0]  # Заголовки в 27-й ячейке
                values_cell_14 = table[14][4]  # Значения в 31-й ячейке
                values_cell_02_14 = table[14][8]  # Значения в 31-й ячейке
                headers_14 = split_and_clean(headers_cell_14)
                values_14 = split_and_clean(values_cell_14)
                values_02_14 = split_and_clean(values_cell_02_14)


                # Сопоставляем заголовки и значения
                for header, value, value_02 in zip(headers_14, values_14, values_02_14):
                    dict_search_key_building = {
                        "Keyno": key_number,
                        "card": page_index,
                        "el_type": header,
                        "el_code": value,
                        "el_desc": value_02
                    }
                    values_list_search_key_building.append(dict_search_key_building)

                with open(f'search_key_buildin_{page_index}.json', 'w', encoding='utf-8') as f:
                    json.dump(values_list_search_key_building, f, ensure_ascii=False, indent=4)

                




                
                
                # headers_cell_15 = table[15][0]  # Заголовки в 27-й ячейке
                # values_cell_15 = table[15][5]  # Значения в 31-й ячейке
                # headers_15 = split_and_clean(headers_cell_15)
                # values_15 = split_and_clean(values_cell_15)

                # # Обработка данных из таблицы 9

                # for header, value in zip(headers_15, values_15):
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
                for header, value, value_02 in zip(headers_16, values_16, values_02_16):
                    
                    current_dict_search_key_element = {
                        "Keyno": key_number,
                        "card": page_index,
                        "el_type": header,
                        "el_code": value,
                        "el_desc": value_02,
                    }
                    values_list_search_key_element.append(current_dict_search_key_element)

                with open(f'search_key_element_{page_index}.json', 'w', encoding='utf-8') as f:
                    json.dump(values_list_search_key_element, f, ensure_ascii=False, indent=4)  # Записываем в файл
                
                
                
                
                
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
                    header_str = '' if header is None else header.replace('None', '')

                    current_dict_search_key_bat = {
                        "Keyno": key_number,
                        "card": page_index,
                        "bat": f"{header_str} {value}",
                        "bat_t": value_02,
                        "bat_desc": value_03,
                        "bat_units": value_04.replace(",", ""),  # Убираем запятые в 'bat_units'
                    }
                    values_list_search_key_bat.append(current_dict_search_key_bat)
                
                with open(f'search_key_bat_{page_index}.json', 'w', encoding='utf-8') as f:
                    json.dump(values_list_search_key_bat, f, ensure_ascii=False, indent=4)  # Записываем в файл
            

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
                        "cap_units": value
                    }
                    values_list_search_key_capacity.append(current_dict_search_key_capacity)
                with open(f'search_key_capacity_{page_index}.json', 'w', encoding='utf-8') as f:
                    json.dump(values_list_search_key_capacity, f, ensure_ascii=False, indent=4)  # Записываем в файл



                

if __name__ == "__main__":

    pars_pdf()
