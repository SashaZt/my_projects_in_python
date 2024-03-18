import mysql.connector
import csv
import re

# Установить соединение с базой данных
db = mysql.connector.connect(
    host="localhost",
    user="python_mysql",
    password="python_mysql",
    database="intercars"
)

# Создать объект курсора для выполнения запросов к базе данных
cursor = db.cursor()

# Выполнить запрос для первой таблицы
cursor.execute("""
SELECT id, sku, brand, name FROM ax_product;
""")
products_results = cursor.fetchall()

# # Выполнить запрос для второй таблицы
# cursor.execute("""
# SELECT brand1, brand2 FROM intercars.ax_synonym;
# """)
# synonym_results = cursor.fetchall()

# Закрыть соединение с базой данных
db.close()

# Создание словаря для хранения синонимов брендов
# synonym_dict = {row[0]: row[1] for row in synonym_results}

# # Сортировка по полю brand
# products_results = sorted(products_results, key=lambda x: x[2])

# Запись результатов запросов в CSV файл
csv_file_path = 'out.csv'  # Путь к файлу, измените на нужный
with open(csv_file_path, mode='w', newline='', encoding="utf-8") as file:
    writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, delimiter=';')

    # Записываем заголовки
    writer.writerow(["ID", "SKU", "Brand", "name"])

    # Объединяем данные из двух таблиц и записываем в CSV
    for row in products_results:
        product_id, sku, brand, name = row

        # Проверяем, начинается ли бренд с английских или русских букв и не содержит символ "/"
        if re.match(r'^[A-Za-z]', sku):
            # synonym_brand = synonym_dict.get(brand, '')  # Получаем синоним из словаря
            writer.writerow([product_id, sku, brand, name])

# import mysql.connector
#
# # Установить соединение с базой данных
# db = mysql.connector.connect(
#     host="localhost",
#     user="python_mysql",
#     password="python_mysql",
#     database="intercars"
# )
#
# # Создать объект курсора для выполнения запросов к базе данных
# cursor = db.cursor()
#
# # Список значений sku для удаления
# sku_to_delete = [
#     "НИЗ"
# ]
#
# # Создаем строку для условия WHERE
# condition = "brand IN ('" + "','".join(sku_to_delete) + "')"
#
# # Выполняем DELETE запрос
# delete_query = f"DELETE FROM intercars.ax_product WHERE {condition};"
# cursor.execute(delete_query)
#
# # Фиксируем изменения и закрываем соединение
# db.commit()
# db.close()

#
#
# import mysql.connector
# import csv
# import re
#
# # Установить соединение с базой данных
# db = mysql.connector.connect(
#     host="localhost",
#     user="python_mysql",
#     password="python_mysql",
#     database="intercars"
# )
#
# # Создать объект курсора для выполнения запросов к базе данных
# cursor = db.cursor()
#
# # Выполнить запрос для получения уникальных брендов
# cursor.execute("""
# SELECT DISTINCT brand FROM ax_product;
# """)
# brands = cursor.fetchall()
#
# # Закрыть соединение с базой данных
# db.close()
#
# # Запись уникальных брендов в CSV файл
# brands_all = []
# csv_file_path = 'unique_brands.csv'  # Путь к файлу, измените на нужный
# with open(csv_file_path, mode='w', newline='', encoding="utf-8") as file:
#     writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, delimiter=';')
#
#     # Записываем заголовок
#     # writer.writerow(["Brand"])
#
#     # Записываем уникальные бренды
#     for brand in brands:
#         if re.match(r'^[A-Za-zА-Яа-я]', brand[0]) and "/" not in brand[0]:
#             brands_all.append(brand[0])
#             writer.writerow([brand[0]])
#
# # for values in brands_all:
# #     print(values)
#
#
# import os
# import re
#
# # Указываем путь до папки
# folder_path = "c:/intercars_html/"
#
# # Создаем множество для хранения уникальных значений
# unique_values = set()
#
# # Проходим по всем файлам в папке
# for filename in os.listdir(folder_path):
#     if os.path.isfile(os.path.join(folder_path, filename)):
#         # Используем регулярное выражение для поиска нужного значения в имени файла
#         match = re.search(r'_(\w+).html', filename)
#         if match:  # Если найдено совпадение
#             unique_value = match.group(1)  # Извлекаем значение
#             unique_values.add(unique_value)  # Добавляем в множество
#
# for value in unique_values:
#     print(value)
#
# brands_all_set = set(brands_all)
#
# # Находим различия
# unique_only =  unique_values - brands_all_set
# csv_file_path = 'unique_only.csv'  # Путь к файлу, измените на нужный
# with open(csv_file_path, mode='w', newline='', encoding="utf-8") as file:
#     writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, delimiter=';')
#
#     for value in unique_only:
#         writer.writerow([value])
