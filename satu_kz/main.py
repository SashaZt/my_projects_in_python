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
data_directory = current_directory / "data"
json_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"

# Создание директорий, если их нет
json_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

# Пути к файлам
output_csv_file = data_directory / "output.csv"
all_urls_file = data_directory / "all_urls.csv"
product_catalog_csv = data_directory / "product_catalog.csv"
xlsx_result = data_directory / "result.xlsx"
json_result = data_directory / "result.json"
file_proxy = configuration_directory / "proxy.txt"
config_txt_file = configuration_directory / "config.txt"


async def save_links_to_file(links: list, file_name: str):
    """
    Асинхронно сохраняет список ссылок в файл.

    :param links: Список ссылок для сохранения.
    :param file_name: Имя файла для сохранения.
    """
    try:
        # Открываем файл и записываем ссылки
        async with aiofiles.open(file_name, mode="w", encoding="utf-8") as file:
            for link in links:
                await file.write(link + "\n")
        print(f"Ссылки успешно сохранены в файл: {file_name}")
    except Exception as e:
        print(f"Ошибка при сохранении файла {file_name}: {e}")


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


# Функция для извлечения номера следующей страницы
async def extract_next_page_number(page):
    """
    Извлекает номер следующей страницы из кнопки "Вперед" или последней ссылки.

    :param page: Объект страницы Playwright.
    :return: Номер следующей страницы (str) или None, если кнопка/ссылка не найдена.
    """
    try:
        # Ищем кнопку "Вперед"
        next_button = await page.query_selector('[data-qaid="next_page"]')
        if next_button:
            # Если кнопка найдена, получаем значение атрибута href
            href = await next_button.get_attribute("href")
            if href:
                # Извлекаем номер страницы из href
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
        else:
            # Если кнопка "Вперед" отсутствует, ищем последнюю ссылку
            pages = await page.locator('[data-qaid="pages"]').all()
            if pages:
                # Находим последний элемент и получаем его ссылку
                last_page = pages[-1]
                last_page_href = await last_page.get_attribute("href")
                if last_page_href:
                    try:
                        # Извлекаем номер страницы из ссылки
                        last_page_number = last_page_href.split(";")[1].split("?")[0]
                        print(f"Номер последней страницы: {last_page_number}")
                        return last_page_number
                    except IndexError:
                        print(
                            f"Ошибка при извлечении номера страницы из ссылки: {last_page_href}"
                        )
                        return None
                else:
                    print("Не удалось извлечь ссылку на последнюю страницу.")
                    return None
            else:
                print("Страницы не найдены.")
                return None
    except Exception as e:
        print(f"Ошибка при извлечении номера страницы: {e}")
        return None


async def extract_json_country(page):
    # Собираем Страны
    """
    Находит первый <script type="application/javascript"> на странице,
    извлекает JSON из его содержимого и сохраняет в файл JSON.

    :param page: Объект страницы Playwright.
    :param output_json_path: Путь для сохранения извлеченного JSON.
    """
    try:
        # Находим первый тег <script type="application/javascript">
        script = await page.query_selector('//script[@type="application/javascript"]')
        if not script:
            print("Не найдено ни одного тега <script type='application/javascript'>.")
            return

        # Извлекаем содержимое тега
        script_content = await script.inner_html()

        if script_content.strip():
            # Регулярное выражение для поиска JSON-структуры
            json_pattern = re.compile(
                r"window\.ApolloCacheState\s*=\s*({.*?});", re.DOTALL
            )
            match = json_pattern.search(script_content)

            if match:
                # Извлекаем JSON
                json_str = match.group(1)
                parsed_json = json.loads(json_str)
                dict_country = parsin_country_json(parsed_json)
                return dict_country
                # logger.info(dict_json)
                # # Сохраняем JSON в файл
                # with open(output_json_path, "w", encoding="utf-8") as json_file:
                #     json.dump(parsed_json, json_file, indent=4, ensure_ascii=False)

            else:
                print("JSON структура не найдена в содержимом скрипта.")
        else:
            print("Содержимое первого тега <script> пусто.")
    except Exception as e:
        print(f"Ошибка: {e}")


async def extract_json_company(page):
    """
    Находит первый <script type="application/javascript"> на странице,
    извлекает JSON из его содержимого и сохраняет в файл JSON.

    :param page: Объект страницы Playwright.
    :param output_json_path: Путь для сохранения извлеченного JSON.
    """
    try:
        # Находим первый тег <script type="application/javascript">
        script = await page.query_selector('//script[@type="application/javascript"]')
        if not script:
            print("Не найдено ни одного тега <script type='application/javascript'>.")
            return

        # Извлекаем содержимое тега
        script_content = await script.inner_html()

        if script_content.strip():
            # Регулярное выражение для поиска JSON-структуры
            json_pattern = re.compile(
                r"window\.ApolloCacheState\s*=\s*({.*?});", re.DOTALL
            )
            match = json_pattern.search(script_content)

            if match:
                # Извлекаем JSON
                json_str = match.group(1)
                parsed_json = json.loads(json_str)
                dict_company = parsin_company_json(parsed_json)
                return dict_company

            else:
                print("JSON структура не найдена в содержимом скрипта.")
        else:
            print("Содержимое первого тега <script> пусто.")
    except Exception as e:
        print(f"Ошибка: {e}")


def save_extracted_numbers_to_csv(unique_itm_values, output_csv_file):
    """
    Сохраняет уникальные значения в CSV файл с заголовком 'id'.

    :param unique_itm_values: Множество уникальных значений.
    :param output_csv_file: Путь к выходному CSV файлу.
    """
    try:
        # Преобразуем множество в DataFrame, приводя значения к строкам, если требуется
        df = pd.DataFrame([str(value) for value in unique_itm_values], columns=["id"])

        # Сохраняем в CSV
        df.to_csv(output_csv_file, index=False, encoding="utf-8")
        logger.info(f"Данные успешно сохранены в {output_csv_file}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в CSV: {e}")


# Основная функция сбора последне категории в списке
async def run_one(playwright):
    proxy_config = {
        "server": "http://5.79.73.131:13010",
    }
    # Запускаем браузер
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

    # Отключаем загрузку ненужных ресурсов (изображения, шрифты и т.д.)
    await context.route(
        "**/*",
        lambda route, request: (
            route.abort()
            if request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        ),
    )
    unique_itm_values = set()
    companys_url = read_cities_from_csv(all_urls_file)
    # URL для обработки
    # url_start = "https://satu.kz/Spetsialnye-tkani"
    for url in companys_url:
        await page.goto(url)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(5)  # Ждем загрузки
        all_company = await extract_json_company(page)
        # Добавляем каждый элемент списка all_company в уникальное множество
        unique_itm_values.update(all_company)
        all_urls = await extract_json_country(page)

        for url_raw in all_urls:
            url_value = url_raw["value"]
            # url_name = url_raw["name"]
            url_id = url.split("?", maxsplit=1)[0].split("/")[-1]
            url = f"{url}{url_value}"
            await page.goto(url)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            all_company = await extract_json_company(page)
            # Добавляем каждый элемент списка all_company в уникальное множество
            unique_itm_values.update(all_company)
            await asyncio.sleep(1)  # Ждем загрузки
        logger.info(len(unique_itm_values))
        url_id = url.split("?", maxsplit=1)[0].split("/")[-1]
        output_file = data_directory / f"{url_id}.csv"
        save_extracted_numbers_to_csv(unique_itm_values, output_file)

    await browser.close()


async def main_one():
    async with async_playwright() as playwright:
        await run_one(playwright)


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["id"].tolist()


def parsing_json():
    """
    Преобразует JSON-данные о компании в плоский словарь.

    :param json_data: JSON-объект с информацией.
    :return: Плоский словарь с извлечёнными данными.
    """
    all_data = []
    for json_file in json_directory.glob("*.json"):
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
    # 37.48.118.4:13010
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
        output_json_file = json_directory / f"{company_id}.json"
        if output_json_file.exists():
            continue
        response = requests.post(
            "https://satu.kz/graphql",
            # cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=30,
        )
        json_data = response.json()
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
        time.sleep(4)


def extract_values_with_title(quick_filters, target_title):
    """
    Находит фильтр по 'title' и извлекает список значений с названиями и форматированным значением.

    :param quick_filters: Список фильтров.
    :param target_title: Название ('title') фильтра, который нужно найти.
    :return: Список словарей с полями 'name' и 'value'.
    """
    try:
        # Найти фильтр с указанным 'title'
        for filter_item in quick_filters:
            if filter_item.get("title") == target_title:
                filter_name = filter_item.get("name")
                if filter_name:
                    # Формируем список словарей с названием и значением
                    return [
                        {
                            "name": value["title"],
                            "value": f"?{filter_name}={value['value']}",
                        }
                        for value in filter_item.get("values", [])
                    ]
        return []
    except Exception as e:
        print(f"Ошибка при извлечении значений: {e}")
        return []


def parsin_country_json(data):
    # Получаем список словарей, страна и ссылка на нее
    try:

        # Locate the target key dynamically in "ROOT_QUERY"
        key_prefix = 'categoryListing({"alias":"Spetsialnye-tkani","limit":48,'
        target_key = next(
            (key for key in data["ROOT_QUERY"] if key.startswith(key_prefix)), None
        )

        if not target_key:
            return "Target key not found in ROOT_QUERY."

        # Navigate to the "page" -> "quickFilters" -> "title"
        quick_filters = data["ROOT_QUERY"][target_key]["page"].get("quickFilters", {})
        # Пример использования
        target_title = "Страна производитель"  # Замените на нужное название фильтра
        result = extract_values_with_title(quick_filters, target_title)
        return result

    except KeyError as e:
        return f"KeyError: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def parsin_company_json(data):
    # Получаем список словарей, страна и ссылка на нее
    try:

        # Locate the target key dynamically in "ROOT_QUERY"
        key_prefix = 'categoryListing({"alias":"Spetsialnye-tkani","limit":48,'
        target_key = next(
            (key for key in data["ROOT_QUERY"] if key.startswith(key_prefix)), None
        )

        if not target_key:
            return "Target key not found in ROOT_QUERY."

        # Navigate to the "page" -> "quickFilters" -> "title"
        companyIds_raw = data["ROOT_QUERY"][target_key]["page"].get("companyIds", [])
        # Пример использования
        return companyIds_raw

    except KeyError as e:
        return f"KeyError: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


# Основная функция
async def run(playwright):
    proxy_config = {
        "server": "http://5.79.73.131:13010",
    }
    # Запускаем браузер
    browser = await playwright.chromium.launch(headless=False)
    # browser = await playwright.chromium.launch(proxy=proxy_config, headless=False)
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
    )
    page = await context.new_page()

    # Отключаем загрузку ненужных ресурсов (изображения, шрифты и т.д.)
    await context.route(
        "**/*",
        lambda route, request: (
            route.abort()
            if request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        ),
    )
    # URL для обработки
    url_start = "https://satu.kz/consumer-goods"
    await page.goto(url_start)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(5)  # Ждем загрузки
    # Извлечение ссылок первого уровня
    all_links_level_1 = await extract_links_from_grid_block(page)
    logger.info(all_links_level_1)
    if not all_links_level_1:
        logger.info("Ссылки первого уровня не найдены.")
        return

    # Хранилище всех конечных ссылок
    final_links = []

    # Рекурсивная обработка всех ссылок первого уровня
    for link in list(all_links_level_1)[:1]:

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await process_links_recursively(page, link, final_links)

    # Закрываем браузер
    await browser.close()

    # Сохраняем собранные ссылки в CSV
    save_links_to_csv(final_links, all_urls_file)


async def process_links_recursively(page, current_link, final_links):
    """
    Рекурсивно обходит ссылки, начиная с текущей, до последнего уровня.

    :param page: Объект страницы Playwright.
    :param current_link: Ссылка для обработки.
    :param final_links: Список для сохранения конечных ссылок.
    """
    try:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        # Переход на текущую ссылку
        await page.goto(current_link)
        await asyncio.sleep(2)  # Ждем загрузки страницы

        # Извлечение дочерних ссылок
        child_links = await extract_links_from_scroll_block(page)
        logger.info(child_links)
        # Если дочерних ссылок нет, добавляем текущую ссылку в финальный список
        if not child_links:
            final_links.append(current_link)
            logger.info(f"Последняя ссылка: {current_link}")
            return

        # Рекурсивно обрабатываем каждую дочернюю ссылку
        for child_link in child_links:

            await process_links_recursively(page, child_link, final_links)

    except Exception as e:
        logger.error(f"Ошибка на ссылке {current_link}: {e}")


def save_links_to_csv(links, file_path):
    """
    Сохраняет список ссылок в CSV.

    :param links: Список ссылок.
    :param file_path: Путь для сохранения CSV.
    """
    try:
        # Создаем DataFrame с заголовком 'url'
        df = pd.DataFrame(links, columns=["url"])
        df.to_csv(file_path, index=False, encoding="utf-8")
        print(f"Ссылки успешно сохранены в файл: {file_path}")
    except Exception as e:
        print(f"Ошибка при сохранении ссылок в CSV: {e}")


async def extract_links_from_grid_block(page):
    """
    Извлекает ссылки (href) из элементов внутри //div[@data-qaid="grid_block"].

    :param page: Объект страницы Playwright.
    :return: Список ссылок (href).
    """
    try:
        links = set()
        # Ищем блок grid_block
        grid_block = await page.query_selector('//div[@data-qaid="grid_block"]')
        if not grid_block:
            print("Блок grid_block не найден.")
            return None

        # Ищем все div внутри grid_block
        divs = await grid_block.query_selector_all("//div")
        for div in divs:
            # Ищем все <a> внутри каждого div
            anchors = await div.query_selector_all("a")
            for anchor in anchors:
                href = await anchor.get_attribute("href")
                if href:
                    url = f"https://satu.kz{href}"
                    links.add(url)
        return links
    except Exception as e:
        print(f"Ошибка при извлечении ссылок: {e}")
        return []


async def extract_links_from_scroll_block(page):
    """
    Извлекает ссылки (href) из элементов внутри //ul[@data-qaid="scroll_block"].

    :param page: Объект страницы Playwright.
    :return: Список ссылок (href).
    """
    try:
        links = set()
        # Ищем блок scroll_block
        scroll_block = await page.query_selector('//ul[@data-qaid="scroll_block"]')
        if not scroll_block:
            print("Блок scroll_block не найден.")
            return None

        # Ищем все <a> внутри блока scroll_block
        anchors = await scroll_block.query_selector_all("a")
        for anchor in anchors:
            href = await anchor.get_attribute("href")
            if href:
                url = f"https://satu.kz{href}" if href.startswith("/") else href
                links.add(url)
        return list(links)
    except Exception as e:
        print(f"Ошибка при извлечении ссылок: {e}")
        return []


if __name__ == "__main__":

    # Запуск основной функции
    # asyncio.run(main())
    asyncio.run(main_one())
    # parsing_page()
    # get_json()
    # parsing_json()
