import re
import json
import os
import csv
import aiofiles
import glob
import asyncio
from selectolax.parser import HTMLParser
from curl_cffi.requests import AsyncSession
from asyncio import WindowsSelectorEventLoopPolicy
from configuration.logger_setup import logger
import random
import sys

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)


def get_dir_json():
    """
    Создание директорий и файлов JSON из out.json.

    - Загружает файл out.json, содержащий данные для разных сайтов.
    - Создает поддиректории для каждого сайта в папке temp.
    - Сохраняет данные для каждого сайта в отдельный out.json в соответствующей поддиректории.
    """
    with open("out.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    for key in data.keys():
        dir_path = os.path.join(temp_path, key)
        os.makedirs(dir_path, exist_ok=True)

        with open(os.path.join(dir_path, "out.json"), "w", encoding="utf-8") as outfile:
            json.dump({key: data[key]}, outfile, ensure_ascii=False, indent=4)

    logger.info("Данные успешно разделены и сохранены в соответствующих папках.")
    load_json_files_from_subdirectories()


def load_json_files_from_subdirectories():
    """
    Загрузка JSON-файлов из поддиректорий и сохранение ссылок в CSV.

    - Итерирует по поддиректориям в папке temp.
    - Загружает out.json из каждой поддиректории и извлекает ссылки.
    - Сохраняет извлеченные ссылки в файлы CSV в соответствующих поддиректориях.
    """
    for root, dirs, files in os.walk(temp_path):
        for directory in dirs:
            subdir_path = os.path.join(root, directory)
            json_file_path = os.path.join(subdir_path, "out.json")
            csv_file_path = os.path.join(subdir_path, "out.csv")

            all_links = []
            if os.path.exists(json_file_path):
                with open(json_file_path, "r", encoding="utf-8") as json_file:
                    try:
                        data = json.load(json_file)
                        links = data.get("motodom_ua", [])
                        for l in links:
                            all_links.append(l["link"])
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка при загрузке {json_file_path}: {e}")

            with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                for link in all_links:
                    writer.writerow([link])


def get_random_proxy():
    """
    Возвращает случайный прокси из файла proxi.json.

    - Загружает список прокси из файла proxi.json.
    - Выбирает случайный прокси из списка.
    - Форматирует прокси для использования в HTTP-запросах.
    - Если файл отсутствует или содержит некорректные данные, завершает выполнение программы.
    """
    proxies_path = os.path.join("configuration", "proxi.json")

    try:
        with open(proxies_path, "r", encoding="utf-8") as proxy_file:
            proxies = json.load(proxy_file)

        if not proxies:
            logger.error("Файл proxi.json пуст или не содержит корректных данных.")
            sys.exit(
                "Программа завершена из-за отсутствия корректных данных в proxi.json."
            )

        proxy = random.choice(proxies)
        proxy_url = f"http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
        return proxy_url
    except FileNotFoundError:
        logger.error("Файл proxi.json не найден в папке configuration.")
        sys.exit("Программа завершена из-за отсутствия файла proxi.json.")
    except json.JSONDecodeError:
        logger.error("Ошибка чтения JSON из файла proxi.json.")
        sys.exit("Программа завершена из-за ошибки чтения JSON из файла proxi.json.")
    except IndexError:
        logger.error("Файл proxi.json пуст или не содержит корректных данных.")
        sys.exit("Программа завершена из-за отсутствия корректных данных в proxi.json.")


async def fetch_and_save_html(url, file_name_html, cookies, headers):
    """
    Загрузка HTML страницы и сохранение в файл.

    - Загружает страницу по указанному URL, используя заданные cookies и headers.
    - Сохраняет полученное HTML-содержимое в файл.
    - Использует случайный прокси для выполнения запроса.
    - Логирует ошибки при загрузке страницы.
    """
    if not os.path.exists(file_name_html):
        try:
            proxy_url = get_random_proxy()
            if proxy_url is None:
                logger.error("Нет доступных прокси для использования.")
                return

            async with AsyncSession(proxy=proxy_url) as session:
                response = await session.get(url, cookies=cookies, headers=headers)
                if response.status_code == 200:
                    html_content = response.text
                    with open(file_name_html, "w", encoding="utf-8") as file:
                        file.write(html_content)
                    # logger.info(f"Файл сохранен: {file_name_html}")
                    # await asyncio.sleep(5)
                else:
                    logger.error(f"Ошибка {response.status_code} при загрузке {url}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке {url} через прокси {proxy_url}: {e}")


async def get_html_for_site(directory, url, id_link):
    """
    Управление процессом загрузки HTML для указанного сайта.

    - Определяет настройки cookies и headers для каждого поддерживаемого сайта.
    - Вызывает fetch_and_save_html для загрузки и сохранения HTML страницы.

    Добавление нового сайта:
    - Добавьте новое условие для вашего сайта, используя название директории.
    - Определите cookies и headers, необходимые для загрузки страниц с этого сайта.
    - Вызовите fetch_and_save_html с новыми параметрами.
    """
    html_path = os.path.join(directory, "html")
    file_name_html = os.path.join(html_path, f"{id_link}.html")

    if "motodom_ua" in directory:
        cookies = {
            "jrv": "55750",
            "PHPSESSID": "5pfnuqtt1bh94bqaqs9qfv5ctu",
            "default": "imrum01m616km4mgu38a4b0vpr",
            "currency": "UAH",
            "cf_clearance": "u7PFikBy.dJRMui6wRUUCmWA4Wbdu1nvD5FgD36KfvY-1723014419-1.0.1.1-QMhdwCrE.tZv_sGpWTNOXRP_x3OLH_jgX5.QlhvoSNGdK_JOqyi3V2oRHsp7_DbTqy11voEP.pI0u2DVX0V0Gg",
            "language_url": "ru",
            "language": "ru-ru",
        }
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }
        await fetch_and_save_html(url, file_name_html, cookies, headers)

    elif "tireshop_ua" in directory:
        cookies = {
            "language": "ru",
            "_ms": "37997b6d-db6c-4452-b320-cf43fa925144",
            "PHPSESSID": "3t80nt1grucdo6pfdatcin5su2",
            "currency": "UAH",
        }
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
            "cache-control": "no-cache",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }
        await fetch_and_save_html(url, file_name_html, cookies, headers)


async def create_html_and_read_csv():
    """
    Создание HTML-файлов и чтение данных из CSV.

    - Итерирует по поддиректориям в папке temp.
    - Загружает JSON данные из out.json и извлекает ссылки.
    - Запускает процесс загрузки HTML для каждого сайта.

    Добавление нового сайта:
    - Убедитесь, что структура JSON в out.json соответствует ожиданиям.
    - Функция автоматически поддерживает новый сайт, если он добавлен в get_html_for_site.
    """
    for directory in os.listdir(temp_path):
        subdir_path = os.path.join(temp_path, directory)
        if os.path.isdir(subdir_path):
            html_path = os.path.join(subdir_path, "html")
            os.makedirs(html_path, exist_ok=True)

            json_file_path = os.path.join(subdir_path, "out.json")
            if os.path.exists(json_file_path):
                with open(json_file_path, "r", encoding="utf-8") as json_file:
                    data = json.load(json_file)
                    links = data.get(directory, [])
                    tasks = [
                        get_html_for_site(subdir_path, l["link"], l["id"])
                        for l in links
                    ]
                    await asyncio.gather(*tasks)


async def parse_html(
    dir_path, directory, availability_selector, price_selectors, currency_symbol="грн."
):
    """
    Парсинг HTML-файлов для извлечения данных.

    - Загружает HTML файлы из поддиректорий.
    - Использует CSS-селекторы для извлечения информации о наличии и цене.
    - Сохраняет извлеченные данные в JSON файлы.

    Добавление нового сайта:
    - Определите новые CSS-селекторы для вашего сайта для извлечения данных.
    - Добавьте их в вызов функции parse_html_file.
    """
    subdir_path = os.path.join(dir_path, directory)
    json_out = os.path.join(subdir_path, "out.json")

    async with aiofiles.open(json_out, "r", encoding="utf-8") as file:
        content = await file.read()
        json_data = json.loads(content)

    html_path = os.path.join(subdir_path, "html")
    files_html = glob.glob(os.path.join(html_path, "*.html"))

    for item in files_html:
        id_product = os.path.splitext(os.path.basename(item))[0]
        async with aiofiles.open(item, "r", encoding="utf-8") as file:
            html_content = await file.read()

        tree = HTMLParser(html_content)
        available = None
        price = None

        available_text_node = tree.css_first(availability_selector)
        if available_text_node:
            extracted_text = available_text_node.text(strip=True)
            available = "в наличии" in extracted_text.lower()

        for selector in price_selectors:
            price = extract_price(tree, selector, currency_symbol)
            if price is not None:
                break

        data = {
            "id": id_product,
            "available": available,
            "price": price,
            "err": None,
        }
        result(subdir_path, data)


async def parse_html_file():
    """
    Запуск парсинга для всех поддиректорий.

    - Создает задачи для парсинга HTML файлов для каждого сайта.
    - Выполняет парсинг в асинхронном режиме.

    Добавление нового сайта:
    - Добавьте новый сайт в логике определения availability_selector и price_selectors.
    - Убедитесь, что селекторы корректны для извлечения данных с вашего сайта.
    """
    tasks = [
        parse_html(
            temp_path,
            directory,
            (
                "#product > div.product-stats li span"
                if "motodom_ua" in directory
                else (
                    "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div:nth-child(4) > div:nth-child(2) > div"
                    if "tireshop_ua" in directory
                    else None  # None используется, когда нет условия, соответствующего newsite_ua
                )
            ),
            (
                [
                    "div.price-group > div.product-price",
                    "div.price-group > div.product-price-new",
                ]
                if "motodom_ua" in directory
                else (
                    [
                        "div.d-flex.align-items-center.my-4.product__product-price.product__card-hr > div.product__item-sale > div.product__card-price.price-grn",
                        "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div.d-flex.align-items-center.my-4.product__product-price.product__card-hr > div:nth-child(1) > div",
                        "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div.d-flex.align-items-center.my-4 > div.product__card-total-price.price-grn.gray",
                    ]
                    if "tireshop_ua" in directory
                    else None  # None используется, когда нет условия, соответствующего newsite_ua
                )
            ),
            "грн.",
        )
        for directory in os.listdir(temp_path)
        if os.path.isdir(os.path.join(temp_path, directory))
    ]

    await asyncio.gather(*tasks)


def result(subdir_path, data):
    """
    Сохранение результата парсинга в JSON-файл.

    - Обновляет данные в out.json на основе результатов парсинга.
    - Сохраняет обновленные данные в result.json.
    """
    out_path = os.path.join(subdir_path, "out.json")
    result_path = os.path.join(subdir_path, "result.json")

    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)

        updated = False
        for key, items in json_data.items():
            for item in items:
                if item["id"] == data["id"]:
                    item.update(data)
                    updated = True

        if updated:
            with open(out_path, "w", encoding="utf-8") as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
            with open(result_path, "w", encoding="utf-8") as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
        else:
            logger.warning(f"ID {data['id']} not found in {out_path}")
    else:
        logger.error(f"File {out_path} does not exist.")


def extract_price(tree, selector, currency_symbol="грн."):
    """
    Извлечение цены из HTML.

    - Использует CSS-селектор для поиска элемента цены на странице.
    - Удаляет символ валюты и пробелы из извлеченного текста.
    - Преобразует текст в числовое значение для удобства дальнейшего анализа.
    """
    try:
        node = tree.css_first(selector)
        if node:
            price = node.text(strip=True).replace(" ", "")
            if currency_symbol in price:
                price = price.replace(currency_symbol, "")
            return int(price)
    except ValueError as e:
        logger.error(f"Ошибка конвертации цены: {e}")
    except Exception as e:
        logger.error(f"Ошибка извлечения цены: {e}")
    return None


def get_results():
    """
    Объединение всех результатов в один файл.

    - Собирает данные из всех result.json в поддиректориях.
    - Объединяет данные в один файл result.json в корневой директории.
    """
    combined_data = {}

    for directory in os.listdir(temp_path):
        subdir_path = os.path.join(temp_path, directory)
        json_file_path = os.path.join(subdir_path, "result.json")

        if os.path.isfile(json_file_path):
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                combined_data.update(data)

    output_file_path = os.path.join(current_directory, "result.json")
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(combined_data, output_file, ensure_ascii=False, indent=4)

    logger.info(f"Объединенный файл сохранен по пути: {output_file_path}")


if __name__ == "__main__":
    get_dir_json()
    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    asyncio.run(create_html_and_read_csv())
    asyncio.run(parse_html_file())
    get_results()
