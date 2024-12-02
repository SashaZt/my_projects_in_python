import asyncio
import json
import re
import time
from pathlib import Path

import aiofiles
import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from playwright.async_api import async_playwright

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"
json_page_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"

# Создание директорий, если их нет
html_files_directory.mkdir(parents=True, exist_ok=True)
json_page_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
output_csv_file = data_directory / "output.csv"
xlsx_result = data_directory / "result.xlsx"
json_result = data_directory / "result.json"
file_proxy = configuration_directory / "proxy.txt"
config_txt_file = configuration_directory / "config.txt"


async def save_html_to_file(file_name: str, html_content: str):
    """
    Асинхронно сохраняет HTML-контент в файл.

    :param file_name: Имя файла для сохранения HTML-контента.
    :param html_content: HTML-контент, который нужно сохранить.
    """
    try:
        async with aiofiles.open(file_name, mode="w", encoding="utf-8") as file:
            await file.write(html_content)
        print(f"HTML-контент успешно сохранен в файл: {file_name}")
    except Exception as e:
        print(f"Ошибка при сохранении файла {file_name}: {e}")


async def extract_next_page_number(page):
    """
    Извлекает номер следующей страницы из атрибута href кнопки "Вперед".

    :param page: Объект страницы Playwright.
    :return: Номер следующей страницы (str) или None, если кнопка не найдена.
    """
    try:
        # Ищем элемент "Вперед"
        next_button = await page.query_selector('[data-qaid="next_page"]')
        if not next_button:
            print("Кнопка 'Вперед' не найдена.")
            return None

        # Получаем значение атрибута href
        href = await next_button.get_attribute("href")
        if href:
            # Извлекаем номер страницы из href
            # Разделяем по ';' и извлекаем часть после ';' до '?'
            parts = href.split(";")
            if len(parts) > 1:
                page_part = parts[1].split("?")[0]
                print(f"Номер следующей страницы: {page_part}")
                return page_part
            else:
                print("Номер страницы отсутствует в href.")
                return None
        else:
            print("Атрибут href отсутствует у кнопки 'Вперед'.")
            return None
    except Exception as e:
        print(f"Ошибка при извлечении номера страницы: {e}")
        return None


async def run(playwright):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
    )
    page = await context.new_page()

    await context.route(
        "**/*",
        lambda route, request: (
            route.abort()
            if request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        ),
    )

    url = "https://satu.kz/Kartridzhi-fotobarabany?a18=13401"

    await page.goto(url)
    parts = url.rsplit("/", maxsplit=1)[-1].split(";")
    url_id = parts[0].split("?")[0]  # Извлекаем url_id

    # Прокручиваем страницу вниз
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(5)  # Ждем, чтобы страница догрузилась
    first_page = 1
    first_html_file = html_files_directory / f"{url_id}_0{first_page}.html"
    html_content = await page.content()
    await save_html_to_file(first_html_file, html_content)
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(5)  # Ждем, чтобы страница догрузилась

        next_page_number = await extract_next_page_number(page)

        output_html_file = html_files_directory / f"{url_id}_0{next_page_number}.html"
        html_content = await page.content()
        await save_html_to_file(output_html_file, html_content)
        # Ищем кнопку "Вперед"
        try:
            next_button = await page.query_selector('[data-qaid="next_page"]')
            if next_button:
                print("Кнопка 'Вперед' найдена. Нажимаем...")
                await next_button.click()
                await page.wait_for_load_state("load")
                await asyncio.sleep(2)  # Ждем загрузки новой страницы
            else:
                print("Кнопка 'Вперед' не найдена. Завершаем...")
                break
        except Exception as e:
            print("Ошибка при поиске кнопки 'Вперед':", e)
            break

    await browser.close()


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["id"].tolist()


def parsing_page():
    # Папка с HTML файлами
    # Множество для хранения уникальных itm_value
    unique_itm_values = set()

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_files_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            table = soup.find("div", attrs={"data-qaid": "product_gallery"})
            if table:  # Проверяем, что таблица найдена
                div_element = table.find_all("a", attrs={"rel": "nofollow"})
                if div_element:
                    for href in div_element:
                        url_company = href.get("href")
                        if url_company:  # Проверяем, что href существует
                            unique_itm_values.add(url_company)

    # Логируем уникальные значения после завершения обработки
    save_extracted_numbers_to_csv(unique_itm_values, output_csv_file)


def save_extracted_numbers_to_csv(unique_itm_values, output_file):
    """
    Извлекает числовую часть из URL-ов и сохраняет в CSV.

    :param unique_itm_values: Множество уникальных значений (URL-ов).
    :param output_file: Имя выходного CSV-файла.
    """
    try:
        # Извлекаем числовую часть из каждого URL
        extracted_numbers = [
            re.search(r"/c(\d+)-", url).group(1)
            for url in unique_itm_values
            if re.search(r"/c(\d+)-", url)
        ]

        # Преобразуем список чисел в DataFrame
        data = pd.DataFrame(extracted_numbers, columns=["id"])

        # Сохраняем в CSV
        data.to_csv(output_file, index=False, encoding="utf-8")
        print(f"Извлечённые числа сохранены в файл: {output_file}")
    except Exception as e:
        print(f"Ошибка при обработке и сохранении: {e}")


def parsing_json():
    """
    Преобразует JSON-данные о компании в плоский словарь.

    :param json_data: JSON-объект с информацией.
    :return: Плоский словарь с извлечёнными данными.
    """
    all_data = []
    for json_file in json_page_directory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)
        try:
            company_data = data.get("data", {}).get("company", {})

            # Составляем плоский словарь
            flat_data = {
                "company_id": company_data.get("id"),
                "name": company_data.get("name"),
                "contact_person": company_data.get("contactPerson"),
                "contact_email": company_data.get("contactEmail"),
                "address": company_data.get("addressText"),
                # "is_chat_visible": company_data.get("isChatVisible"),
                # "main_logo_url": company_data.get("mainLogoUrl"),
                "slug": company_data.get("slug"),
                # "is_one_click_order_allowed": company_data.get(
                #     "isOneClickOrderAllowed"
                # ),
                # "is_orderable_in_catalog": company_data.get("isOrderableInCatalog"),
                # "is_package_cpa": company_data.get("isPackageCPA"),
                # "address_map_description": company_data.get("addressMapDescription"),
                "website_url": company_data.get("webSiteUrl"),
                # "operation_type": company_data.get("operationType"),
                # "in_top_segment": company_data.get("inTopSegment"),
                "region_id": company_data.get("region", {}).get("id"),
                # "geo_coordinates": company_data.get("geoCoordinates"),
                "phones": "; ".join(
                    phone.get("number") for phone in company_data.get("phones", [])
                ),  # Соединяем номера телефонов через "; "
                "site_id": company_data.get("site", {}).get("id"),
                # "site_is_disabled": company_data.get("site", {}).get("isDisabled"),
                "opinion_stats_id": company_data.get("opinionStats", {}).get("id"),
                # "opinion_positive_percent": company_data.get("opinionStats", {}).get(
                #     "opinionPositivePercent"
                # ),
                # "opinion_total": company_data.get("opinionStats", {}).get(
                #     "opinionTotal"
                # ),
            }
            all_data.append(flat_data)

        except Exception as e:
            print(f"Ошибка при парсинге данных: {e}")
            return {}
    # Создаем DataFrame из списка словарей
    df = pd.DataFrame(all_data)

    # Сохраняем DataFrame в Excel файл
    df.to_excel(xlsx_result, index=False)


def get_json():
    companys_id = read_cities_from_csv(output_csv_file)
    cookies = {
        "cid": "270153821938440617613145839967091521916",
        "evoauth": "wb5cdecf4c4de459a88a9719d6d85a4d7",
        "timezone_offset": "120",
        "last_search_term": "",
        "user_tracker": "694b374bcae0b670fdef32ed66ce6fb6485f88ae|193.24.221.34|2024-11-30",
        "auth": "5c18ac9a4f6cb3bec14c7df31bbd6ea00f0cacbd",
        "csrf_token": "b0dc3533afe24266b9f754e83dbb165d",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "content-type": "application/json",
        # 'cookie': 'cid=270153821938440617613145839967091521916; evoauth=wb5cdecf4c4de459a88a9719d6d85a4d7; timezone_offset=120; last_search_term=; user_tracker=694b374bcae0b670fdef32ed66ce6fb6485f88ae|193.24.221.34|2024-11-30; auth=5c18ac9a4f6cb3bec14c7df31bbd6ea00f0cacbd; csrf_token=b0dc3533afe24266b9f754e83dbb165d',
        "dnt": "1",
        "origin": "https://satu.kz",
        "priority": "u=1, i",
        "referer": "https://satu.kz/c672063-internet-magazin-itmagkz.html",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-forwarded-proto": "https",
        "x-language": "ru",
        "x-requested-with": "XMLHttpRequest",
    }
    for company in companys_id:
        json_data = {
            "operationName": "CompanyContactsQuery",
            "variables": {
                "withGroupManagerPhones": False,
                "withWorkingHoursWarning": False,
                "getProductDetails": False,
                "company_id": company,
                "groupId": -1,
                "productId": -1,
            },
            "query": "query CompanyContactsQuery($company_id: Int!, $groupId: Int!, $productId: Long!, $withGroupManagerPhones: Boolean = false, $withWorkingHoursWarning: Boolean = false, $getProductDetails: Boolean = false) {\n  context {\n    context_meta\n    currentRegionId\n    recaptchaToken\n    __typename\n  }\n  company(id: $company_id) {\n    ...CompanyWorkingHoursFragment @include(if: $withWorkingHoursWarning)\n    ...CompanyRatingFragment\n    id\n    name\n    contactPerson\n    contactEmail\n    phones {\n      id\n      description\n      number\n      __typename\n    }\n    addressText\n    isChatVisible\n    mainLogoUrl(width: 100, height: 50)\n    slug\n    isOneClickOrderAllowed\n    isOrderableInCatalog\n    isPackageCPA\n    addressMapDescription\n    region {\n      id\n      __typename\n    }\n    geoCoordinates {\n      id\n      latitude\n      longtitude\n      __typename\n    }\n    branches {\n      id\n      name\n      phones\n      address {\n        region_id\n        country_id\n        city\n        zipCode\n        street\n        regionText\n        __typename\n      }\n      __typename\n    }\n    webSiteUrl\n    site {\n      id\n      isDisabled\n      __typename\n    }\n    operationType\n    __typename\n  }\n  productGroup(id: $groupId) @include(if: $withGroupManagerPhones) {\n    id\n    managerPhones {\n      id\n      number\n      __typename\n    }\n    __typename\n  }\n  product(id: $productId) @include(if: $getProductDetails) {\n    id\n    name\n    image(width: 60, height: 60)\n    price\n    signed_id\n    discountedPrice\n    priceCurrencyLocalized\n    buyButtonDisplayType\n    regions {\n      id\n      name\n      isCity\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CompanyWorkingHoursFragment on Company {\n  id\n  isWorkingNow\n  isOrderableInCatalog\n  scheduleSettings {\n    id\n    currentDayCaption\n    __typename\n  }\n  scheduleDays {\n    id\n    name\n    dayType\n    hasBreak\n    workTimeRangeStart\n    workTimeRangeEnd\n    breakTimeRangeStart\n    breakTimeRangeEnd\n    __typename\n  }\n  __typename\n}\n\nfragment CompanyRatingFragment on Company {\n  id\n  inTopSegment\n  opinionStats {\n    id\n    opinionPositivePercent\n    opinionTotal\n    __typename\n  }\n  __typename\n}",
        }
        company_id = json_data["variables"]["company_id"]
        output_html_file = json_page_directory / f"{company_id}.json"
        if output_html_file.exists():
            continue
        response = requests.post(
            "https://satu.kz/graphql",
            # cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30,
        )
        json_data = response.json()
        with open(output_html_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        time.sleep(4)


if __name__ == "__main__":

    # Запуск основной функции
    # asyncio.run(main())
    # parsing_page()
    get_json()
    # parsing_json()
