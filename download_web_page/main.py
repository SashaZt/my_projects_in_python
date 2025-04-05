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
output_html_file = html_directory / "leroymerlin.html"


def get_html():

    cookies = {
        "auto-contextualization_attempt": "true",
        "pa_privacy": "%22exempt%22",
        "_pcid": "%7B%22browserId%22%3A%22m92o0q4hag9yp49x%22%2C%22_t%22%3A%22mor2y7gv%7Cm92o0q4w%22%7D",
        "_pctx": "%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAE0RXSwH18yBbSjABMATwDsAcwAeAH34BOYZQAMARwAs0kAF8gA",
        "search_session": "98d4bc9d-ec38-4964-9d87-e5580a2c2932|28558dab-c963-4d0a-8484-8fa043e4de36",
        "lm-csrf": "NRwFebxOetyJxoWRgDdTrtL/RC6V22G4PHMpt6vAIqQ=.1743788028610.gf9zZQ4PaLxS3inL/MkaEqmqxUHy2pY9KI3nnJJ1piA=",
        "datadome": "HMpjtGnjVp~W11i2li6SPskEeV~K01mTy8LnBXo8JPT22zvgyfZeiNSXvm0NE~Vus7mZyGhYrJQFHEmOCf1b3rvPpqyU2nXqTmzNlqfeqMo1iesS9wYTuJlIWO9xqwAV",
        "_dd_s": "rum=0&expire=1743788936024",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://www.leroymerlin.pl/produkty/odkurzacz-przemyslowy-starmix-basic-ipulse-l-1635-35-l-1600w-80900005.html",
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
    scrap_html()
    # main_realoem()
    # get_html()
    # asyncio.run(main())
