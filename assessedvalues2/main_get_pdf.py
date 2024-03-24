import requests
from bs4 import BeautifulSoup
import re
import pdfplumber
import re
import json
import mysql.connector
import os
import sys
import glob
import time


current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
pdf_path = os.path.join(temp_path, "pdf")


def create_folders():
    # Убедитесь, что папки существуют или создайте их
    for folder in [
        temp_path,
        pdf_path,
    ]:
        if not os.path.exists(folder):
            os.makedirs(folder)


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
    headers = config["headers"]

    # Генерация строки кукисов из конфигурации
    if "cookies" in config:
        cookies_str = "; ".join([f"{k}={v}" for k, v in config["cookies"].items()])
        headers["Cookie"] = cookies_str
    return config


def get_pdf():
    config = load_config()
    headers = config["headers"]
    print("Введите код города")
    # jurcode = int(input())
    jurcode = 102
    print("Введите диапозон поиска по кодам, от")
    # range_a = int(input())
    range_a = 1
    print("Введите диапозон поиска по кодам, до")
    # range_b = int(input())
    range_b = 10

    params = {
        "jurcode": jurcode,
    }
    folder_pdf = os.path.join(pdf_path, "*.pdf")
    files_pdf = glob.glob(folder_pdf)
    # Инициализация переменной для хранения максимального номера
    # Инициализация переменной для хранения всех найденных номеров
    found_parts = []

    # Обход всех файлов и сбор номеров в заданном диапазоне
    for item in files_pdf:
        filename = os.path.basename(item)
        parts = filename.split('_')
        if len(parts) >= 2:
            try:
                part_number = int(parts[1])  # Извлекаем номер
                if range_a <= part_number <= range_b:
                    found_parts.append(part_number)
            except ValueError:
                # Если part2 не является числом, пропускаем этот файл
                continue

    # Определяем отсутствующие номера в диапазоне
    missing_parts = [n for n in range(range_a, range_b + 1) if n not in found_parts]

    # Определяем номер, с которого начать обработку
    # Если в missing_parts есть элементы, берем первый как начальный номер для обработки
    current = missing_parts[0] if missing_parts else range_b + 1

    while current <= range_b:
        if current in found_parts:
            current += 1
            continue
        # for r in range(current, range_b):
            # filename_pdf = os.path.join(pdf_path, f"{r}_{extracted_part}.pdf")
            # if not os.path.exists(filename_pdf):
        data = {
            "__VIEWSTATE": "/wEPDwUKLTc4MjI3ODkzMQ9kFgJmD2QWAgIDD2QWBAIBDw8WAh4ISW1hZ2VVcmwFF34vSW1hZ2VzL0Jhbm5lcl8xMDIuZ2lmZGQCBw9kFgoCAw8PFgIeBFRleHQFc1RvIHZpZXcgYSBQcm9wZXJ0eSBSZWNvcmQgQ2FyZCwgY2xpY2sgb24gdGhlIDxpbWcgc3JjPSIvSW1hZ2VzL3BkZi5naWYiPiBpY29uIChmYXIgcmlnaHQgY29sdW1uKSBpbiBTZWFyY2ggUmVzdWx0cy5kZAIFDw8WAh8ABR1+L0ltYWdlcy9nZXRfYWRvYmVfcmVhZGVyLnBuZ2RkAgsPEGRkFgFmZAIPD2QWBgIFDw8WAh8BBSREYXRhYmFzZSBMYXN0IFVwZGF0ZWQgT246IDEyLzE1LzIwMjNkZAINDw8WAh4HVmlzaWJsZWhkZAIbDw8WAh8CaGRkAhEPZBYEAgUPDxYCHwJoZGQCEw8PFgIfAmhkZBgBBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAQUbY3RsMDAkTWFpbkNvbnRlbnQkQ2hlY2tCb3gxT80iG19lB94gVZz1EUBXqHW8Yrk=",
            "__VIEWSTATEGENERATOR": "53A94410",
            "__EVENTVALIDATION": "/wEdACGI52/fdvM1ojkzyOtJQ1U9E3u8fGxhoRzC+CoOGy3Pc2yehPXoKmEFi7AB0/0c5kRoD6AdipkjhA6txRFPEwFGVxiFmc0K4GVOqu4pU3XS5dBoR0owc5GbBC9NOn6m5NfJr9nyQzhpydi6mgPW2HwZZ5AWazvgVHy5dHSHxbp5a7CmYUDPSJEkKRjIOCeHpgnoljvz9AL8VPTgIyIMIZuG+d3fBy3LDDz0lsNt4u+CuHy54AbD95NHm/4/aSGZY8BK/NaKuqXdJrDDqiOq60YLKTrk38jQA0dsCq4LOmISS+otXN0C5/dk1ng4bn88f7YSHpSzsWdGUQdbNwKl9bSFrl6STmLjCZWJpqcNvRF+2vdqfdC80ccotIo0qyZaxpZB2Q8XgNBt8fh3a0nwoxyLr6PTBnr8UEoIXGKkTIjKBaYqgFYp21geoY8EnDgotAnHt8wJ0pUQtFgpOIHhWtwtTFeP/ttkFhn+GKF7kPiB7ou76UHXff5vzSA37Kf5sKpfT1jWnziQqskoPV+QvecSBuwQ5ywzv/l7GbY0CqFVTDhFmtWJSQP3Ng+qBKwq0H4NpB3eLizt/0/Y0ypFpty33pa2hggksIWlHRCkPi7XBmRGi8WAc1WDwix4vBITs9aVU2FANAvOssZt3gq/1YHU1QSYR2bhyBDDyq7xWTSrxuqtYwNFv7PYP9Csd7z86Wgj8hmlfwPt4hbSbaj+nNphCrCNyw==",
            "ctl00$MainContent$DDsortOption": "mapad",
            "ctl00$MainContent$BtnSearch": "Click to Search using criteria below",
            "ctl00$MainContent$lblKey": "Key",
            "ctl00$MainContent$lblMap": "Map",
            "ctl00$MainContent$lblParcel": "Parcel",
            "ctl00$MainContent$lblExt": "Ext",
            "ctl00$MainContent$lblOwner": "Owner",
            "ctl00$MainContent$lblLoc1": "St.No.",
            "ctl00$MainContent$lblLoc2": "StNo2",
            "ctl00$MainContent$lblStreet": "Street",
            "ctl00$MainContent$lblClass": "Class",
            "ctl00$MainContent$lblBook": "Book",
            "ctl00$MainContent$lblPage": "Page",
            "ctl00$MainContent$TxtKey": current,
            "ctl00$MainContent$TxtMap": "",
            "ctl00$MainContent$TxtParcel": "",
            "ctl00$MainContent$TxtExt": "",
            "ctl00$MainContent$TxtOwner": "",
            "ctl00$MainContent$TxtLoc1": "",
            "ctl00$MainContent$TxtLoc2": "",
            "ctl00$MainContent$TxtStreet": "",
            "ctl00$MainContent$TxtStcl": "",
            "ctl00$MainContent$TxtBook": "",
            "ctl00$MainContent$TxtPage": "",
        }

        response = requests.post(
            "https://www.assessedvalues2.com/SearchPage.aspx",
            params=params,
            headers=headers,
            data=data,
        )
        src = response.text
        soup = BeautifulSoup(src, "lxml")
        try:
            url_pdf = soup.find("a", attrs={"target": "_blank"}).get("href")
        except:
            print(f"Индекса {current} нету на сайте, пропускаем")
            current += 1
            # Пересчитываем пропущенные номера после обработки текущего номера
            missing_parts = [n for n in range(current, range_b + 1) if n not in found_parts]
            if missing_parts:
                current = missing_parts[0]  # Обновляем current до следующего отсутствующего номера
            continue
        url = f"https://www.assessedvalues2.com{url_pdf}"
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Проверяем, не вернул ли сервер ошибку

            pattern = r"pdf=([^&]+)"
            match = re.search(pattern, url)

            if match:
                extracted_part = match.group(1)  # Извлекаем нужную часть
                print(extracted_part)
            else:
                print("Совпадение не найдено.")
            filename_pdf = os.path.join(pdf_path, f"{jurcode}_{current}_{extracted_part}.pdf")
            with open(filename_pdf, "wb") as out_file:
                out_file.write(response.content)
                print(f"Файл успешно скачан и сохранён как {filename_pdf}")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP ошибка при скачивании файла: {http_err}")
        except Exception as e:
            print(f"Произошла ошибка при скачивании файла: {e}")
        
        current += 1
        # Пересчитываем пропущенные номера после обработки текущего номера
        missing_parts = [n for n in range(current, range_b + 1) if n not in found_parts]
        if missing_parts:
            current = missing_parts[0]  # Обновляем current до следующего отсутствующего номера


if __name__ == "__main__":
    # create_folders()
    get_pdf()
