import re
import json
from pathlib import Path
import csv
import aiofiles
import glob
import asyncio
from selectolax.parser import HTMLParser
from curl_cffi.requests import AsyncSession
from asyncio import WindowsSelectorEventLoopPolicy
from configuration.logger_setup import logger
import random
import shutil
import sys
from playwright.async_api import async_playwright

# Получаем текущую директорию
current_directory = Path.cwd()

# Создаем путь к директории "temp"
temp_path = current_directory / "temp"

# Создание директории, если она не существует
temp_path.mkdir(parents=True, exist_ok=True)


def del_temp():
    temp_path = current_directory / "temp"
    # Используем pathlib для представления пути
    temp_path = Path(temp_path)

    # Проверяем, существует ли директория, перед удалением
    if temp_path.exists() and temp_path.is_dir():
        try:
            # Рекурсивно удаляем директорию temp и все её содержимое
            shutil.rmtree(temp_path)
            logger.info(f"Директория {temp_path} успешно удалена.")
        except Exception as e:
            logger.error(f"Ошибка при удалении директории {temp_path}: {e}")
    else:
        logger.debug(f"Директория {temp_path} не существует.")


def get_dir_json():
    """
    Создание директорий и файлов JSON из out.json.

    - Загружает файл out.json, содержащий данные для разных сайтов.
    - Создает поддиректории для каждого сайта в папке temp.
    - Сохраняет данные для каждого сайта в отдельный out.json в соответствующей поддиректории.
    """
    # Загружаем данные из out.json
    with open("out.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Определяем путь к временной директории
    temp_path = Path.cwd() / "temp"

    # Проходим по ключам данных
    for key in data.keys():
        # Создаем поддиректорию для каждого сайта
        dir_path = temp_path / key
        dir_path.mkdir(parents=True, exist_ok=True)

        # Записываем данные в out.json в поддиректории
        with open(dir_path / "out.json", "w", encoding="utf-8") as outfile:
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
    # Определяем путь к временной директории
    temp_path = Path.cwd() / "temp"

    # Проходим по всем поддиректориям
    for subdir in temp_path.iterdir():
        if subdir.is_dir():
            json_file_path = subdir / "out.json"
            csv_file_path = subdir / "out.csv"

            all_links = []

            if json_file_path.exists():
                with open(json_file_path, "r", encoding="utf-8") as json_file:
                    try:
                        data = json.load(json_file)
                        for key, value in data.items():
                            # Извлечение всех ссылок из каждого ключа
                            links = value if isinstance(value, list) else []
                            for l in links:
                                all_links.append(l.get("link", ""))
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка при загрузке {json_file_path}: {e}")

            with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)
                for link in all_links:
                    writer.writerow([link])

            logger.info(f"Ссылки сохранены в {csv_file_path}")


def get_random_proxy():
    """
    Возвращает случайный прокси из файла proxi.json.

    - Загружает список прокси из файла proxi.json.
    - Выбирает случайный прокси из списка.
    - Форматирует прокси для использования в HTTP-запросах.
    - Если файл отсутствует или содержит некорректные данные, завершает выполнение программы.
    """
    proxies_path = Path("configuration") / "proxi.json"

    try:
        with open(proxies_path, "r", encoding="utf-8") as proxy_file:
            proxies = json.load(proxy_file)

        if not proxies:
            logger.error("Файл proxi.json пуст или не содержит корректных данных.")
            sys.exit(
                "Программа завершена из-за отсутствия корректных данных в proxi.json."
            )

        proxy = random.choice(proxies)

        # Проверяем корректность формата прокси
        if len(proxy) < 4:
            logger.error("Некорректный формат прокси в файле proxi.json.")
            sys.exit("Программа завершена из-за некорректного формата прокси.")

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
    file_path = Path(file_name_html)

    if not file_path.exists():
        try:
            proxy_url = get_random_proxy()
            if proxy_url is None:
                logger.error("Нет доступных прокси для использования.")
                return

            async with AsyncSession(proxy=proxy_url) as session:
                response = await session.get(url, cookies=cookies, headers=headers)
                if response.status_code == 200:
                    html_content = response.text
                    file_path.write_text(html_content, encoding="utf-8")
                    logger.info(f"Файл сохранен: {file_name_html}")
                    await asyncio.sleep(
                        5
                    )  # Задержка для предотвращения быстрого повторного запроса
                else:
                    logger.error(f"Ошибка {response.status_code} при загрузке {url}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке {url} через прокси {proxy_url}: {e}")


async def get_html_for_site(directory, url, id_link):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }
    """
    Управление процессом загрузки HTML для указанного сайта.

    - Определяет настройки cookies и headers для каждого поддерживаемого сайта.
    - Вызывает fetch_and_save_html для загрузки и сохранения HTML страницы.

    Добавление нового сайта:
    - Добавьте новое условие для вашего сайта, используя название директории.
    - Определите cookies и headers, необходимые для загрузки страниц с этого сайта.
    - Вызовите fetch_and_save_html с новыми параметрами.
    """
    # Создаем путь к директории "html"
    html_path = Path(directory) / "html"
    logger.info(html_path)
    exit()

    # Создаем путь к файлу HTML с использованием идентификатора ссылки
    file_name_html = html_path / f"{id_link}.html"

    if "motodom_ua" in directory:

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
    temp_path = Path.cwd() / "temp"

    # Итерируем по всем поддиректориям в temp
    for subdir in temp_path.iterdir():
        if subdir.is_dir():
            html_path = subdir / "html"
            html_path.mkdir(
                exist_ok=True
            )  # Создание директории "html", если не существует

            json_file_path = subdir / "out.json"
            if json_file_path.exists():
                with json_file_path.open("r", encoding="utf-8") as json_file:
                    try:
                        data = json.load(json_file)
                        links = data.get(subdir.name, [])
                        tasks = [
                            get_html_for_site(subdir, l["link"], l["id"]) for l in links
                        ]
                        await asyncio.gather(*tasks)
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка при загрузке {json_file_path}: {e}")


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
    subdir_path = Path(dir_path) / directory
    json_out = subdir_path / "out.json"

    async with aiofiles.open(json_out, "r", encoding="utf-8") as file:
        content = await file.read()
        json_data = json.loads(content)

    html_path = subdir_path / "html"
    files_html = html_path.glob("*.html")

    for html_file in files_html:
        id_product = html_file.stem
        async with aiofiles.open(html_file, "r", encoding="utf-8") as file:
            html_content = await file.read()

        tree = HTMLParser(html_content)
        available = None
        price = None

        # Извлечение информации о наличии
        available_text_node = tree.css_first(availability_selector)
        if available_text_node:
            extracted_text = available_text_node.text(strip=True)
            available = "в наличии" in extracted_text.lower()

        # Извлечение цены
        for selector in price_selectors:
            price = extract_price(tree, selector, currency_symbol)
            if price is not None:
                break

        # Сохранение результатов
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
    temp_path = Path("temp")

    # Создание задач для парсинга HTML
    tasks = [
        parse_html(
            temp_path,
            directory.name,
            (
                "#product > div.product-stats li span"
                if "motodom_ua" in directory.name
                else (
                    "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div:nth-child(4) > div:nth-child(2) > div"
                    if "tireshop_ua" in directory.name
                    else None  # None используется, когда нет условия, соответствующего newsite_ua
                )
            ),
            (
                [
                    "div.price-group > div.product-price",
                    "div.price-group > div.product-price-new",
                ]
                if "motodom_ua" in directory.name
                else (
                    [
                        "div.d-flex.align-items-center.my-4.product__product-price.product__card-hr > div.product__item-sale > div.product__card-price.price-grn",
                        "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div.d-flex.align-items-center.my-4.product__product-price.product__card-hr > div:nth-child(1) > div",
                        "div.flex-column.flex-grow-1.ms-0.ms-lg-4.product-calc > div.d-flex.align-items-center.my-4 > div.product__card-total-price.price-grn.gray",
                    ]
                    if "tireshop_ua" in directory.name
                    else None  # None используется, когда нет условия, соответствующего newsite_ua
                )
            ),
            "грн.",
        )
        for directory in temp_path.iterdir()
        if directory.is_dir()
    ]

    await asyncio.gather(*tasks)


def result(subdir_path, data):
    """
    Сохранение результата парсинга в JSON-файл.

    - Обновляет данные в out.json на основе результатов парсинга.
    - Сохраняет обновленные данные в result.json.
    """
    subdir_path = Path(subdir_path)
    out_path = subdir_path / "out.json"
    result_path = subdir_path / "result.json"

    if out_path.exists():
        with out_path.open("r", encoding="utf-8") as file:
            json_data = json.load(file)

        updated = False
        for key, items in json_data.items():
            for item in items:
                if item["id"] == data["id"]:
                    item.update(data)
                    updated = True

        if updated:
            with out_path.open("w", encoding="utf-8") as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
            with result_path.open("w", encoding="utf-8") as file:
                json.dump(json_data, file, ensure_ascii=False, indent=4)
            logger.info(f"Data for ID {data['id']} updated and saved.")
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

    # Путь к временной директории
    temp_path = Path.cwd() / "temp"

    # Проход по всем поддиректориям
    for subdir in temp_path.iterdir():
        if subdir.is_dir():
            json_file_path = subdir / "result.json"

            if json_file_path.is_file():
                with json_file_path.open("r", encoding="utf-8") as json_file:
                    data = json.load(json_file)
                    combined_data.update(data)

    # Путь к выходному файлу
    output_file_path = Path.cwd() / "result.json"

    # Запись объединенных данных в файл
    with output_file_path.open("w", encoding="utf-8") as output_file:
        json.dump(combined_data, output_file, ensure_ascii=False, indent=4)

    logger.info(f"Объединенный файл сохранен по пути: {output_file_path}")


# Сохранение куков в JSON файл в указанную директорию
async def save_cookies_to_file(cookies, directory, filename="cookies.json"):
    # Путь к файлу в формате temp/directory/filename
    file_path = Path("temp") / directory / filename

    # Создаем все промежуточные директории, если они не существуют
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Сохраняем куки в файл
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(cookies, file, indent=4)
    logger.info(f"Cookies saved to {file_path}")


# Обработка куков в формат словаря
def process_cookies(raw_cookies):
    cookies_dict = {cookie["name"]: cookie["value"] for cookie in raw_cookies}
    return cookies_dict


# Функция для получения куков с URL
async def fetch_cookies(page, url):
    logger.info(f"Fetching cookies from {url}")
    try:
        await page.goto(url)
        await asyncio.sleep(2)  # Немногое ожидание для загрузки страницы

        # Определяем селекторы для кнопок
        button_selector_1 = "#thankYouForm_top > div.row > button.btn.btn-outline-primary.btn-language-ru.btn-sm"
        button_selector_2 = (
            "#offcanvastCookie > div.offcanvas-body.small > div > button"
        )

        # Кликаем первую кнопку, если она существует
        button1 = await page.query_selector(button_selector_1)
        if button1:
            await button1.click()
            logger.info("Clicked the first button")

        # Кликаем вторую кнопку, если она существует
        button2 = await page.query_selector(button_selector_2)
        if button2:
            await button2.click()
            logger.info("Clicked the second button")

        # Если ни одна кнопка не найдена, выводим сообщение
        if not button1 and not button2:
            logger.info("No buttons found to click")

        # Ожидание, чтобы изменения от кликов вступили в силу
        await asyncio.sleep(3)

        raw_cookies = await page.context.cookies()
        logger.info(f"Cookies fetched successfully from {url}")
        return process_cookies(raw_cookies)
    except Exception as e:
        logger.error(f"Failed to fetch cookies from {url}: {e}")
        return {}


# Основная функция
async def main():
    # Пример использования
    urls_with_directories = {
        "bikermarket_com_ua": "https://bikermarket.com.ua/ua/",
        "liquimoly_com_ua": "https://liqui-moly.com.ua/",
        "motodom_ua": "https://motodom.ua/",
        "motokvartal_com_ua": "https://motokvartal.com.ua/",
        "motomotion_com_ua": "https://moto-motion.com.ua/ru/",
        "motostyle_ua": "https://motostyle.ua/",
        "tireshop_ua": "https://tireshop.ua/",
    }

    for directory, url in urls_with_directories.items():
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            cookies = await fetch_cookies(page, url)
            if cookies:
                await save_cookies_to_file(cookies, directory)
            else:
                logger.warning(f"No cookies saved for {url}")

            await browser.close()
            logger.info("Browser closed")


if __name__ == "__main__":
    # del_temp()
    # get_dir_json()
    # asyncio.run(main())

    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    asyncio.run(create_html_and_read_csv())
    # asyncio.run(parse_html_file())
    # get_results()
