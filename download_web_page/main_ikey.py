import asyncio
import csv
import hashlib
import json
import os
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
output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"

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
NUM_WORKERS = 10  # Количество параллельных потоков


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
            print(f"Ошибка парсинга XML: {e}")
            return []
        except FileNotFoundError:
            print(f"Файл {xml_file} не найден")
            return []
    logger.info(f"Найдено {len(urls)} URL-ов")
    url_data = pd.DataFrame(urls, columns=["url"])
    url_data.to_csv(output_csv_file, index=False)


async def process_url(url, semaphore, worker_id):
    """Обработка одного URL"""
    print(f"Worker {worker_id}: Processing {url}")

    output_html_file = (
        html_directory / f"html_{hashlib.md5(url.encode()).hexdigest()}.html"
    )

    # Если файл уже существует, пропускаем
    if output_html_file.exists():
        print(f"Worker {worker_id}: File already exists for {url}, skipping")
        return

    # Используем семафор для ограничения числа одновременно запущенных браузеров
    async with semaphore:
        try:
            async with async_playwright() as p:
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
                        if request.resource_type
                        in ["image", "media", "font", "stylesheet"]
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
                except:
                    # Если кнопка не существует или истекло время ожидания, продолжаем скрипт
                    pass

                # Ждем, пока появится элемент с почтовым индексом, и нажимаем на него
                postal_code_button = await page.wait_for_selector(
                    'span:text("Wpisz kod pocztowy")'
                )
                await postal_code_button.click()

                # Ждем 2 секунды после нажатия на кнопку почтового индекса
                await asyncio.sleep(2)

                # Ждем, пока появится поле ввода
                postal_code_input = await page.wait_for_selector(
                    'input[aria-describedby="hnf-postalcode-helper"]'
                )

                # Вводим почтовый индекс
                await postal_code_input.fill("22-100")

                # Ждем 2 секунды после заполнения поля ввода
                await asyncio.sleep(2)

                # Нажимаем Enter
                await postal_code_input.press("Enter")

                # Ждем 2 секунды после нажатия Enter
                await asyncio.sleep(2)

                # Теперь переходим на конкретный URL
                print(f"Worker {worker_id}: Navigating to {url}")
                await page.goto(url)

                # Ждем 2 секунды для загрузки страницы
                await asyncio.sleep(2)

                # Сохраняем HTML-контент
                content = await page.content()
                with open(output_html_file, "w", encoding="utf-8") as f:
                    f.write(content)

                print(f"Worker {worker_id}: Saved {url} to {output_html_file}")

                # Закрываем браузер
                await browser.close()

        except Exception as e:
            print(f"Worker {worker_id}: Error processing {url}: {e}")


async def process_batch(urls_batch, semaphore, worker_id):
    """Обработка пакета URL-адресов"""
    tasks = []
    for url in urls_batch:
        tasks.append(process_url(url, semaphore, worker_id))

    await asyncio.gather(*tasks)


async def main():
    # Чтение списка URL из CSV
    urls = []
    try:
        with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                urls.append(row["url"])
    except FileNotFoundError:
        print(f"CSV file {output_csv_file} not found. Using test URLs.")
        # Тестовые URL, если CSV-файл не найден

    # Разделение URL на пакеты для каждого работника
    batch_size = len(urls) // NUM_WORKERS + (1 if len(urls) % NUM_WORKERS > 0 else 0)
    url_batches = [urls[i : i + batch_size] for i in range(0, len(urls), batch_size)]

    print(f"Processing {len(urls)} URLs with {NUM_WORKERS} workers")
    print(f"Each worker will process approximately {batch_size} URLs")

    # Создаем семафор для ограничения числа одновременных сессий браузера
    semaphore = asyncio.Semaphore(NUM_WORKERS)

    # Запускаем обработчики для каждого пакета URL
    tasks = []
    for i, batch in enumerate(url_batches):
        worker_id = i + 1
        tasks.append(process_batch(batch, semaphore, worker_id))

    # Ждем завершения всех задач
    await asyncio.gather(*tasks)

    print("All URLs processed")


if __name__ == "__main__":
    asyncio.run(main())
