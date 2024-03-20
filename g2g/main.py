import csv
import glob
import json
import math
import os
import re
import time
import sys
from urllib.parse import urlparse, parse_qs
import pandas as pd
import requests
from browsermobproxy import Server
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

"""Для прокси нужно jre-8u371-windows-x64.exe т.е. java 8 версии"""
server_options = {"log_path": "browsermob-proxy.log"}

server = Server(
    r"C:\Program Files (x86)\browsermob-proxy\bin\browsermob-proxy",
    options=server_options,
)
server.start()
proxy = server.create_proxy()


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    )
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument(
        "--auto-open-devtools-for-tabs=devtools://devtools/bundled/inspector.html"
    )
    # Определение пути к chromedriver.exe
    if getattr(sys, 'frozen', False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
    
    # Путь к chromedriver.exe
    chromedriver_path = os.path.join(application_path, "chromedriver.exe")
    service = webdriver.ChromeService(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def selenium_get_curl(url, type_pars):
    proxy.new_har(
        "sls.g2g.com", options={"captureHeaders": True, "captureContent": True}
    )
    """Ссылка куда переходим"""
    driver = get_chromedriver()
    driver.get(url)
    time.sleep(10)

    driver.execute_script(
        """
        var elements = document.querySelectorAll('[aria-label="Network panel"]');
        for (var i = 0; i < elements.length; i++) {
            var element = elements[i];
            if (element.offsetWidth > 0 && element.offsetHeight > 0) {
                element.click();
                break;
            }
        }
    """
    )
    time.sleep(5)
    # получить все запросы из Network panel
    requests = driver.execute_script(
        """
        var performanceEntries = performance.getEntriesByType("resource");
        var fetchRequests = [];
        for (var i = 0; i < performanceEntries.length; i++) {
            var entry = performanceEntries[i];
            fetchRequests.push(entry);
        }
        return fetchRequests;
    """
    )

    counets_url = driver.find_element(
        By.XPATH, '//div[@class="text-secondary"]'
    ).text.replace(",", "")
    count_url = int(re.search(r"(\d+)", counets_url).group(0))
    url_in_page = 48
    list_url = math.ceil(count_url / url_in_page)

    curl_command = "curl "
    entries = proxy.har["log"]["entries"]
    if type_pars == 1:
        for entry in entries:
            # print(entry)
            """Указываем тут url который нужно отслеживать"""
            if entry["request"]["url"].startswith(
                "https://sls.g2g.com/offer/search?service_id="
            ):
                # Method (GET, POST, etc.)
                curl_command += "-X {} ".format(entry["request"]["method"])

                # URL
                curl_command += "'{}' \\\n".format(entry["request"]["url"])

                # Headers
                for header in entry["request"]["headers"]:
                    header_name = header["name"]
                    header_value = header["value"]
                    curl_command += "  -H '{}: {}' \\\n".format(
                        header_name, header_value
                    )

                if (
                    entry["request"]["method"] == "POST"
                    and "postData" in entry["request"]
                ):
                    if "text" in entry["request"]["postData"]:
                        curl_command += "  --data '{}'".format(
                            entry["request"]["postData"]["text"]
                        )

                break

    elif type_pars == 0:
        for entry in entries:
            # print(entry)
            """Указываем тут url который нужно отслеживать"""
            if entry["request"]["url"].startswith("https://www.g2g.com/categories/"):
                # Method (GET, POST, etc.)
                curl_command += "-X {} ".format(entry["request"]["method"])

                # URL
                curl_command += "'{}' \\\n".format(entry["request"]["url"])

                # Headers
                for header in entry["request"]["headers"]:
                    header_name = header["name"]
                    header_value = header["value"]
                    curl_command += "  -H '{}: {}' \\\n".format(
                        header_name, header_value
                    )

                if (
                    entry["request"]["method"] == "POST"
                    and "postData" in entry["request"]
                ):
                    if "text" in entry["request"]["postData"]:
                        curl_command += "  --data '{}'".format(
                            entry["request"]["postData"]["text"]
                        )

                break
    # Extracting cookies
    cookies_match = re.search(r"Cookie:\s(.*?)'", curl_command)
    if cookies_match:
        cookies_str = cookies_match.group(1)
        cookies_list = cookies_str.split("; ")
        cookies = {
            cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies_list
        }

    # Extracting headers
    headers_match = re.findall(r"-H '(.*?)'", curl_command)
    headers = {header.split(": ")[0]: header.split(": ")[1] for header in headers_match}
    print(f"Всего {count_url} позиций")
    return curl_command, list_url


def get_cookie_header(curl_command):
    cookies = {}
    headers = {}
    params = {}
    method = "GET"  # по умолчанию

    url_match = re.search(r"'(.*?)'", curl_command)
    if url_match:
        url = url_match.group(1)
        parsed_url = urlparse(url)
        params = parse_qs(parsed_url.query)

    method_match = re.search(r"-X (\w+)", curl_command)
    if method_match:
        method = method_match.group(1)

    cookies_match = re.search(r"Cookie:\s(.*?)'", curl_command)
    if cookies_match:
        cookies_str = cookies_match.group(1)
        cookies_list = cookies_str.split("; ")
        cookies = {
            cookie.split("=")[0]: cookie.split("=")[1] for cookie in cookies_list
        }

    headers_match = re.findall(r"-H '(.*?)'", curl_command)
    headers = {header.split(": ")[0]: header.split(": ")[1] for header in headers_match}
    url_match = re.search(r"'(.*?)'", curl_command)
    url = None
    if url_match:
        url = url_match.group(1)
    return url, params, cookies, headers


def get_requests(url, params, headers, list_url, type_pars):
    if type_pars == 1:
        # Определите текущую директорию, где находится скрипт
        current_directory = os.getcwd()
        # Задайте имя папки data_json
        data_json_directory = "data_json_GamePal"
        if not os.path.exists(data_json_directory):
            os.makedirs(data_json_directory)
        # Создайте полный путь к папке data_json
        data_json_path = os.path.join(current_directory, data_json_directory)
        for i in range(1, list_url + 1):
            if i == 1:
                url = "https://sls.g2g.com/offer/search"
                params["currency"] = ["USD"]

                response = requests.get(url, params=params, headers=headers)
                json_data = response.json()
                filename = f"g2g_0{i}.json"
                file_path = os.path.join(data_json_path, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(
                        json_data, f, ensure_ascii=False, indent=4
                    )  # Записываем в файл
                print(f"Паузка 1сек, скачал {file_path}")
                time.sleep(1)
            if i > 1:
                url = "https://sls.g2g.com/offer/search"
                params["currency"] = ["USD"]
                params["page"] = [i]
                response = requests.get(url, params=params, headers=headers)
                json_data = response.json()
                filename = f"g2g_0{i}.json"
                file_path = os.path.join(data_json_path, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(
                        json_data, f, ensure_ascii=False, indent=4
                    )  # Записываем в файл
                print(f"Паузка 1сек, скачал {file_path}")
                time.sleep(1)
    elif type_pars == 0:
        driver = get_chromedriver()
        for l in range(1, list_url + 1):

            if l == 1:
                print(f"Страница {l}, а всего {list_url}")
                # Определите текущую директорию, где находится скрипт
                current_directory = os.getcwd()
                # Задайте имя папки data_json
                data_json_directory = "data_json_item"
                if not os.path.exists(data_json_directory):
                    os.makedirs(data_json_directory)
                # Создайте полный путь к папке data_json
                data_json_path = os.path.join(current_directory, data_json_directory)

                driver.get(url)
                time.sleep(5)
                hrefs = driver.find_elements(
                    By.XPATH,
                    '//div[@class="full-height full-width position-relative"]/a',
                )
                href = [urls.get_attribute("href") for urls in hrefs]
                extracted_parts = []
                for u in href:
                    # Разделяем URL на части по '/'
                    parts = u.split("/")
                    # Извлекаем последнюю часть, затем разделяем ее по '?' и берем первую часть
                    extracted_part = parts[-1].split("?")[0]
                    extracted_parts.append(extracted_part)
                params = {
                    "currency": "USD",
                    "country": "UA",
                    "include_inactive": "1",
                    "include_out_of_stock": "1",
                }
                headers = {
                    "authority": "sls.g2g.com",
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
                    "authorization": "",
                    "dnt": "1",
                    "origin": "https://www.g2g.com",
                    "referer": "https://www.g2g.com/",
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-site",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "x-api-key": "0DWATzuevY8r91rPCySTl91p2Odp6itK23sOskIX",
                }
                i = 1
                for d in extracted_parts:
                    urlss = f"https://sls.g2g.com/offer/{d}"
                    try:
                        response = requests.get(urlss, params=params, headers=headers)

                        # Проверяем статус ответа
                        if response.status_code == 200:
                            json_data = response.json()
                            # Дальнейшая обработка json_data
                        else:
                            print(f"Error {response.status_code}:", response.text)

                    except requests.exceptions.RequestException as e:
                        # Обработка исключений связанных с запросами
                        print("Request error:", e)

                    except json.decoder.JSONDecodeError as e:
                        # Обработка ошибок декодирования JSON
                        print("JSON Decode error:", e)
                    filename = f"g2g_{d}.json"
                    file_path = os.path.join(data_json_path, filename)
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(
                            json_data, f, ensure_ascii=False, indent=4
                        )  # Записываем в файл
                    # print(f'Паузка 1сек, скачал {file_path}')
                time.sleep(1)
            if l > 1:
                print(f"Страница {l}, а всего {list_url}")
                # Определите текущую директорию, где находится скрипт
                current_directory = os.getcwd()
                # Задайте имя папки data_json
                data_json_directory = "data_json_item"
                if not os.path.exists(data_json_directory):
                    os.makedirs(data_json_directory)
                # Создайте полный путь к папке data_json
                data_json_path = os.path.join(current_directory, data_json_directory)
                driver.get(f"{url}&page={l}")
                time.sleep(5)
                hrefs = driver.find_elements(
                    By.XPATH,
                    '//div[@class="full-height full-width position-relative"]/a',
                )
                href = [urls.get_attribute("href") for urls in hrefs]
                extracted_parts = []
                for u in href:
                    # Разделяем URL на части по '/'
                    parts = u.split("/")
                    # Извлекаем последнюю часть, затем разделяем ее по '?' и берем первую часть
                    extracted_part = parts[-1].split("?")[0]
                    extracted_parts.append(extracted_part)
                params = {
                    "currency": "USD",
                    "country": "UA",
                    "include_inactive": "1",
                    "include_out_of_stock": "1",
                }
                headers = {
                    "authority": "sls.g2g.com",
                    "accept": "application/json, text/plain, */*",
                    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
                    "authorization": "",
                    "dnt": "1",
                    "origin": "https://www.g2g.com",
                    "referer": "https://www.g2g.com/",
                    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": '"Windows"',
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-site",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "x-api-key": "0DWATzuevY8r91rPCySTl91p2Odp6itK23sOskIX",
                }
                i = 1
                for d in extracted_parts:
                    urlss = f"https://sls.g2g.com/offer/{d}"
                    try:
                        response = requests.get(urlss, params=params, headers=headers)

                        # Проверяем статус ответа
                        if response.status_code == 200:
                            json_data = response.json()
                            # Дальнейшая обработка json_data
                        else:
                            print(f"Error {response.status_code}:", response.text)

                    except requests.exceptions.RequestException as e:
                        # Обработка исключений связанных с запросами
                        print("Request error:", e)

                    except json.decoder.JSONDecodeError as e:
                        # Обработка ошибок декодирования JSON
                        print("JSON Decode error:", e)
                    filename = f"g2g_{d}.json"
                    file_path = os.path.join(data_json_path, filename)
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(
                            json_data, f, ensure_ascii=False, indent=4
                        )  # Записываем в файл
                    # print(f'Паузка 1сек, скачал {file_path}')
                time.sleep(1)


def parsing_gamePal(type_pars, file_name_csv):
    if type_pars == 1:
        # Определите текущую директорию, где находится скрипт
        current_directory = os.getcwd()

        # Задайте имя папки data_json
        data_json_directory = "data_json_GamePal"
        # Создайте полный путь к папке data_json

        data_json_path = os.path.join(current_directory, data_json_directory)
        if not os.path.exists(data_json_path):
            os.makedirs(data_json_path)
        folder = rf"{data_json_path}\*.json"
        files_json = glob.glob(folder)
        header_order = [
            "price",
            "unit_price",
            "name",
            "region",
            "checkout_devlivery",
            "stock",
            "Server",
            "ServiceType",
        ]

        # Создайте множество для уникальных заголовков
        unique_headers = set(header_order)

        # Здесь мы создаем CSV файл и записываем заголовки
        with open(f"{file_name_csv}.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(header_order)

        for item in files_json:
            print(item)
            with open(item, "r", encoding="utf-8") as f:
                data_json = json.load(f)
            datas = data_json["payload"]["results"]

            for g in datas:
                title = g["title"]
                unit_price = str(g["converted_unit_price"]).replace(".", ",")
                available_qty = g["available_qty"]
                min_qty = g["min_qty"]
                display_price = str(unit_price * min_qty).replace(".", ",")
                offer_attributes = g["offer_attributes"]
                region_id = g["region_id"]

                if region_id == "dfced32f-2f0a-4df5-a218-1e068cfadffa":
                    region_id = "US"
                if region_id == "ac3f85c1-7562-437e-b125-e89576b9a38e":
                    region_id = "EU"
                values = [
                    display_price,
                    unit_price,
                    title,
                    region_id,
                    available_qty,
                    min_qty,
                ]

                for o in offer_attributes:
                    pattern = r"lgc_\d+_(\w+)"
                    collection_id = re.findall(pattern, o["collection_id"])[0]
                    value = o["value"]

                    unique_headers.add(
                        collection_id
                    )  # Добавляем новый заголовок в множество
                    values.append(value)

                # Здесь мы добавляем значения в CSV файл построчно
                with open(
                    f"{file_name_csv}.csv", "a", newline="", encoding="utf-8"
                ) as csvfile:
                    writer = csv.writer(csvfile, delimiter=",")
                    writer.writerow(values)

        # Теперь записываем уникальные заголовки в первую строку CSV файла в заданном порядке
        with open(f"{file_name_csv}.csv", "r", newline="", encoding="utf-8") as f:
            lines = f.readlines()
        lines[0] = ",".join(header_order) + "\n"

        with open(f"{file_name_csv}.csv", "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)

        # Загрузка данных из файла CSV
        data = pd.read_csv(f"{file_name_csv}.csv", encoding="utf-8")

        # Сохранение данных в файл XLSX
        data.to_excel(f"{file_name_csv}.xlsx", index=False, engine="openpyxl")
        files = glob.glob(os.path.join(data_json_path, "*"))
        # Удаляем каждый файл
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
    elif type_pars == 0:
        current_directory = os.getcwd()

        # Задайте имя папки data_json
        data_json_directory = "data_json_item"
        data_json_path = os.path.join(current_directory, data_json_directory)
        if not os.path.exists(data_json_path):
            os.makedirs(data_json_path)
        folder = rf"{data_json_path}\*.json"
        files_json = glob.glob(folder)
        header_order = [
            "price",
            "unit_price",
            "name",
            "gallery_images",
            "checkout_devlivery",
            "stock",
            "Server",
            "ServiceType",
        ]

        # Создайте множество для уникальных заголовков
        unique_headers = set(header_order)

        # Здесь мы создаем CSV файл и записываем заголовки
        with open(f"{file_name_csv}.csv", "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            writer.writerow(header_order)

        for item in files_json:
            with open(item, "r", encoding="utf-8") as f:
                data_json = json.load(f)
            datas = data_json["payload"]
            title = datas["title"]
            unit_price = datas["converted_unit_price"]

            available_qty = datas["available_qty"]
            min_qty = datas["min_qty"]
            display_price = unit_price * min_qty

            try:
                gallery_images = datas["gallery_images"][0]
            except:
                gallery_images = None

            unit_price = str(unit_price).replace(".", ",")
            display_price = str(display_price).replace(".", ",")
            values = [
                display_price,
                unit_price,
                title,
                gallery_images,
                available_qty,
                min_qty,
            ]

            offer_attributes = datas["offer_attributes"]
            for o in offer_attributes:
                if o["collection_id"] == "9870fe77":
                    collection_id = "Server"
                elif o["collection_id"] == "33821c26":
                    collection_id = "Item Type"
                else:
                    pattern = r"lgc_\d+_(\w+)"
                    matches = re.findall(pattern, o["collection_id"])
                    if matches:
                        collection_id = matches[0]
                    else:
                        collection_id = "Unknown"
                value = o["value"]

                unique_headers.add(
                    collection_id
                )  # Добавляем новый заголовок в множество
                values.append(value)
            # Здесь мы добавляем значения в CSV файл построчно
            with open(
                f"{file_name_csv}.csv", "a", newline="", encoding="utf-8"
            ) as csvfile:
                writer = csv.writer(csvfile, delimiter=",")
                writer.writerow(values)

        # Теперь записываем уникальные заголовки в первую строку CSV файла в заданном порядке
        with open(f"{file_name_csv}.csv", "r", newline="", encoding="utf-8") as f:
            lines = f.readlines()
        lines[0] = ",".join(header_order) + "\n"

        with open(f"{file_name_csv}.csv", "w", newline="", encoding="utf-8") as f:
            f.writelines(lines)


def csv_to_excell(file_name_csv):
    current_directory = os.getcwd()
    data_json_directory = "data_json_item"
    data_json_path = os.path.join(current_directory, data_json_directory)
    if not os.path.exists(data_json_path):
        os.makedirs(data_json_path)
    folder = rf"{data_json_path}\*.json"
    files_json = glob.glob(folder)
    # Загрузка данных из файла CSV
    data = pd.read_csv(f"{file_name_csv}.csv", encoding="utf-8")

    # Сохранение данных в файл XLSX
    data.to_excel(f"{file_name_csv}.xlsx", index=False, engine="openpyxl")

    # Получаем список всех файлов в папке
    files = glob.glob(os.path.join(data_json_path, "*"))
    # Удаляем каждый файл
    for f in files:
        if os.path.isfile(f):
            os.remove(f)


if __name__ == "__main__":
    while True:
        print('Введите 1 для запуска парсинга'
            '\nВведите 0 для закрытия программы')
        user_input = int(input("Выберите действие: "))

        if user_input == 1:
            print("Вставьте ссылку")
            url_all = input()

            match = re.search(r"-(\w+)\?", url_all)
            type_pars_str = match.group(1)
            if type_pars_str == "service":
                type_pars = 1  # GamePal
                curl_result, list_url = selenium_get_curl(url_all, type_pars)
                get_cookie_header(curl_result)
                server.stop()  # остановка сервера должна быть здесь
                url, params, cookies, headers = get_cookie_header(curl_result)

                get_requests(url, params, headers, list_url, type_pars)
                print("Название файла")
                file_name_csv = input()
            else:
                type_pars = 0  # Items
                url = url_all
                curl_result, list_url = selenium_get_curl(url_all, type_pars)
                get_cookie_header(curl_result)
                server.stop()  # остановка сервера должна быть здесь
                url, params, cookies, headers = get_cookie_header(curl_result)
                get_requests(url, params, headers, list_url, type_pars)
                print("Название файла")
                file_name_csv = input()
            if type_pars_str == "service":
                type_pars = 1  # GamePal
            else:
                type_pars = 0  # Items
            parsing_gamePal(type_pars, file_name_csv)
            csv_to_excell(file_name_csv)
            if os.path.exists(f"{file_name_csv}.xlsx"):
                print(f"Файл {file_name_csv}.xlsx успешно создан.")
                time.sleep(5)
        elif user_input == 0:
            print("Программа завершена.")
            sys.exit(1)
        else:
            print("Неверный ввод, пожалуйста, введите корректный номер действия.")
        
