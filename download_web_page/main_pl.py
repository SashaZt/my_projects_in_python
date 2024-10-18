import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from playwright.async_api import async_playwright
import pandas as pd
from tqdm import tqdm
from configuration.logger_setup import logger
import xml.etree.ElementTree as ET
import re
import aiofiles
import json
import os
import requests
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
xml_files_directory = current_directory / "xml_files"
json_responses_directory = current_directory / "json_responses"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
xml_files_directory.mkdir(exist_ok=True, parents=True)

output_csv_file = data_directory / "output.csv"
file_json = json_responses_directory / "post_response.json"


# Функция загрузки списка прокси
def load_proxies():
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


# Функция для получения списка URL
def get_urls(file_path):
    df = pd.read_csv(file_path)
    return df.iloc[:, 0].dropna().tolist()


# Функция для сохранения страницы
async def save_page(url, proxy):
    try:
        if "@" in proxy:
            protocol, rest = proxy.split("://", 1)
            credentials, server = rest.split("@", 1)
            username, password = credentials.split(":", 1)
            proxy_config = {
                "server": f"{protocol}://{server}",
                "username": username,
                "password": password,
            }
        else:
            proxy_config = {"server": f"http://{proxy}"}

        async with async_playwright() as p:
            browser = await p.chromium.launch(proxy=proxy_config, headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Отключаем медиа
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )

            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            content = await page.content()
            html_file_path = (
                html_files_directory / f"{url.replace(':', '').replace('/', '_')}.html"
            )
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            await context.close()
            await browser.close()
            logger.info(f"Страница сохранена: {html_file_path}")
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {e}")


# Асинхронная функция для сохранения HTML и получения ссылок по XPath
async def single_html():
    url = "https://sede.agenciatributaria.gob.es/Sede/search.html?q=instrucciones%20detalladas%20sobre%20declaraciones%20de%20impuestos&&pilimitzzz=220"
    proxies = load_proxies()
    proxy = random.choice(proxies)
    try:
        proxy_config = parse_proxy(proxy)
        async with async_playwright() as p:
            browser = await p.chromium.launch(proxy=proxy_config, headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Отключаем медиа
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )

            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="networkidle")

            # Находим все ссылки по заданному XPath
            elements = await page.locator(
                "//a[@class='stretched-link text-primary text-decoration-none card-hover-link text-break']"
            ).all()
            hrefs = set()
            for element in elements:
                href = await element.get_attribute("href")
                if href and href.endswith(".html"):
                    hrefs.add(href)

            await context.close()
            await browser.close()
            write_csv(hrefs)
            return hrefs
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {e}")
        return set()


# Основная функция
async def log_post_response(response):
    if (
        response.request.method == "POST"
        and "https://sede.agenciatributaria.gob.es/se_search_internetv2_es/_search/template"
        in response.url
    ):
        try:
            json_response = await response.json()
            await save_response_json(json_response, file_json)
            logger.info(f"POST response saved to {file_json}")
        except Exception as e:
            logger.error(f"Failed to process POST response: {e}")


# Асинхронная функция для сохранения HTML и получения JSON ответов
async def single_html_json():
    url = "https://sede.agenciatributaria.gob.es/Sede/search.html?q=instrucciones%20detalladas%20sobre%20declaraciones%20de%20impuestos&&pilimitzzz=220"
    proxies = load_proxies()
    proxy = random.choice(proxies)
    counter = 1  # Предполагаем, что счетчик инициализируется здесь
    path_json_GamePal = "json_responses"  # Папка для сохранения JSON
    os.makedirs(
        path_json_GamePal, exist_ok=True
    )  # Создаем папку, если она не существует

    try:
        proxy_config = parse_proxy(proxy)
        async with async_playwright() as p:
            browser = await p.chromium.launch(proxy=proxy_config, headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            page.on("response", log_post_response)

            # Отключаем медиа
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media"]
                    else route.continue_()
                ),
            )

            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="networkidle")

            await context.close()
            await browser.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {e}")
        return set()


# Асинхронная функция для сохранения JSON-данных в файл
async def save_response_json(json_response, file_path):
    async with aiofiles.open(file_path, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(json_response, ensure_ascii=False, indent=4))


# Функция для парсинга прокси
def parse_proxy(proxy):
    if "@" in proxy:
        protocol, rest = proxy.split("://", 1)
        credentials, server = rest.split("@", 1)
        username, password = credentials.split(":", 1)
        return {
            "server": f"{protocol}://{server}",
            "username": username,
            "password": password,
        }
    else:
        return {"server": f"http://{proxy}"}


# Функция для сохранения страницы sitemap через Playwright
async def save_sitemap_with_playwright(url, proxy):
    try:
        if "@" in proxy:
            protocol, rest = proxy.split("://", 1)
            credentials, server = rest.split("@", 1)
            username, password = credentials.split(":", 1)
            proxy_config = {
                "server": f"{protocol}://{server}",
                "username": username,
                "password": password,
            }
        else:
            proxy_config = {"server": f"http://{proxy}"}

        async with async_playwright() as p:
            browser = await p.chromium.launch(proxy=proxy_config, headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            content = await page.content()
            sitemap_file_path = xml_files_directory / "sitemap.xml"
            with open(sitemap_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            await context.close()
            await browser.close()
            logger.info(f"Sitemap сохранен: {sitemap_file_path}")
    except Exception as e:
        logger.error(f"Ошибка при обработке {url}: {e}")


# Функция для парсинга всех loc из sitemap.xml
def parsing_all_sitemap(content):
    root = ET.fromstring(content)
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = root.findall(".//ns:loc", namespace)
    return [loc.text for loc in locations]


# Функция для сохранения всех sitemap-*.xml
async def save_additional_sitemaps(locations, proxy):
    try:
        if "@" in proxy:
            protocol, rest = proxy.split("://", 1)
            credentials, server = rest.split("@", 1)
            username, password = credentials.split(":", 1)
            proxy_config = {
                "server": f"{protocol}://{server}",
                "username": username,
                "password": password,
            }
        else:
            proxy_config = {"server": f"http://{proxy}"}

        async with async_playwright() as p:
            browser = await p.chromium.launch(proxy=proxy_config, headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            for loc in locations:
                if "sitemap-" in loc:
                    await page.goto(loc, timeout=60000, wait_until="domcontentloaded")
                    content = await page.content()
                    sitemap_name = loc.split("/")[-1]
                    sitemap_file_path = xml_files_directory / sitemap_name
                    with open(sitemap_file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logger.info(f"Дополнительный sitemap сохранен: {sitemap_file_path}")

            await context.close()
            await browser.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке sitemap: {e}")


# Функция для многопоточной обработки URL
def process_urls_multithread(urls, max_workers=2):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_url, url)
            for url in tqdm(urls, desc="Обработка URL")
        ]
        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"Ошибка в потоке: {e}")


# Функция для обработки URL
def process_url(url):
    proxies = load_proxies()
    proxy = random.choice(proxies)
    asyncio.run(save_page(url, proxy))


# Функция для чтения всех XML из xml_files_directory и извлечения ссылок по шаблонам
def extract_links_from_xml():
    extracted_links = set()
    for xml_file in xml_files_directory.glob("*.xml"):
        with open(xml_file, "r", encoding="utf-8") as f:
            content = f.read()
            links = re.findall(r'https://home-club.com.ua/ua/sku[^\s<>"]+', content)
            links += re.findall(r'https://home-club.com.ua/ua/ikea[^\s<>"]+', content)
            extracted_links.update(links)
    return list(extracted_links)


def write_csv(extracted_links):
    df = pd.DataFrame(extracted_links, columns=["url"])
    df.to_csv(output_csv_file, index=False)
    logger.info(f"Ссылки записаны в файл: {output_csv_file}")


# Функция для выполнения основной логики
def main():
    # asyncio.run(single_html())
    asyncio.run(single_html_json())
    sitemap_url = "https://home-club.com.ua/sitemap.xml"
    proxies = load_proxies()
    proxy = random.choice(proxies)
    asyncio.run(save_sitemap_with_playwright(sitemap_url, proxy))

    sitemap_content_path = xml_files_directory / "sitemap.xml"
    if sitemap_content_path.exists():
        with open(sitemap_content_path, "r", encoding="utf-8") as f:
            sitemap_content = f.read()
        all_locations = parsing_all_sitemap(sitemap_content)
        asyncio.run(save_additional_sitemaps(all_locations, proxy))

    extracted_links = extract_links_from_xml()
    logger.info(f"Извлечено {len(extracted_links)} ссылок по шаблонам.")

    df = pd.DataFrame(extracted_links, columns=["url"])
    df.to_csv(output_csv_file, index=False)
    logger.info(f"Ссылки записаны в файл: {output_csv_file}")

    urls = get_urls(output_csv_file)
    process_urls_multithread(urls)


if __name__ == "__main__":
    main()
