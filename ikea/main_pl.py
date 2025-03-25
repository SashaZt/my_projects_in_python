# Рабочий код для сбора данных с сайта IKEA
# Скрипт скачивает XML файлы, парсит их, сохраняет URL в CSV файл, скачивает HTML страницы и сохраняет их в папку html
# Дата 21.03.2025
import asyncio
import csv
import hashlib
import json
import math
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger
from playwright.async_api import async_playwright

current_directory = Path.cwd()
xml_directory = current_directory / "xml"
data_directory = current_directory / "data"
log_directory = current_directory / "log"
html_directory = current_directory / "html"

log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
start_xml_path = xml_directory / "sitemap.xml"
all_urls_csv_file = data_directory / "all_urls.csv"
find_urls_csv_file = data_directory / "find_urls.csv"
matches_file = data_directory / "ikea_matches.json"
output_json_file = data_directory / "output.json"
prom_file = current_directory / "Пром.xlsx"
rozetka_file = current_directory / "Розетка.xlsx"
exclusion_file = current_directory / "exclusion_products.txt"
not_found_file = data_directory / "not_found_links.json"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)
# Конфигурация
NUM_WORKERS = 9  # Количество параллельных потоков


headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
}


def download_start_xml():
    cookies = {
        "ikexp_id": "4ae34af6-60c6-4801-89ff-8080a441f26d",
        "ak_bmsc": "63624010FCFAF059993FE3731D18C012~000000000000000000000000000000~YAAQHwxAF05yZa6VAQAAwuC2uBuQuyxHPgi1ZcY9osMYW4hOPNAGPNItdPFFUdZpszT5rKClPsrSTa0HqJjPfjhu1UojeTVNeKoURT/ikcmmsPuXe0q5H8Gv0uCwJGejK/lVzT4B+xy+K1blRrGsPeHHRkAVkJgugqOv+s3bbHPFjy27pZTpk3t3AJ4dql2S6a21EiqxpFlgPYy1N4bYFZ7xLZuO84Now434qDfC3pduUHjOEvBPay/B4h5BQXe/1irzAfnrg1bbkvgFFC8eM8jsG++HjYNtxF/AZkRXLznopx+XweMCP4a+2yndvEzUA1IZloP9dn8Bq/e/WzEt2PV02REAwPoXEV6x85Tgb74u4cXGTopG1NwhKssreNRcuhfm1vavRY8=",
        "ikea_cookieconsent_pl": "%7B%221%22%3Atrue%2C%222%22%3Atrue%2C%223%22%3Atrue%2C%224%22%3Atrue%7D",
        "_fbp": "fb.1.1742560761431.444801568",
        "rtbhouse-split": "1",
        "episod_id": "1742560761504.f4ee1238",
        "BehtarIKEA": "7336e9bf-c5be-4abc-8ce1-f3c50fa4c270",
        "PIM-SESSION-ID": "pzixFKEDlO0aNhE0",
        "weDareSessionId": "5oebr-hrmlk-5jy",
        "_cs_mk_ga": "0.5746547625992453_1742562698666",
        "_abck": "F62F3894666D693DDA831F7A6E61F6B9~0~YAAQHAxAF//qHqmVAQAALavVuA2q8WFMQRBWH43KGH+5Ba1poiVvUoznX3tDuWZ0kWkjiRi6g1TnnlFMB4/tZ5MXLBnYa3nia5XJ/2CvQrXR/EKL0X61gTC03nghSnphF5QCC2rlwPmVpcvQk8UcG/fVJ9oH2QhSfUIOAwKH9xpb8+QJOMeYVlM9/zreuprbdO0vgS4dOLzhfOrFzSVyUrMXMRiwgSVP9NqbYQlCp2ai52qdwXH9e5ten/twYS9TKTePiUh251nFfcO22w0r/8jzIYGFCDuRtLdq3kImjHgtNkUwF0NteElo746WQhTJEI4mlm839ciKRXDp2tD58GreyT6eIwcpPxE4tmLp/Waqzypf2ek2mAZh7HnwtRZ+GnU1Q+iEYeWEOnBNW9h5T/EpCQbxq8+U8mJ2SeetwZN9ua4HS6aAr/XBWOxkOHKC10eNaGudMj0Ap/Ph4XfhXCDVxpRqqypKiI6VFN38Y2RCiML4Wg48hTY=~-1~-1~1742564350",
        "bm_sz": "6C0ED6E38C0ECA35FB70C981F1ADAE5D~YAAQHAxAF1AcH6mVAQAArt3WuBtwUXBti3t8ORPsEa+dFMMxmYOPPuW6mV9bRo4YAU43ETM+agNUiAjLv2HPh3eGG3iRPib/T1s03gUdXWs2G+vFGjnz9s7jX4W5uNuONMHOK0lVziHXhMm0TVYAwrk5VtVzxTdtraP3H0iEdry7euHhC8TBTXFKmo7wJGGhL2Tmsrir2z5g9Jd9Va+NeR0JLZmrb6zkOZgzDcNEtB4MZFE176DknLRKOibPy1LGjrmkIdF7ZuBoME9RbywxgScsUC2wCsjiKw0oACz1RecoLBuv2HTQIk/XJAsBgqHvkrymGhbvp9lk2wptWfjPe0cKKrP0c2nANArfeKboPNYrtD4wnjHtbDCfjCaLLccWhCcLPzIo1iCQCp5VgEi4j7uNzEctDya8AqqzafUJQ2pG8iptFKEJH/H+lfEQNVClKVxbLvZ+A3QOGYbwvnEiutcq8srawJo0rPg2hRA=~4273222~4342841",
        "bm_sv": "34073B5BB713B0BE4B9D321DCB820AE8~YAAQJAxAF0YyzK+VAQAAT5nauBtZgz5TU1DiJq+Ghr3pgpTkZ417WU3s5T88ORowu8uNdkfZlP9rBE8X6X1dNsj5dX+xV/uzXJxRqIoVmCRpWxiQahl2GDAyRTls4ss4IWu88Evh0+kQXwIKVBg19U8PnwjPPwP1H/NfeTclL3GeO4RD8Nn+0tcUxNgIHzGuN26X+CnEUInsB2UkpbYzgRVHn/UgJCuofQkBsR2BnGhGOuQuZbm9BV1CZ1aGBVmi~1",
        "episod_session_id": "1742560761504.bd3bd789.1.1742563088177",
    }

    response = requests.get(
        "https://www.ikea.com/sitemaps/sitemap.xml",
        cookies=cookies,
        headers=headers,
        timeout=30,
    )

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(start_xml_path, "wb") as file:
            file.write(response.content)
        logger.info(f"Файл успешно сохранен в: {start_xml_path}")
    else:
        logger.error(f"Ошибка при скачивании файла: {response.status_code}")


def parse_start_xml():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    download_start_xml()
    target = "https://www.ikea.com/sitemaps/prod-pl-PL_"
    try:
        # Парсим XML файл
        tree = ET.parse(start_xml_path)
        root = tree.getroot()

        # Определяем пространство имен (namespace), если оно есть
        namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Ищем все теги <url> и извлекаем <loc>
        matching_urls = [
            url.text
            for url in root.findall(".//sitemap:loc", namespace)
            if url.text and target in url.text
        ]
        return matching_urls

    except FileNotFoundError:
        return []


def download_all_xml():
    urls = parse_start_xml()

    cookies = {
        "ikexp_id": "4ae34af6-60c6-4801-89ff-8080a441f26d",
        "ak_bmsc": "63624010FCFAF059993FE3731D18C012~000000000000000000000000000000~YAAQHwxAF05yZa6VAQAAwuC2uBuQuyxHPgi1ZcY9osMYW4hOPNAGPNItdPFFUdZpszT5rKClPsrSTa0HqJjPfjhu1UojeTVNeKoURT/ikcmmsPuXe0q5H8Gv0uCwJGejK/lVzT4B+xy+K1blRrGsPeHHRkAVkJgugqOv+s3bbHPFjy27pZTpk3t3AJ4dql2S6a21EiqxpFlgPYy1N4bYFZ7xLZuO84Now434qDfC3pduUHjOEvBPay/B4h5BQXe/1irzAfnrg1bbkvgFFC8eM8jsG++HjYNtxF/AZkRXLznopx+XweMCP4a+2yndvEzUA1IZloP9dn8Bq/e/WzEt2PV02REAwPoXEV6x85Tgb74u4cXGTopG1NwhKssreNRcuhfm1vavRY8=",
        "ikea_cookieconsent_pl": "%7B%221%22%3Atrue%2C%222%22%3Atrue%2C%223%22%3Atrue%2C%224%22%3Atrue%7D",
        "_fbp": "fb.1.1742560761431.444801568",
        "rtbhouse-split": "1",
        "episod_id": "1742560761504.f4ee1238",
        "BehtarIKEA": "7336e9bf-c5be-4abc-8ce1-f3c50fa4c270",
        "PIM-SESSION-ID": "pzixFKEDlO0aNhE0",
        "weDareSessionId": "5oebr-hrmlk-5jy",
        "_cs_mk_ga": "0.5746547625992453_1742562698666",
        "_abck": "F62F3894666D693DDA831F7A6E61F6B9~0~YAAQHAxAF//qHqmVAQAALavVuA2q8WFMQRBWH43KGH+5Ba1poiVvUoznX3tDuWZ0kWkjiRi6g1TnnlFMB4/tZ5MXLBnYa3nia5XJ/2CvQrXR/EKL0X61gTC03nghSnphF5QCC2rlwPmVpcvQk8UcG/fVJ9oH2QhSfUIOAwKH9xpb8+QJOMeYVlM9/zreuprbdO0vgS4dOLzhfOrFzSVyUrMXMRiwgSVP9NqbYQlCp2ai52qdwXH9e5ten/twYS9TKTePiUh251nFfcO22w0r/8jzIYGFCDuRtLdq3kImjHgtNkUwF0NteElo746WQhTJEI4mlm839ciKRXDp2tD58GreyT6eIwcpPxE4tmLp/Waqzypf2ek2mAZh7HnwtRZ+GnU1Q+iEYeWEOnBNW9h5T/EpCQbxq8+U8mJ2SeetwZN9ua4HS6aAr/XBWOxkOHKC10eNaGudMj0Ap/Ph4XfhXCDVxpRqqypKiI6VFN38Y2RCiML4Wg48hTY=~-1~-1~1742564350",
        "episod_session_id": "1742560761504.bd3bd789.1.1742563088177",
        "bm_sv": "34073B5BB713B0BE4B9D321DCB820AE8~YAAQFwxAF/d/lqiVAQAAxIPduBt4QfzIbqtpFjIX5nJXPN1vx4bSUsqKdhHw34Bn556sW/wDVkhfY0p3pm7nDsmWgMZu5DAAoPiYqKftTfHsuxCKIrqz5oQ2lN04Y9OWLuAD1Kh4vAhN/g0jA8mvDLu+gaASszOqDZSZZgyWEcw1YFcrWiK3cz5zm97yk8tVRq/gD/yZ17zVvmFFZZctWrBHkJP0th75fgI6i5n87mDsaLQDgM1L6jahwALTXmLD~1",
        "bm_sz": "6C0ED6E38C0ECA35FB70C981F1ADAE5D~YAAQFwxAF/h/lqiVAQAAxIPduBscyVdbfLzmjiN6zjXpG/5VYksQLL3n8CrhyDp0CdoOsVGkUePS671Ge54HHfjq401ZbIwBpPb4EOUQ8lwMuZNBMqJC0Z+nINR1AAo5rmKnkkCx0Z1uNg1RX6sMYI8PzXzBo+v3wzplsOEAfyrRvuW9u/um96ogFa6VR7GhreNOovjW/DF03CaxmS3tusAQzQ4bdpo5tognIeMMDsZ+XlnuXe2LQk2brAEqs7TxtXYhqQ3Rqi7rxiD36NsJ8JVdU7QXTjCO/AwMyZQVK9hVoCVgX+qqVByN3H5Rlup8SPvCKV9MiHeq8EatVT8Pw9wj1ZutDYyvIj/3gWzjOV8NdSTPX4EpDgP4l5oUPvIPBtXhpyLWr/Y8HFdLHv+TWbMYvUfs3Ka3wIHxzQ4AH/j0EKEYtcu57Lww/imSo4jVhHZiuec8SQzeSiCUBJUcOzBXC+ofofKINZ8gk8a0OFX/OCafh1xuoQG/lgRTYESBtw==~4273222~4342841",
    }

    for url in urls:

        response = requests.get(
            url,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )
        # Извлечение имени файла из URL с помощью Path
        file_name = Path(urlparse(url).path).name  # Извлекает 'prod-pl-PL_6.xml'
        file_path = xml_directory / file_name  # Формируем полный путь с помощью /
        if file_path.exists():
            logger.info(f"Файл {file_name} уже существует")
            continue
        # Проверка успешности запроса
        if response.status_code == 200:
            # Сохранение содержимого в файл
            with open(file_path, "wb") as file:
                file.write(response.content)
            logger.info(f"Файл успешно сохранен в: {file_path}")
        else:
            logger.error(f"Ошибка при скачивании файла: {response.status_code}")
    parse_all_sitemap_urls()


def parse_all_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in xml_directory.glob("prod*.xml"):
        try:
            # Парсим XML файл
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Определяем пространство имен (namespace), если оно есть
            namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Ищем все теги <url> и извлекаем <loc>
            for url in root.findall(".//sitemap:url", namespace):
                loc = url.find("sitemap:loc", namespace)

                if loc is not None and loc.text:
                    urls.append(loc.text)

        except ET.ParseError as e:
            logger.error(f"Ошибка парсинга XML: {e}")
            return []
        except FileNotFoundError:
            logger.error(f"Файл {xml_file} не найден")
            return []
    logger.info(f"Найдено {len(urls)} URL-ов")
    url_data = pd.DataFrame(urls, columns=["url"])
    url_data.to_csv(all_urls_csv_file, index=False)


async def setup_browser_context():
    """Настройка и инициализация браузера и контекста"""
    p = await async_playwright().start()

    # Запускаем браузер
    browser = await p.chromium.launch(
        headless=True
    )  # headless=True для работы без интерфейса

    # Создаем новый контекст с оптимизациями
    context = await browser.new_context(
        bypass_csp=True,
        java_script_enabled=True,
        permissions=["geolocation"],
        device_scale_factor=1.0,
        has_touch=True,
        ignore_https_errors=True,
    )

    # Отключаем загрузку изображений, шрифтов и других медиафайлов
    await context.route(
        "**/*",
        lambda route, request: (
            route.abort()
            if request.resource_type in ["image", "media", "font", "stylesheet"]
            else route.continue_()
        ),
    )

    # Создаем новую страницу
    page = await context.new_page()

    # Переходим на главную страницу IKEA
    await page.goto("https://www.ikea.com/pl/pl/")

    # Ждем 2 секунды после навигации
    await asyncio.sleep(2)

    # Проверяем наличие кнопки принятия cookies и нажимаем, если она есть
    try:
        cookie_button = await page.wait_for_selector(
            "#onetrust-accept-btn-handler", timeout=5000
        )
        if cookie_button:
            await cookie_button.click()
            # Ждем 2 секунды после нажатия на кнопку cookies
            await asyncio.sleep(2)
    except Exception as e:
        logger.warning(f"Cookie button not found or error clicking it: {e}")

    # Ждем, пока появится элемент с почтовым индексом, и нажимаем на него
    try:
        postal_code_button = await page.wait_for_selector(
            'span:text("Wpisz kod pocztowy")', timeout=10000
        )
        await postal_code_button.click()

        # Ждем 2 секунды после нажатия на кнопку почтового индекса
        await asyncio.sleep(2)

        # Ждем, пока появится поле ввода
        postal_code_input = await page.wait_for_selector(
            'input[aria-describedby="hnf-postalcode-helper"]', timeout=10000
        )

        # Вводим почтовый индекс
        await postal_code_input.fill("22-100")

        # Ждем 2 секунды после заполнения поля ввода
        await asyncio.sleep(2)

        # Нажимаем Enter
        await postal_code_input.press("Enter")

        # Ждем 2 секунды после нажатия Enter
        await asyncio.sleep(2)
    except Exception as e:
        logger.warning(f"Error during postal code setup: {e}")

    return p, browser, context, page


async def process_batch_with_single_browser(urls_batch, worker_id):
    """Обработка пакета URL-адресов с использованием одного экземпляра браузера"""
    logger.info(f"Worker {worker_id}: Starting to process {len(urls_batch)} URLs")

    try:
        # Настраиваем браузер один раз на весь пакет
        p, browser, context, page = await setup_browser_context()
        logger.info(f"Worker {worker_id}: Browser setup completed")

        # Обрабатываем все URL последовательно, используя один экземпляр браузера
        for url in urls_batch:
            output_html_file = (
                html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
            )

            # Если файл уже существует, пропускаем
            if output_html_file.exists():
                logger.debug(
                    f"Worker {worker_id}: File already exists for {url}, skipping"
                )
                continue

            try:
                # Переходим на конкретный URL
                logger.info(f"Worker {worker_id}: Navigating to {url}")
                await page.goto(
                    url, timeout=60000
                )  # Увеличенный таймаут для загрузки страницы

                # Ждем 2 секунды для загрузки страницы
                # await asyncio.sleep(2)

                # Сохраняем HTML-контент
                content = await page.content()
                with open(output_html_file, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info(f"Worker {worker_id}: Saved {url} to {output_html_file}")

            except Exception as e:
                logger.error(f"Worker {worker_id}: Error processing URL {url}: {e}")

        # Закрываем браузер после обработки всех URL в пакете
        await browser.close()
        await p.stop()
        logger.info(f"Worker {worker_id}: Completed processing batch")

    except Exception as e:
        logger.error(f"Worker {worker_id}: Critical error in batch processing: {e}")


async def main_pl():
    # Чтение списка URL из CSV
    urls = []
    try:
        with open(find_urls_csv_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                urls.append(row["url"])
        logger.info(f"Loaded {len(urls)} URLs from CSV")
    except FileNotFoundError:
        logger.error(f"CSV file {find_urls_csv_file} not found.")
        return

    # Разделение URL на пакеты для каждого работника
    batch_size = len(urls) // NUM_WORKERS + (1 if len(urls) % NUM_WORKERS > 0 else 0)
    url_batches = [urls[i : i + batch_size] for i in range(0, len(urls), batch_size)]

    logger.info(f"Processing {len(urls)} URLs with {NUM_WORKERS} workers")
    logger.info(f"Each worker will process approximately {batch_size} URLs")

    # Запускаем обработчики для каждого пакета URL
    tasks = []
    for i, batch in enumerate(url_batches):
        worker_id = i + 1
        tasks.append(process_batch_with_single_browser(batch, worker_id))

    # Ждем завершения всех задач
    await asyncio.gather(*tasks)

    logger.info("All URLs processed")


# Функция для проверки формата кода товара IKEA
def is_valid_ikea_code(code):
    if not isinstance(code, str):
        return False
    # Проверяем формат: цифры.цифры.цифры
    pattern = r"^\d+\.\d+\.\d+$"
    return bool(re.match(pattern, str(code)))


# Функция для преобразования кода IKEA в formated_code (без точек)
def format_ikea_code(code):
    if not isinstance(code, str):
        return None
    # Убираем все точки из кода
    return code.replace(".", "")


# Загрузка и обработка данных из Excel-файлов
def process_excel_files():
    try:
        # Загружаем данные из Пром.xlsx
        logger.info(f"Загрузка файла {prom_file}...")
        prom_df = pd.read_excel(prom_file, sheet_name=0)  # Первый лист

        # Проверяем наличие колонки 'Код_товару'
        if "Код_товару" not in prom_df.columns:
            logger.error(
                f"Внимание: Колонка 'Код_товару' не найдена в {prom_file}. Используем 'A'..."
            )
            # Если колонки с таким названием нет, используем первую колонку
            prom_df = prom_df.rename(columns={prom_df.columns[0]: "Код_товару"})

        # Загружаем данные из Розетка.xlsx
        logger.info(f"Загрузка файла {rozetka_file}...")
        rozetka_df = pd.read_excel(rozetka_file, sheet_name=0)  # Первый лист

        # Проверяем наличие колонки 'Артикул'
        if "Артикул" not in rozetka_df.columns:
            logger.error(
                f"Внимание: Колонка 'Артикул' не найдена в {rozetka_file}. Используем 'D'..."
            )
            # Если колонки нет или она имеет другое название, пробуем колонку D
            try:
                rozetka_df = rozetka_df.rename(
                    columns={rozetka_df.columns[3]: "Артикул"}
                )
            except IndexError:
                logger.error(f"Ошибка: В файле {rozetka_file} нет колонки D.")
                return None

        # Преобразуем все значения в строки для единообразия
        prom_df["Код_товару"] = prom_df["Код_товару"].astype(str)
        rozetka_df["Артикул"] = rozetka_df["Артикул"].astype(str)

        # Создаем словарь для хранения результатов
        result = []

        # Обрабатываем данные из Пром.xlsx
        logger.info("Обработка данных из Пром.xlsx...")
        for idx, row in prom_df.iterrows():
            code = row["Код_товару"]
            is_valid = is_valid_ikea_code(code)
            formatted_code = format_ikea_code(code) if is_valid else None

            item = {
                "id_ikea": code,
                "find_ikea": formatted_code,
                "source": "prom",
                "valid": is_valid,
            }

            if not is_valid:
                logger.error(f"Невалидный код из Пром.xlsx: {code}")

            result.append(item)

        # Обрабатываем данные из Розетка.xlsx
        logger.info("Обработка данных из Розетка.xlsx...")
        for idx, row in rozetka_df.iterrows():
            code = row["Артикул"]
            is_valid = is_valid_ikea_code(code)
            formatted_code = format_ikea_code(code) if is_valid else None

            item = {
                "id_ikea": code,
                "find_ikea": formatted_code,
                "source": "rozetka",
                "valid": is_valid,
            }

            if not is_valid:
                logger.error(f"Невалидный код из Розетка.xlsx: {code}")

            result.append(item)

        # Сохраняем результаты в JSON
        logger.info(f"Сохранение результатов в {output_json_file}...")
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)

        logger.info(f"Обработка завершена. Обработано {len(result)} записей.")
        return result

    except FileNotFoundError as e:
        logger.error(f"Ошибка: Файл не найден - {e}")
    except Exception as e:
        logger.error(f"Ошибка при обработке файлов: {e}")

    return None


# Функция для сопоставления кодов IKEA с URL из CSV с удалением дубликатов
# def match_codes_with_urls(codes_data):
#     if not codes_data:
#         logger.error("Нет данных о кодах для сопоставления.")
#         return

#     try:
#         if not all_urls_csv_file.exists():
#             logger.error(f"Файл {all_urls_csv_file} не найден.")
#             return

#         logger.info(f"Загрузка URL из {all_urls_csv_file}...")
#         urls_df = pd.read_csv(all_urls_csv_file)

#         if "url" not in urls_df.columns:
#             logger.error(f"Колонка 'url' не найдена в {all_urls_csv_file}.")
#             return

#         # Создаем список для хранения совпадений кодов
#         matches = []
#         # Создаем список для хранения найденных URL-адресов
#         find_urls = []

#         # Получаем только валидные коды
#         valid_codes = [item for item in codes_data if item["valid"]]

#         logger.info(f"Найдено {len(valid_codes)} валидных кодов для поиска.")

#         # Для каждого валидного кода ищем соответствующий URL
#         for code_item in valid_codes:
#             formatted_code = code_item["find_ikea"]
#             if not formatted_code:
#                 continue

#             # Ищем URL, содержащий код товара
#             matching_urls = []
#             for url in urls_df["url"]:
#                 if formatted_code in url:
#                     matching_urls.append(url)
#                     find_urls.append({"url": url})

#             if matching_urls:
#                 # Добавляем только информацию о коде (без URL)
#                 matches.append(
#                     {
#                         "id_ikea": code_item["id_ikea"],
#                         "find_ikea": formatted_code,
#                         "source": code_item["source"],
#                     }
#                 )

#         logger.info(f"Найдено {len(matches)} совпадений.")

#         # Сохраняем результаты в JSON
#         logger.info(f"Сохранение результатов в {matches_file}...")
#         with open(matches_file, "w", encoding="utf-8") as f:
#             json.dump(matches, f, ensure_ascii=False, indent=4)

#         # Создаем DataFrame с найденными URL
#         find_urls_df = pd.DataFrame(find_urls)

#         # Удаляем дубликаты URL
#         original_count = len(find_urls_df)
#         find_urls_df = find_urls_df.drop_duplicates(subset=["url"])
#         unique_count = len(find_urls_df)

#         # Логируем информацию об удаленных дубликатах
#         duplicates_removed = original_count - unique_count
#         logger.info(
#             f"Удалено дубликатов URL: {duplicates_removed} ({duplicates_removed/original_count*100:.2f}% от общего числа)"
#         )

#         # Сохраняем только уникальные URL в CSV
#         find_urls_df.to_csv(find_urls_csv_file, index=False)

#         logger.info(
#             f"Сопоставление завершено. Результаты сохранены в {matches_file} и {find_urls_csv_file}."
#         )
#         logger.info(
#             f"В файл {find_urls_csv_file} записано {unique_count} уникальных URL."
#         )

#         return matches, find_urls_df.to_dict("records")


#     except Exception as e:
#         logger.error(f"Ошибка при сопоставлении кодов с URL: {e}")
#         return None, None
def match_codes_with_urls(codes_data):
    if not codes_data:
        logger.error("Нет данных о кодах для сопоставления.")
        return

    try:
        if not all_urls_csv_file.exists():
            logger.error(f"Файл {all_urls_csv_file} не найден.")
            return

        logger.info(f"Загрузка URL из {all_urls_csv_file}...")
        urls_df = pd.read_csv(all_urls_csv_file)

        if "url" not in urls_df.columns:
            logger.error(f"Колонка 'url' не найдена в {all_urls_csv_file}.")
            return

        # Создаем список для хранения совпадений кодов
        matches = []
        # Создаем список для хранения найденных URL-адресов
        find_urls = []
        # Создаем список для хранения ненайденных товаров
        not_found_items = []

        # Получаем только валидные коды
        valid_codes = [item for item in codes_data if item["valid"]]

        logger.info(f"Найдено {len(valid_codes)} валидных кодов для поиска.")

        # Для каждого валидного кода ищем соответствующий URL
        for code_item in valid_codes:
            formatted_code = code_item["find_ikea"]
            if not formatted_code:
                continue

            # Ищем URL, содержащий код товара
            matching_urls = []
            for url in urls_df["url"]:
                if formatted_code in url:
                    matching_urls.append(url)
                    find_urls.append({"url": url})

            if matching_urls:
                # Добавляем только информацию о коде (без URL)
                matches.append(
                    {
                        "id_ikea": code_item["id_ikea"],
                        "find_ikea": formatted_code,
                        "source": code_item["source"],
                    }
                )
            else:
                # Если URL не найден, добавляем в список ненайденных
                not_found_items.append(
                    {
                        "id_ikea": code_item["id_ikea"],
                        "find_ikea": formatted_code,
                        "source": code_item["source"],
                    }
                )

        logger.info(
            f"Найдено {len(matches)} совпадений. Не найдено {len(not_found_items)} товаров."
        )

        # Сохраняем результаты в JSON
        logger.info(f"Сохранение результатов в {matches_file}...")
        with open(matches_file, "w", encoding="utf-8") as f:
            json.dump(matches, f, ensure_ascii=False, indent=4)

        logger.info(f"Сохранение списка ненайденных товаров в {not_found_file}...")
        with open(not_found_file, "w", encoding="utf-8") as f:
            json.dump(not_found_items, f, ensure_ascii=False, indent=4)

        # Создаем DataFrame с найденными URL
        find_urls_df = pd.DataFrame(find_urls)

        # Удаляем дубликаты URL
        original_count = len(find_urls_df)
        find_urls_df = find_urls_df.drop_duplicates(subset=["url"])
        unique_count = len(find_urls_df)

        # Логируем информацию об удаленных дубликатах
        duplicates_removed = original_count - unique_count
        logger.info(
            f"Удалено дубликатов URL: {duplicates_removed} ({duplicates_removed/original_count*100:.2f}% от общего числа)"
        )

        # Сохраняем только уникальные URL в CSV
        find_urls_df.to_csv(find_urls_csv_file, index=False)

        logger.info(
            f"Сопоставление завершено. Результаты сохранены в {matches_file} и {find_urls_csv_file}."
        )
        logger.info(
            f"В файл {find_urls_csv_file} записано {unique_count} уникальных URL."
        )
        logger.info(
            f"В файл {not_found_file} записано {len(not_found_items)} ненайденных товаров."
        )

        return matches, find_urls_df.to_dict("records"), not_found_items

    except Exception as e:
        logger.error(f"Ошибка при сопоставлении кодов с URL: {e}")
        return None, None, None


def pars_htmls():
    logger.info("Собираем данные со страниц html")
    extracted_data = []

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        # 1. Извлечь заголовок продукта
        product_title = soup.find("script", attrs={"id": "pip-range-json-ld"})
        json_string = product_title.string
        json_data = None
        # Убеждаемся, что содержимое не None
        if json_string:
            try:
                # Парсим строку как JSON
                json_data = json.loads(json_string)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при парсинге JSON: {e}")
        mpn = json_data.get("mpn") if json_data else None

        # Извлечение цены
        price = None
        # Сначала пытаемся взять lowPrice
        price = json_data.get("offers", {}).get("lowPrice")
        # Если lowPrice нет (None), берем price
        if price is None:
            price = json_data.get("offers", {}).get("price")

        # Пытаемся найти конкретно элемент с "Sklep - Dostępne w magazynie"
        sklep_element = soup.select_one(
            "div.pip-store-section__button.js-stockcheck-section"
        )

        # Также ищем все элементы со статусом доступности, чтобы в случае отсутствия "Sklep" найти альтернативный
        all_status_elements = soup.select(
            "span.pip-status__label div.pip-store-section__button"
        )

        # Проверяем наличие элемента "Sklep"
        if sklep_element and "Sklep" in sklep_element.text:
            availability_text = sklep_element.text.strip()

        elif all_status_elements:
            # Если не нашли явно "Sklep", но есть другие статусы, используем первый из них
            availability_text = all_status_elements[0].text.strip()
            logger.info(
                f"Файл {mpn}: Найден альтернативный статус: {availability_text}"
            )
        else:
            # Если не найден никакой элемент, попробуем найти похожие
            alt_availability_element = soup.select_one(".pip-status__label")
            if alt_availability_element:
                availability_text = alt_availability_element.text.strip()
                logger.info(
                    f"Файл {mpn}: Найден альтернативный статус: {availability_text}"
                )
            else:
                availability_text = "Статус доступности не найден"
                logger.warning(f"Файл {mpn}: Не удалось найти информацию о доступности")
        # Проверяем, есть ли конкретная фраза "Sklep - Dostępne w magazynie"
        has_in_store = "Sklep - Dostępne w magazynie" in availability_text
        all_data = {
            "mpn": mpn,
            "price": price,
            "product_in_stock": has_in_store,
        }
        logger.info(all_data)
        extracted_data.append(all_data)
    with open(output_json_file, "w", encoding="utf-8") as json_file:
        json.dump(extracted_data, json_file, ensure_ascii=False, indent=4)
    # Добавьте этот вызов
    update_ikea_matches_with_parsed_data(extracted_data)


def update_ikea_matches_with_parsed_data(extracted_data):
    """
    Обновляет данные о товарах в ikea_matches.json, добавляя информацию о цене и наличии.

    Args:
        extracted_data: Список словарей с данными о товарах, полученный из функции pars_htmls()
    """

    # Проверяем, существует ли файл с совпадениями
    if not matches_file.exists():
        logger.error(f"Файл {matches_file} не найден.")
        return

    # Загружаем существующие данные о товарах
    try:
        with open(matches_file, "r", encoding="utf-8") as f:
            ikea_matches = json.load(f)
        logger.info(f"Загружено {len(ikea_matches)} товаров из {matches_file}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке JSON-файла {matches_file}: {e}")
        return

    # Создаем словарь для быстрого поиска данных по MPN
    mpn_to_data = {}
    for item in extracted_data:
        if item["mpn"]:  # Проверяем, что MPN не пустой
            mpn_to_data[item["mpn"]] = item

    logger.info(f"Создан словарь с {len(mpn_to_data)} товарами для поиска по MPN")

    # Счетчики для статистики
    updated_count = 0
    not_found_count = 0

    # Обновляем данные о товарах
    for ikea_item in ikea_matches:
        id_ikea = ikea_item["id_ikea"]

        # Проверяем, есть ли данные для этого MPN
        if id_ikea in mpn_to_data:
            # Извлекаем информацию о наличии и цене
            data_item = mpn_to_data[id_ikea]

            # Добавляем информацию о наличии и цене
            ikea_item["product_in_stock"] = data_item["product_in_stock"]
            ikea_item["price"] = data_item["price"]

            logger.info(
                f"Обновлены данные для товара {id_ikea}: цена={data_item['price']}, наличие={data_item['product_in_stock']}"
            )
            updated_count += 1
        else:
            # Если товар не найден, добавляем флаги о недоступности
            ikea_item["product_in_stock"] = False
            ikea_item["price"] = None
            logger.warning(f"Не найдены данные для товара {id_ikea}")
            not_found_count += 1

    # Сохраняем обновленные данные
    try:
        with open(matches_file, "w", encoding="utf-8") as f:
            json.dump(ikea_matches, f, ensure_ascii=False, indent=4)
        logger.info(
            f"Данные сохранены в {matches_file}. Обновлено: {updated_count}, не найдено: {not_found_count}"
        )
    except Exception as e:
        logger.error(f"Ошибка при сохранении обновленных данных: {e}")


def update_excel_files_with_availability_info(
    exchange_rate_rozetka, exchange_rate_prom
):
    """
    Обновляет файлы Excel на основе данных из ikea_matches.json.

    Для товаров из Розетки:
    - Ищет товар по id_ikea в колонке D (Артикул)
    - Обновляет колонку M (Наявність): "В наявності" или "Не в наявності"
    - Обновляет колонку H (Ціна) с ценой

    Для товаров из Prom:
    - Ищет товар по id_ikea в колонке A (Код_товару)
    - Обновляет колонку P (Наявність): "7" если в наличии, "-" если нет
    - Обновляет колонку I (Ціна) с ценой
    """

    skipped_count = 0
    # Проверяем наличие файлов
    if not matches_file.exists():
        logger.error(f"Файл {matches_file} не найден.")
        return

    if not prom_file.exists():
        logger.error(f"Файл {prom_file} не найден.")
        return

    if not rozetka_file.exists():
        logger.error(f"Файл {rozetka_file} не найден.")
        return
    if not not_found_file.exists():
        logger.error(f"Файл {not_found_file} не найден.")
        return

    # Загружаем данные из ikea_matches.json
    try:
        with open(matches_file, "r", encoding="utf-8") as f:
            ikea_matches = json.load(f)
        logger.info(f"Загружено {len(ikea_matches)} товаров из {matches_file}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке JSON-файла {matches_file}: {e}")
        return
    # Загружаем данные из not_found_file.json
    try:
        with open(not_found_file, "r", encoding="utf-8") as f:
            not_found_items = json.load(f)
        logger.info(f"Загружено {len(not_found_items)} товаров из {not_found_file}")

        # Создаем множество идентификаторов ненайденных товаров для быстрого поиска
        not_found_ids = {item["id_ikea"] for item in not_found_items}

    except Exception as e:
        logger.error(f"Ошибка при загрузке JSON-файла {not_found_file}: {e}")
        return

    # Разделяем товары по источнику
    rozetka_items = [item for item in ikea_matches if item.get("source") == "rozetka"]
    prom_items = [item for item in ikea_matches if item.get("source") == "prom"]

    logger.info(
        f"Товаров для Розетки: {len(rozetka_items)}, для Prom: {len(prom_items)}"
    )
    # Загружаем список исключений
    excluded_products = set()
    if exclusion_file.exists():
        try:
            with open(exclusion_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        excluded_products.add(line)
            logger.info(
                f"Загружено {len(excluded_products)} товаров в список исключений"
            )
        except Exception as e:
            logger.error(f"Ошибка при загрузке списка исключений: {e}")
    else:
        logger.warning(
            f"Файл исключений {exclusion_file} не найден. Продолжаем без исключений."
        )
    # Обновляем файл Розетки
    try:
        # Загружаем Excel файл
        rozetka_df = pd.read_excel(rozetka_file)
        logger.info(f"Загружен файл Розетка.xlsx, размер: {rozetka_df.shape}")

        # Проверяем наличие нужных колонок
        if "Артикул" not in rozetka_df.columns:
            # Если колонки нет или она имеет другое название, пробуем колонку D
            try:
                column_D_name = rozetka_df.columns[3]  # 4-й столбец (индекс 3) - это D
                rozetka_df = rozetka_df.rename(columns={column_D_name: "Артикул"})
                logger.info(f"Переименована колонка D '{column_D_name}' в 'Артикул'")
            except IndexError:
                logger.error(f"В файле {rozetka_file} нет колонки D.")
                return

        # Колонка M (Наявність) - это индекс 12
        availability_column_idx = 12
        availability_column_name = rozetka_df.columns[availability_column_idx]

        # Колонка H (Ціна) - это индекс 7
        price_column_idx = 7
        price_column_name = rozetka_df.columns[price_column_idx]

        logger.info(
            f"Колонка наличия: {availability_column_name} (M), колонка цены: {price_column_name} (H)"
        )

        # Преобразуем артикулы в строки для сравнения
        rozetka_df["Артикул"] = rozetka_df["Артикул"].astype(str)
        # Обработка ненайденных товаров для Розетки
        not_found_rozetka = [
            item for item in not_found_items if item["source"] == "rozetka"
        ]
        not_found_updated_count = 0

        for not_found_item in not_found_rozetka:
            mask = rozetka_df["Артикул"] == not_found_item["id_ikea"]
            if mask.any():
                # Устанавливаем отсутствие и нулевую цену
                rozetka_df.loc[mask, availability_column_name] = "Не в наявності"
                rozetka_df.loc[mask, price_column_name] = 0
                not_found_updated_count += sum(mask)

        # Обновляем данные для каждого товара
        updated_count = 0
        for item in rozetka_items:
            # Находим строки, где Артикул совпадает с id_ikea
            mask = rozetka_df["Артикул"] == item["id_ikea"]
            if mask.any():
                # Обновляем наличие
                avail_value = (
                    "В наявності"
                    if item.get("product_in_stock", False)
                    else "Не в наявності"
                )
                rozetka_df.loc[mask, availability_column_name] = avail_value

                # Обновляем цену, если товар не в списке исключений
                if (
                    item.get("price") is not None
                    and item["id_ikea"] not in excluded_products
                ):
                    price_value = abs(float(item["price"])) * exchange_rate_rozetka
                    price = math.ceil(float(price_value))
                    rozetka_df.loc[mask, price_column_name] = price

                updated_count += sum(mask)

        logger.info(f"Обновлено {updated_count} товаров в файле Розетка.xlsx")

        # Сохраняем обновленный файл
        output_rozetka_file = current_directory / "Розетка_обновленный.xlsx"
        rozetka_df.to_excel(output_rozetka_file, index=False)
        logger.info(f"Обновленный файл сохранен: {output_rozetka_file}")

    except Exception as e:
        logger.error(f"Ошибка при обновлении файла Розетка.xlsx: {e}")

    # Обновляем файл Prom
    try:
        # Загружаем Excel файл
        prom_df = pd.read_excel(prom_file)
        logger.info(f"Загружен файл Пром.xlsx, размер: {prom_df.shape}")

        # Проверяем наличие нужных колонок
        if "Код_товару" not in prom_df.columns:
            # Если колонки нет или она имеет другое название, пробуем колонку A
            try:
                column_A_name = prom_df.columns[0]  # 1-й столбец (индекс 0) - это A
                prom_df = prom_df.rename(columns={column_A_name: "Код_товару"})
                logger.info(f"Переименована колонка A '{column_A_name}' в 'Код_товару'")
            except IndexError:
                logger.error(f"В файле {prom_file} нет колонки A.")
                return

        # Колонка P (Наявність) - это индекс 15
        availability_column_idx = 15
        availability_column_name = prom_df.columns[availability_column_idx]

        # Колонка I (Ціна) - это индекс 8
        price_column_idx = 8
        price_column_name = prom_df.columns[price_column_idx]

        logger.info(
            f"Колонка наличия: {availability_column_name} (P), колонка цены: {price_column_name} (I)"
        )

        # Преобразуем коды товаров в строки для сравнения
        prom_df["Код_товару"] = prom_df["Код_товару"].astype(str)
        not_found_prom = [item for item in not_found_items if item["source"] == "prom"]
        not_found_updated_count_prom = 0

        for not_found_item in not_found_prom:
            mask = prom_df["Код_товару"] == not_found_item["id_ikea"]
            if mask.any():
                # Устанавливаем отсутствие и нулевую цену
                prom_df.loc[mask, availability_column_name] = "-"
                prom_df.loc[mask, price_column_name] = 0
                not_found_updated_count_prom += sum(mask)
        # Обновляем данные для каждого товара
        updated_count = 0
        for item in prom_items:
            # Находим строки, где Код_товару совпадает с id_ikea
            mask = prom_df["Код_товару"] == item["id_ikea"]
            if mask.any():
                # Обновляем наличие
                avail_value = "7" if item.get("product_in_stock", False) else "-"
                prom_df.loc[mask, availability_column_name] = avail_value

                # Обновляем цену, если она есть
                if (
                    item.get("price") is not None
                    and item["id_ikea"] not in excluded_products
                ):

                    price_value = abs(float(item["price"])) * exchange_rate_prom
                    price = math.ceil(float(price_value))
                    prom_df.loc[mask, price_column_name] = price

                updated_count += sum(mask)

        logger.info(f"Обновлено {updated_count} товаров в файле Пром.xlsx")

        # Сохраняем обновленный файл
        output_prom_file = current_directory / "Пром_обновленный.xlsx"
        prom_df.to_excel(output_prom_file, index=False)
        logger.info(f"Обновленный файл сохранен: {output_prom_file}")
        logger.info(
            f"Обновлено {updated_count} товаров в файле Пром.xlsx, пропущено {skipped_count} из списка исключений"
        )

    except Exception as e:
        logger.error(f"Ошибка при обновлении файла Пром.xlsx: {e}")


def main_loop():
    while True:
        # Запрос ввода от пользователя
        print(
            "Введите 1 для загрузки ссылок"
            "\nВведите 2 для загрузки всех товаров"
            "\nВведите 3 для получения отчета в Excel"
            "\nВведите 4 для удаления временных файлов"
            "\nВведите 0 для закрытия программы"
        )
        user_input = int(input("Выберите действие: "))

        if user_input == 1:
            download_all_xml()
            codes_data = process_excel_files()
            match_codes_with_urls(codes_data)
        elif user_input == 2:
            asyncio.run(main_pl())
        elif user_input == 3:
            logger.info("Введите курс для rozetka")
            exchange_rate_rozetka = float(input())
            logger.info("Введите курс для prom")
            exchange_rate_prom = float(input())
            pars_htmls()
            update_excel_files_with_availability_info(
                exchange_rate_rozetka, exchange_rate_prom
            )
        elif user_input == 4:
            if os.path.exists(html_directory):
                shutil.rmtree(html_directory)
            html_directory.mkdir(parents=True, exist_ok=True)
        elif user_input == 0:
            print("Программа завершена.")
            break  # Выход из цикла, завершение программы
        else:
            print("Неверный ввод, пожалуйста, введите корректный номер действия.")


if __name__ == "__main__":
    main_loop()
