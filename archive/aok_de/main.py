# from selenium import webdriver
import csv
import glob
import json
import os
import re
import sqlite3
import time

import requests
import undetected_chromedriver as webdriver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
bd_path = os.path.join(temp_path, 'bd')
list_path = os.path.join(temp_path, 'list')
product_path = os.path.join(temp_path, 'product')

headers = {
    'authority': 'navigatoren-api.aok.de',
    'accept': 'application/json',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'dnt': '1',
    'origin': 'https://www.aok.de',
    'referer': 'https://www.aok.de/',
    'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
}


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()

    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    # chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions') # Отключает использование расширений
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        'source': '''
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
      '''
    })
    return driver


def create_sqlite_table_ind_reg():
    filename = os.path.join(bd_path, 'aok.db')
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    # Создайте таблицу, если она не существует
    cursor.execute(
        'CREATE TABLE ind_reg ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'total_count INT,'
        'index_region VARCHAR(50)'
        ')'

    )

    # Закройте соединение
    conn.close()


def create_sqlite_table_contact_aok():
    filename = os.path.join(bd_path, 'aok.db')
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    # Создайте таблицу, если она не существует, с уникальным id_company
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS contact_aok ('
        'id INTEGER PRIMARY KEY AUTOINCREMENT,'
        'id_company INT UNIQUE,'
        'name_company VARCHAR(200),'
        'email_company VARCHAR(200),'
        'www_company VARCHAR(200)'
        ')'
    )

    # Закройте соединение
    conn.close()
def add_columns_to_table():
    filename = os.path.join(bd_path, 'aok.db')
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    # Добавляем новые колонки в таблицу
    columns_to_add = [
        'street VARCHAR(200)',
        'streetAddition VARCHAR(200)',
        'zip VARCHAR(200)',
        'city VARCHAR(200)',
        'phone VARCHAR(200)',
        'title VARCHAR(200)',
        'fax VARCHAR(200)'
    ]

    for column in columns_to_add:
        try:
            cursor.execute(f'ALTER TABLE contact_aok ADD COLUMN {column}')
            print(f"Колонка '{column}' успешно добавлена.")
        except sqlite3.OperationalError as e:
            print(f"Ошибка при добавлении колонки '{column}': {e}")

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

# Вызываем функцию
add_columns_to_table()

def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, list_path, product_path, bd_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [list_path, product_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
        # print(f'Очистил папку {os.path.basename(folder)}')


def get_csv_productid():
    csv_filename = 'index.csv'
    productid_list = []

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        for row in reader:
            productid_list.append(row)
    return productid_list


def get_total_company():
    filename = os.path.join(bd_path, 'aok.db')
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    locations = get_csv_productid()
    data_to_insert = []  # Ваши данные
    for location in locations:
        params = {
            'sorting': 'distance',
            'location': location[0],
            'radius': '10000',
            'pe_ang_krankenpflege': '002',
            'size': '10',
        }

        response = requests.get('https://navigatoren-api.aok.de/api/v1/careservices/', params=params, headers=headers)
        try:
            json_data = response.json()
        except:
            print(location[0])
            continue
        count = json_data['count']
        data_to_insert.append([count, location[0]])
        time.sleep(1)
    cursor.executemany('INSERT INTO ind_reg (total_count, index_region) VALUES (?, ?)', data_to_insert)

    conn.commit()
    conn.close()


def get_bd():
    filename = os.path.join(bd_path, 'aok.db')
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ind_reg')
    data_to_insert = cursor.fetchall()
    conn.commit()
    conn.close()
    return data_to_insert


def get_parsing():
    # filename = os.path.join(bd_path, 'aok.db')
    # conn = sqlite3.connect(filename)
    # cursor = conn.cursor()
    datas = get_bd()
    for item in datas[1:]:
        count = item[1]
        index = item[2]
        total_pages = (count // 10) + 2
        values_in_bd = []
        from_data = 0
        for i in range(1, total_pages):
            file_json = os.path.join(list_path, f'{index}_{i}.json')
            if not os.path.exists(file_json):
                if i == 1:
                    time.sleep(1)
                    params = {
                        'sorting': 'distance',
                        'location': index,
                        'radius': '10000',
                        'pe_ang_krankenpflege': '002',
                        'size': '10',
                    }

                    response = requests.get('https://navigatoren-api.aok.de/api/v1/careservices/', params=params,
                                            headers=headers)
                    try:
                        json_data = response.json()
                        with open(file_json, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

                        # results_json_data = json_data['results']
                    except:
                        print(index)
                        continue
                    # for r in results_json_data:
                    #     id_company = r.get('id', None)
                    #     name_company = r.get('locationName', None)
                    #     email_company = r.get('email', None)
                    #     www_company = r.get('website', None)
                    #     # value_0 = [id_company, name_company, email_company, www_company]
                    #     cursor.execute(
                    #         'INSERT OR REPLACE INTO contact_aok (id_company, name_company, email_company, www_company) VALUES (?,?,?,?)',
                    #         (id_company, name_company, email_company, www_company))
                    #     # values_in_bd.append(value_0)

                elif i > 1:
                    time.sleep(1)
                    from_data += 10
                    params = {
                        'sorting': 'distance',
                        'location': index,
                        'radius': '10000',
                        'pe_ang_krankenpflege': '002',
                        'from': from_data,
                        'size': '10',
                    }
                    response = requests.get('https://navigatoren-api.aok.de/api/v1/careservices/', params=params,
                                            headers=headers)
                    try:
                        json_data = response.json()
                        with open(file_json, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

                        # results_json_data = json_data['results']
                    except:
                        print(index)
                        continue
    #             for r in results_json_data:
    #                 id_company = r.get('id', None)
    #                 name_company = r.get('locationName', None)
    #                 email_company = r.get('email', None)
    #                 www_company = r.get('website', None)
    #                 value_1 = [id_company, name_company, email_company, www_company]
    #                 cursor.execute(
    #                     'INSERT OR REPLACE INTO contact_aok (id_company, name_company, email_company, www_company) VALUES (?,?,?,?)',
    #                     (id_company, name_company, email_company, www_company))
    #                 values_in_bd.append(value_1)
    #         time.sleep(1)
    #         print(f'{index}_{i}_из_{total_pages}')
    #     # cursor.executemany('INSERT OR REPLACE INTO contact_aok (id_company, name_company, email_company, www_company) VALUES (?,?,?,?)', values_in_bd)
    #     # print(values_in_bd)
    #     # cursor.executemany('INSERT INTO contact_aok (id_company, name_company, email_company, www_company) VALUES (?,?,?,?)',values_in_bd)
    #
    # conn.commit()
    # conn.close()


def pars():
    filename = os.path.join(bd_path, 'aok.db')
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    folder = os.path.join(list_path, '*.json')
    files_html = glob.glob(folder)

    for item in files_html:
        with open(item, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        results_json_data = json_data['results']
        for r in results_json_data:
            id_company = r.get('id', None)
            name_company = r.get('locationName', None)
            email_company = r.get('email', None)
            www_company = r.get('website', None)
            street = r.get('address', {}).get('street', None)
            streetAddition = r.get('address', {}).get('streetAddition', None)
            zip_code = r.get('address', {}).get('zip', None)
            city = r.get('address', {}).get('city', None)
            title = r.get('address', {}).get('title', None)
            phone = r.get('phone', None)
            fax = r.get('fax', None)

            # Проверка, существует ли запись с таким id_company
            cursor.execute('SELECT id FROM contact_aok WHERE id_company = ?', (id_company,))
            data = cursor.fetchone()
            if data is None:
                # Если записи нет, выполняем вставку
                cursor.execute(
                    'INSERT INTO contact_aok (id_company, name_company, email_company, www_company, street, streetAddition, zip, city, phone, title, fax) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    (id_company, name_company, email_company, www_company, street, streetAddition, zip_code, city, phone, title, fax))
            else:
                # Если запись есть, выполняем обновление
                cursor.execute(
                    'UPDATE contact_aok SET name_company=?, www_company=?, street=?, streetAddition=?, zip=?, city=?, phone=?, title=?, fax=? WHERE id_company=?',
                    (name_company,  www_company, street, streetAddition, zip_code, city, phone, title, fax, id_company))

    conn.commit()
    conn.close()



def get_selenium():
    csv_data = get_csv_sel()
    driver = get_chromedriver()
    driver.get('https://www.google.com/')
    time.sleep(1)
    mail = 'mail'
    for i in csv_data[2:]:
        safe_i = re.sub(r'[^a-zA-Z0-9]', '_', i)
        file_html = os.path.join(product_path, f'{safe_i}.html')
        if not os.path.exists(file_html):
            element_to_click = driver.find_element(By.XPATH, '//textarea[@type="search"]')
            element_to_click.clear()
            element_to_click.send_keys(f'{i} {mail}')
            element_to_click.send_keys(Keys.RETURN)
            # Получение исходного кода страницы
            html = driver.page_source
            time.sleep(2)
            # Сохранение HTML-кода страницы в файл
            with open(file_html, "w", encoding='utf-8') as file:
                file.write(driver.page_source)

    driver.quit()
    unique_emails = set()
    with open("saved_page.html", "r", encoding='utf-8') as file:
        content = file.read()
        found_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        for email in found_emails:
            if is_valid_email(email):
                unique_emails.add(email)

    print(unique_emails)


def is_valid_email(email):
    # Исключаем строки, похожие на расширения файлов
    if re.search(r'\.[a-zA-Z]{2,4}\.[a-zA-Z]{2,4}$', email):
        return False

    # Расширенное регулярное выражение для проверки валидности email
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return pattern.match(email)


def get_csv_sel():
    csv_filename = 'sel.csv'
    productid_list = []

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')

        for row in reader:
            productid_list.append(row[1])
    return productid_list


def upload_to_csv():
    # Подключаемся к базе данных SQLite
    filename = os.path.join(bd_path, 'aok.db')
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()

    # Открываем CSV-файл для чтения
    with open('to_bd.csv', 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')

        for row in csv_reader:
            id_company, email_company = row

            # Обновляем email_company для каждого id_company
            cursor.execute("UPDATE contact_aok SET email_company = ? WHERE id_company = ?", (email_company, id_company))

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

if __name__ == '__main__':
    # create_sqlite_table_ind_reg()
    # create_sqlite_table_contact_aok()
    # add_columns_to_table()
    # delete_old_data()
    # get_total_company()
    # get_bd()
    # get_parsing()

    pars()
    # get_csv_sel()
    # get_selenium()
    # upload_to_csv()
