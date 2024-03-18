from bs4 import BeautifulSoup
import csv
import urllib.parse
import glob
import re
import requests
import json
import os
import time
from config import db_config, use_bd, use_table
import mysql.connector

cookies = {
    'PHPSESSID_MIKE': 't73notsemv17bsdniokuocsqh1',
    'ActiveBasket': '1',
    'dv_consent': '{"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1704032486}',
}

headers = {
    'authority': 'mike.larsson.pl',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'PHPSESSID_MIKE=t73notsemv17bsdniokuocsqh1; ActiveBasket=1; dv_consent={"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1704032486}',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://www.larsson.pl/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-site',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')
img_path = os.path.join(temp_path, 'img')


def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, list_path, product_path, img_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [list_path, product_path, img_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)


def get_requests():
    # cookies = {
    #     'PHPSESSID_MIKE': '6uu4pm3a3kgnt5113onr2sk8no',
    #     'ActiveBasket': '1',
    #     'dv_consent': '{"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1701527319}',
    # }
    #
    # headers = {
    #     'authority': 'mike.larsson.pl',
    #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    #     'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    #     'cache-control': 'no-cache',
    #     # 'cookie': 'PHPSESSID_MIKE=6uu4pm3a3kgnt5113onr2sk8no; ActiveBasket=1; dv_consent={"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1701527319}',
    #     'dnt': '1',
    #     'pragma': 'no-cache',
    #     'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    #     'sec-ch-ua-mobile': '?0',
    #     'sec-ch-ua-platform': '"Windows"',
    #     'sec-fetch-dest': 'document',
    #     'sec-fetch-mode': 'navigate',
    #     'sec-fetch-site': 'none',
    #     'sec-fetch-user': '?1',
    #     'upgrade-insecure-requests': '1',
    #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # }
    #
    #
    #
    # response = requests.get(
    #     'https://mike.larsson.pl/pl/category/10300000000/vehicle/adiva-namura-50:62447/',
    #     cookies=cookies,
    #     headers=headers,
    # )
    # json_data = response.json()
    # with open(f'Hannover.json', 'w', encoding='utf-8') as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    # src = response.text
    filename = f"larsson.html"
    # with open(filename, "w", encoding='utf-8') as file:
    #     file.write(src)
    with open(filename, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    table_category = soup.find('div', attrs={'id': 'cat-con'})
    regex_cart = re.compile('cat-item.*')
    cart_table = table_category.find_all('div', attrs={'class': regex_cart})
    urls_category = [u.find('a').get('href') for u in cart_table]
    # for url in urls_category:
    kodu_tovary = soup.find_all('div', attrs={'class': 'gal_artnr'})
    kod_category = [k.get_text(strip=True).replace("Nr kat.: ", "").replace(".", "") for k in kodu_tovary]
    print(kod_category)


def filter_classes(tag):
    return tag and tag.name == 'tr' and tag.has_attr('class') and ('tda' in tag['class'] or 'tdb' in tag['class'])


def parsing():
    filename = os.path.join(list_path, '*.html')
    files_html = glob.glob(filename)
    for item in files_html:
        file_name_csv = item.split('\\')[-1].replace('.html', '.csv')
        with open(item, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        table = soup.find('table')

        if table:
            row_all = table.select('tr.tda, tr.tdb')

            all_specifications_table = []
            all_specifications_history = []
            for row_td in row_all:

                url_row = row_td.find('a').get('href').split(':')
                url_write = row_td.find('a').get('href')
                cod_tovara = url_row[-1].split('?')[0]

                key_table = (
                    'Model', 'Kod roku', 'Typ', 'VIN_od', 'VIN_do', 'Rocznik', 'Il. cyl.', 'Moc silnika',
                    'Kod produktu',
                    'url_zapasowa')

                values_table = [a.find('a').get_text(strip=True) for a in row_td]

                # Добавляем cod_tovara в конец списка values_table
                values_table.append(cod_tovara)
                values_table.append(url_write)

                specifications_table = dict(zip(key_table, values_table))
                all_specifications_table.append(specifications_table)

                history = row_td.find('td', attrs={'class': 'show_history_tips'})
                table = history.find('table')
                rows_tr = table.find_all('tr')

                specifications_history = {}
                for row in rows_tr:
                    tds = row.find_all('td')
                    if len(tds) == 2:
                        key = tds[0].get_text(strip=True)
                        value = tds[1].get_text(strip=True)
                        specifications_history[key] = value

                all_specifications_history.append(specifications_history)

        # Объединяем данные из обоих списков
        combined_data = []
        for table, history in zip(all_specifications_table, all_specifications_history):
            combined_dict = {**table, **history}  # Объединяем два словаря
            combined_data.append(combined_dict)

        # Определяем заголовки для CSV
        # Возьмем ключи из первого элемента списка (предполагая, что все элементы имеют одинаковые ключи)
        headers = combined_data[0].keys() if combined_data else []
        # Запись данных в CSV
        with open(file_name_csv, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers, delimiter=";")

            # Записываем заголовки
            writer.writeheader()

            # Записываем строки данных
            for data in combined_data:
                writer.writerow(data)

        print(f"Данные записаны в файл {file_name_csv}")


def get_all_brand():
    cookies = {
        'ActiveBasket': '1',
        'dv_consent': '{"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1701526738}',
        'PHPSESSID_MIKE': '0l3vv3p66d8feiupnlbj1i8tef',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }
    # urls = [
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Adly%C3%BEHerchee/?ftype=1&type=99&Marke=Adly/Herchee&vsr=all',
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Arctic+Cat%C3%BETextron/?ftype=1&type=99&Marke=Arctic%20Cat/Textron&vsr=all',
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Atala%C3%BERizzato/?ftype=1&type=99&Marke=Atala/Rizzato&vsr=all',
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Buffalo%C3%BEQuelle/?ftype=1&type=99&Marke=Buffalo/Quelle&vsr=all',
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Cectek%C3%BEHerkules/?ftype=1&type=99&Marke=Cectek/Herkules&vsr=all',
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Huatian%C3%BELintex/?ftype=1&type=99&Marke=Huatian/Lintex&vsr=all',
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/MZ%C3%BEMUZ/?ftype=1&type=99&Marke=MZ/MUZ&vsr=all',
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/Quickfoot%C3%BEOpen+Concepts/',
    #     'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/SMC%C3%BEBarossa/?ftype=1&type=99&Marke=SMC/Barossa&vsr=all'
    # ]
    # cookies = {
    # 'ActiveBasket': '1',
    # 'dv_consent': '{"accepted":[{"uid":"1"},{"uid":"6"}],"ts":1701526738}',
    # 'PHPSESSID_MIKE': '0l3vv3p66d8feiupnlbj1i8tef',
    # }
    #
    # headers = {
    #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    #     'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    # }
    # coun = 0
    # for u in urls:
    #     response = requests.get(u, cookies=cookies, headers=headers)
    #     src_res = response.text
    #     soup_res = BeautifulSoup(src_res, 'lxml')
    #     # Поиск тега title
    #     title_tag = soup_res.find('title')
    #     coun += 1
    #     # Проверка содержимого тега title и его вывод
    #     if title_tag and title_tag.get_text() == "404 Not Found":
    #         print(u)
    #     else:
    #         with open(f'{coun}.html', "w", encoding='utf-8') as file:
    #             file.write(src_res)
    #         time.sleep(5)
    #
    #         print(f'Сохранил {u}, пауза 10сек')

    url_template = 'https://mike.larsson.pl/pl/faction/select_vehicle/ftype/1/type/99/Marke/{}/?ftype=1&type=99&Marke={}&vsr=all'
    with open('url_not_found.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        with open("larsson.html", encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        all_brand_tag = soup.find('select', attrs={'id': 'Marke'})
        for a in all_brand_tag:
            br = a.get_text(strip=True)
            if not br:
                continue
            brfile = f"{br.replace('//', '_').replace('-', '_').replace(' ', '_')}.html"
            filename = os.path.join(list_path, brfile)
            if not os.path.exists(filename):
                part1 = urllib.parse.quote_plus(br)
                part2 = urllib.parse.quote(br, safe='')
                new_url = url_template.format(part1, part2)
                response = requests.get(new_url, cookies=cookies, headers=headers)
                src_res = response.text
                soup_res = BeautifulSoup(src_res, 'lxml')
                # Поиск тега title
                title_tag = soup_res.find('title')

                # Проверка содержимого тега title и его вывод
                if title_tag and title_tag.get_text() == "404 Not Found":
                    writer.writerow([new_url])
                    # print(new_url)
                else:
                    with open(filename, "w", encoding='utf-8') as file:
                        file.write(src_res)
                    time.sleep(10)
                    print(f'Сохранил {br}, пауза 10сек')


def create_sql():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # 2. Создаем базу данных с именем kupypai_com
    # cursor.execute("CREATE DATABASE vpromo2_usa")

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    # 3. В базе данных создаем таблицу ad
    # 4. Создаем необходимые колонки
    #     cursor.execute(f"""
    #     CREATE TABLE {use_table} (
    #                 id INT AUTO_INCREMENT PRIMARY KEY,
    #                 Model VARCHAR(255),
    #                 Kod_roku VARCHAR(255),
    #                 Typ VARCHAR(255),
    #                 VIN_od VARCHAR(255),
    #                 VIN_do VARCHAR(255),
    #                 Rocznik VARCHAR(255),
    #                 Il_cyl VARCHAR(255),
    #                 Moc_silnika VARCHAR(255),
    #                 Kod_produktu VARCHAR(255),
    #                 Url_zapasowa VARCHAR(255),
    #                 Producent VARCHAR(255),
    #                 Nazwa_opis VARCHAR(255),
    #                 Pojemność VARCHAR(255),
    #                 Nazwa_2 VARCHAR(255),
    #                 Nazwa_handlowa VARCHAR(255),
    #                 Moc VARCHAR(255),
    #                 Początkowy_nr_VIN VARCHAR(255),
    #                 Końcowy_nr_VIN VARCHAR(255)
    # )
    #     """)
    """Добавить колонку в текущую БД"""
    cursor.execute(f"""
        ALTER TABLE {use_table}
        ADD COLUMN Kod_części_zamiennej TEXT
    """)
    # Закрываем соединение
    cnx.close()


def get_csv():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()
    cursor.execute(f"USE {use_bd}")
    # Создаем пустой список для хранения данных из колонок 2, 3 и 4
    filename = os.path.join(product_path, '*.csv')
    files_html = glob.glob(filename)
    for item in files_html:
        selected_columns_data = []

        # Открываем файл data.csv с разделителем ;
        with open(item, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            # Пропускаем заголовок
            next(reader)
            # Проходим по каждой строке в файле
            for row in reader:
                # Проверяем, что строка имеет как минимум 4 столбца
                # Извлекаем данные из колонок 2, 3 и 4 (индексы 1, 2 и 3)
                Model = row[0]
                Kod_roku = row[1]
                Typ = row[2]
                VIN_od = row[3]
                VIN_do = row[4]
                Rocznik = row[5]
                Il_cyl = row[6]
                Moc_silnika = row[7]
                Kod_produktu = row[8]
                Url_zapasowa = row[9]
                Producent = row[10]
                Nazwa_opis = row[11]
                Pojemność = row[12]
                Nazwa_2 = row[13]
                Nazwa_handlowa = row[14]
                Moc = row[15]
                Początkowy_nr_VIN = row[16]
                Końcowy_nr_VIN = row[17]

                # Создаем кортеж с данными из этих колонок и добавляем его в список
                selected_columns_data.append(
                    (Model, Kod_roku, Typ, VIN_od, VIN_do, Rocznik, Il_cyl, Moc_silnika, Kod_produktu, Url_zapasowa,
                     Producent, Nazwa_opis, Pojemność, Nazwa_2, Nazwa_handlowa, Moc, Początkowy_nr_VIN, Końcowy_nr_VIN))

        insert_query = (
            f"INSERT INTO {use_table} (Model,Kod_roku,Typ,VIN_od,VIN_do,Rocznik,Il_cyl,Moc_silnika,Kod_produktu,Url_zapasowa,Producent,Nazwa_opis,Pojemność,Nazwa_2,Nazwa_handlowa,Moc,Początkowy_nr_VIN,Końcowy_nr_VIN)"
            f"VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")

        # Вставка данных из selected_columns_data
        cursor.executemany(insert_query, selected_columns_data)

    # Сохранение изменений и закрытие соединения
    cnx.commit()
    cursor.close()
    cnx.close()
    # return selected_columns_data


def get_kod_category():
    try:
        cnx = mysql.connector.connect(**db_config)
        cursor = cnx.cursor()
        cursor.execute(
            "SELECT Url_zapasowa, Kod_części_zamiennej, id FROM larsson WHERE Kod_części_zamiennej IS NULL OR Kod_części_zamiennej = '';")
        data_dict = {}
        id_url_map = {}
        for row in cursor:
            data_dict[row[0]] = row[1]  # row[0] это Url_zapasowa, row[1] это Kod_części_zamiennej
            id_url_map[row[0]] = row[2]  # row[2] это id

        url_zapasowa_list = [url for url in data_dict.keys()]
        """Перебираем ссылки"""
        for u in url_zapasowa_list:

            response = requests.get(u, cookies=cookies, headers=headers)
            src = response.text
            soup = BeautifulSoup(src, 'lxml')
            table_category = soup.find('div', attrs={'id': 'cat-con'})
            regex_cart = re.compile('cat-item.*')
            try:
                cart_table = table_category.find_all('div', attrs={'class': regex_cart})
            except:
                print(f'Ошибка, возможно не работают КуКи')
                continue
            urls_category = [u.find('a').get('href') for u in cart_table]
            all_kod = []
            """Перебираем категории в ссылках"""
            for url in urls_category:
                response = requests.get(url, cookies=cookies, headers=headers)
                src_c = response.text
                soup = BeautifulSoup(src_c, 'lxml')
                try:
                    table_cods = soup.find('div', attrs={'class': 'gallery'}).find_all('div', attrs={
                        'class': 'gal_elem kombi'})
                except:
                    continue

                # kodu_tovary = table_cods.find('div', attrs={'class': 'gal_artnr'})
                for k in table_cods:
                    kod_text = k.find('div', attrs={'class': 'gal_artnr'}).get_text(strip=True)
                    # Использование регулярного выражения для извлечения номера каталога
                    match = re.search(r'Nr kat\.: ([\d.]+)', kod_text)
                    if match:
                        # Удаляем точки из найденного номера и добавляем в список
                        kod_number = match.group(1).replace('.', '')
                        all_kod.append(kod_number)
                        print(kod_number)
                # time.sleep(1)
            kod_string = ', '.join(all_kod)
            record_id = id_url_map[u]
            update_query = "UPDATE larsson SET Kod_części_zamiennej = %s WHERE id = %s"
            cursor.execute(update_query, (kod_string, record_id))
            cnx.commit()
    except mysql.connector.Error as err:
        print("Ошибка базы данных:", err)
    except requests.RequestException as e:
        print("Ошибка HTTP запроса:", e)
    finally:
        if cnx.is_connected():
            cnx.close()
            print('Все получилось')


if __name__ == '__main__':
    # delete_old_data()
    # get_requests()
    # get_cloudscraper()
    # get_selenium()
    # parsing()
    # get_all_brand()
    # create_sql()
    # get_csv()
    get_kod_category()
