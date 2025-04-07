import asyncio
import json
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from logger import logger
from playwright.async_api import async_playwright

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "mediamarkt.html"


def get_html():

    cookies = {
        "optid": "469b68a9-118d-410b-bb03-57a589eb9344",
        "a": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Im8yc2lnbiJ9.eyJzdWIiOiI0ZDI4NjE5NS0wYjM4LTQ5NTAtODQ1Mi0zNzVjMjhjYzFhMjEiLCJpc3MiOiJtbXNlIiwiaWF0IjoxNzQzNzY0MDU3LCJleHAiOjE3NDQ5NzM2NTcsImF1ZCI6IndlYm1vYmlsZSIsInQiOiJ1IiwibyI6MTIwN30.OQ0b7vYdmUF0HYEw5bSvJtv91B-w5lnxgnv9ILDoTpSiQpzJru78rKXc5TfGFd8I9bv_CourbTGwj6mJARFRnRxtgB9HbdR1jfSCaqHkrN_bIBjmfI7J3pkFFtsmiCzu6q0cbKkID0-29VcmmtIAYwzGs1XQo4hZrjufELCTKtUZ4Y2d3mZVUIzY7CbBjq7VR5cumyfxOakUc_B6B5g1miP6cY_niOzzekaXv-eQNQG8hbSLSr5hYC6BEyuFVHNxbsw51w_y30VBr9aq6i_n5Hx6QoHE42qbwpc9pKk3xzZLTof6L3A-icKykWgbus6rWJFcUopdWgbvDSC-LaQD8A",
        "pwaconsent": "v:1.1&id:b0d45d1b64152f007ef190ee5fa9d41d2d5ebb1c&createdMs:1743764059162~required:1&clf:1,cli:1,gfb:1,gtm:1,mms:1,ocx:1|comfort:1&aid:1,baz:1,cne:1,con:1,fix:1,gfa:1,goa:1,gom:1,grc:1,ice:1,lob:1,loq:1,opt:1,ore:1,pcl:1,sen:1,spe:1,sst:1,swo:1,usz:1,woo:1,yte:1,zwi:1|marketing:1&adj:1,cri:1,fab:1,fcm:1,gad:1,gcl:1,gcm:1,gdv:1,gos:1,gse:1,msb:1,omp:1,ras:1,trd:1,wpx:1|",
        "tc_id": "f8c365ebe96f63a5017fb08399497f60bca635d8",
        "_cs_c": "1",
        "_fbp": "fb.1.1743764061017.54283647553947217",
        "ea_uuid": "202504041254212119106820",
        "_ga": "GA1.1.1393470515.1743764061",
        "FPAU": "1.2.1024136410.1743764062",
        "_fpid": "1393470515.1743764061",
        "_gcl_au": "1.1.1060656513.1743764108",
        "_cfuvid": "w8Ss3OeJRg7TJIwm8Y5x8Rbx3hMyClqe1J2EE3CVAbQ-1743928166394-0.0.1.1-604800000",
        "t_fpd": "true",
        "delivery_zip": "%7B%22zip%22%3A%22%22%2C%22name%22%3A%22%22%7D",
        "_msbps": "99",
        "__cf_bm": "c4lZrVVr8QOubSv0uRzXlD22cXFEPKAXppfVN0iz5sI-1743970705-1.0.1.1-wRP7LZgWZV_3Hy7ZzUyi0zgix0HcfBbd073niOEde3kT3DmDWc.x9xvq3DlPFELeF.e65IHpg0gp7GGwfUajfPLjxvCbKysA6oYvWXhfRLI",
        "ts_id": "2a10f738-97d0-4a58-b8dd-4dd5959f1ff6",
        "cf_clearance": "Ykc.P1GKnM3EbSepCTQwXwyuUtJaU5ic52XTpv9ZE8s-1743970990-1.2.1.1-D7iMMdAeMFqFJ3ttVMBryeNWEVqsh8lL5mbAOcmwRDPltH1PFl9hqhUc.df.0QQnkQ72Wm7gKroHKTHoBgkZ.CaZwDZQ19THfV8BAbn8WWe0CzK0Y3My_v.vxJgtLqdigL.e4QAF29EVitmKksraQTBhk17_CpyAkZZPAHJ20qy05xDShUi9tfcaiqrk.qYLqLuNyX.qgx5EEnEkGKIaVj0dG3MLtofTgK12CmQSXJn75tK1lTpVplFST8QUvfBT_oUxxDCY.ORbVDalKgR8fb5K98OhhlGJZhAQVsVQdlOOE9XRc3zRQWDwOOsHydUT2qvvsX.JH.SvvIVMsoysNhczrNAl0s4F36z4wtpoqUc8D02Kzc7UcWciD0O2V.ZZ",
        "lux_uid": "174397099299153546",
        "_cs_id": "d86a9edf-79f5-ae5b-d55c-84a975b6b423.1743764060.9.1743970995.1743970958.1.1777928060809.1.x",
        "_ga_4JZR222EHK": "GS1.1.1743970962.4.1.1743971053.0.0.78813528",
        "FPGSID": "1.1743970963.1743971053.G-4JZR222EHK.Fy-EXeWSR30WB6cbsnRFew",
        "_cs_s": "5.0.0.9.1743972883715",
        "_dd_s": "logs=1&id=51cabb26-8ebd-4d5b-8162-440086976cc2&created=1743958295483&expire=1743971989154",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://mediamarkt.pl/pl/category/sprzatanie-36928.html?query=Odkurzacz&filter=currentprice:199-6899&__cf_chl_tk=wdaxevprMO9JDFCXCrd.ChbKRupwjiy92E.IoWwJG08-1743970981-1.0.1.1-UmFJghRegP0WB7bHtdIYbTsfeIbsMuhiYYyuhE6ljMk",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-full-version": '"135.0.7049.41"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="135.0.7049.41", "Not-A.Brand";v="8.0.0.0", "Chromium";v="135.0.7049.41"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"7.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://mediamarkt.pl/pl/product/_odkurzacz-bezprzewodowy-samsung-vs20c8527tbge-jet-85-pro-1477075.html",
        cookies=cookies,
        headers=headers,
        timeout=10,
    )

    # Проверка кода ответа
    if response.status_code == 200:

        # Сохранение HTML-страницы целиком
        with open(output_html_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")


def remove_at_type(data):
    """Рекурсивно удаляет ключи '@type' из словаря."""
    if isinstance(data, dict):
        # Создаем новый словарь без '@type'
        new_data = {k: remove_at_type(v) for k, v in data.items() if k != "@type"}
        return new_data
    elif isinstance(data, list):
        return [remove_at_type(item) for item in data]
    return data


# Функция для извлечения названия предприятия
def parse_company_name(soup):
    company_name_tag = soup.find(
        "p", class_="modal-title display-inline-block farmer-modal-name ng-binding"
    )
    if company_name_tag:
        return company_name_tag.text.strip()
    return None


# 1. Парсинг телефонных номеров
def parse_phone_numbers(soup):
    phone_data = []
    phone_rows = soup.find_all("tr", class_="beige-hover ng-scope ng-isolate-scope")

    for row in phone_rows:
        phone_dict = {}

        # Извлекаем номер телефона
        phone_link = row.find("a", class_="same-phone-width")
        if phone_link:
            phone_dict["phone_number"] = re.sub(
                r"\s+", " ", phone_link.get("data-content", "").strip()
            )

        # Извлекаем позицию
        position = row.find("span", class_="position-title")
        phone_dict["position"] = position.text.strip() if position else None

        # Извлекаем ФИО
        full_name = row.find("span", class_="phone-comment")
        phone_dict["full_name"] = (
            re.sub(r"\s+", " ", full_name.text.strip()) if full_name else None
        )

        phone_data.append(phone_dict)

    return phone_data


# 2. Парсинг email-таблицы
def parse_emails(soup):
    email_data = []
    email_rows = soup.find_all(
        "tr",
        class_="beige-hover ng-scope",
        attrs={"ng-repeat": "contact in contacts | filter: { name:'email' }"},
    )

    for row in email_rows:
        email_dict = {}

        # Извлекаем email
        email = row.find("span", class_="ng-binding")
        email_dict["email"] = email.text.strip() if email else None

        email_data.append(email_dict)

    return email_data


# 3. Парсинг дополнительной информации
def parse_additional_info(soup):
    info_dict = {}
    org_info = soup.find("div", class_="org-info-parent")

    if org_info:
        # Извлекаем директора
        director_div = org_info.find("div", {"ng-if": "org.director"})
        if director_div:
            director = director_div.find("div", class_="ng-binding")
            info_dict["director"] = director.text.strip() if director else None

        # Извлекаем ЭДРПОУ
        edrpou_div = org_info.find("div", {"ng-if": "org.erdpou"})
        if edrpou_div:
            edrpou = edrpou_div.find("div", class_="ng-binding")
            info_dict["edrpou"] = edrpou.text.strip() if edrpou else None

        # Извлекаем адрес
        address_div = org_info.find("div", {"ng-if": "org.address_label"})
        if address_div:
            address = address_div.find("div", class_="ng-binding")
            info_dict["address"] = address.text.strip() if address else None

        # Извлекаем КВЭД
        kved_div = org_info.find("div", {"ng-if": "org.description"})
        if kved_div:
            kved = kved_div.find("div", class_="ng-binding")
            info_dict["kved"] = kved.text.strip() if kved else None

    return info_dict


# Функция для разделения ФИО на части
def split_full_name(full_name):
    if not full_name:
        return None, None, None
    parts = full_name.split()
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1], None
    elif len(parts) == 1:
        return parts[0], None, None
    return None, None, None


# Функция для извлечения области, района и города/села из адреса
def parse_address(address):
    if not address:
        return None, None, None

    parts = address.split(",")
    if len(parts) < 3:
        return None, None, None

    # Область обычно после "Україна"
    region = None
    district = None
    locality = None

    for part in parts:
        part = part.strip()
        if "обл." in part:
            region = part
        elif "р-н" in part:
            district = part
        elif "село" in part or "місто" in part or "селище" in part:
            locality = part

    return region, district, locality


def scrap_html():
    with open("Page_01.html", "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")

    # Парсим данные
    company_name = parse_company_name(soup)  # Извлекаем название предприятия
    phone_numbers = parse_phone_numbers(soup)
    emails = parse_emails(soup)
    additional_info = parse_additional_info(soup)

    # Добавляем название предприятия в additional_info
    additional_info["company_name"] = company_name

    # Объединяем все в одну структуру
    combined_data = {
        "contacts": {"phone_numbers": phone_numbers, "emails": emails},
        "organization": additional_info,
    }

    # Преобразуем в красивый JSON с отступами и поддержкой UTF-8
    pretty_json = json.dumps(combined_data, indent=4, ensure_ascii=False)
    logger.info(pretty_json)

    # Сохраняем в JSON
    with open("parsed_data.json", "w", encoding="utf-8") as f:
        json.dump(combined_data, f, indent=4, ensure_ascii=False)

    # Подготовка данных для Excel
    # Создаем словарь для одной строки
    excel_row = {}

    # Заполняем основные поля из additional_info
    excel_row["ЄДРПОУ"] = additional_info.get("edrpou", None)
    excel_row["Назва підприємства"] = additional_info.get("company_name", None)
    excel_row["Основний квед"] = additional_info.get("kved", None)
    excel_row["Директор (ФИО)"] = additional_info.get("director", None)

    # Разделяем ФИО директора
    last_name, first_name, middle_name = split_full_name(
        additional_info.get("director")
    )
    excel_row["Директор (прізвище)"] = last_name
    excel_row["Директор (імʼя)"] = first_name
    excel_row["Директор (по-батькові)"] = middle_name

    # Извлекаем адресные данные
    address = additional_info.get("address")
    region, district, locality = parse_address(address)
    excel_row["Адреса (юридична)"] = address
    excel_row["Область"] = region
    excel_row["Район"] = district
    excel_row["Місто / селище / село"] = locality

    # Добавляем email (берем первый доступный)
    excel_row["Емайл"] = emails[0]["email"] if emails else None

    # Добавляем телефоны (до 5 номеров)
    for i in range(5):
        if i < len(phone_numbers) and "phone_number" in phone_numbers[i]:
            excel_row[f"Телефон {i+1}"] = phone_numbers[i]["phone_number"]
        else:
            excel_row[f"Телефон {i+1}"] = None

    # Создаем DataFrame
    df = pd.DataFrame([excel_row])

    # Определяем порядок столбцов
    columns_order = [
        "ЄДРПОУ",
        "Назва підприємства",
        "Основний квед",
        "Директор (ФИО)",
        "Директор (прізвище)",
        "Директор (імʼя)",
        "Директор (по-батькові)",
        "Адреса (юридична)",
        "Область",
        "Район",
        "Місто / селище / село",
        "Емайл",
        "Телефон 1",
        "Телефон 2",
        "Телефон 3",
        "Телефон 4",
        "Телефон 5",
    ]

    # Применяем порядок столбцов
    df = df[columns_order]

    # Записываем в Excel
    with pd.ExcelWriter("parsed_data.xlsx", engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Data", index=False)

    logger.info("Данные успешно записаны в файл 'parsed_data.xlsx'")


async def main():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False
        )  # Set headless=True in production

        # Create new context with optimizations
        context = await browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            permissions=["geolocation"],
            device_scale_factor=1.0,
            has_touch=True,
            ignore_https_errors=True,
        )

        # Disable loading of images, fonts and other media files
        await context.route(
            "**/*",
            lambda route, request: (
                route.abort()
                if request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_()
            ),
        )

        # Create new page
        page = await context.new_page()

        # Navigate to the website (replace with your target URL)
        await page.goto("https://www.tikleap.com/")  # Replace with your actual URL
        await asyncio.sleep(50)

        # Wait for the postal code element to appear and click it
        postal_code_button = await page.wait_for_selector(
            'span:text("Wpisz kod pocztowy")'
        )
        await postal_code_button.click()

        # Wait for the input field to appear
        postal_code_input = await page.wait_for_selector(
            'input[aria-describedby="hnf-postalcode-helper"]'
        )

        # Type the postal code
        await postal_code_input.fill("22-100")

        # Press Enter
        await postal_code_input.press("Enter")

        # Wait a moment to see the result (adjust as needed)
        await asyncio.sleep(5)

        # Close browser
        await browser.close()


if __name__ == "__main__":
    # scrap_html()
    # main_realoem()
    get_html()
    # asyncio.run(main())
