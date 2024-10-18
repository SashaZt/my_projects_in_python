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

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
pdf_files_directory = current_directory / "pdf_files"
json_responses_directory = current_directory / "json_responses"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
pdf_files_directory.mkdir(exist_ok=True, parents=True)

output_csv_file = data_directory / "output.csv"
file_json = json_responses_directory / "post_response.json"


# Функция для получения списка URL
def get_urls(file_path):
    df = pd.read_csv(file_path)
    return df.iloc[:, 0].dropna().tolist()


# Функция загрузки списка прокси
def load_proxies():
    file_path = "roman.txt"
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            proxies = [line.strip() for line in file]
        logger.info(f"Загружено {len(proxies)} прокси.")
        return proxies
    else:
        logger.warning(
            "Файл с прокси не найден. Работа будет выполнена локально без прокси."
        )
        return []


# Асинхронная функция для сохранения HTML и получения ссылок по XPath
async def single_html(urls):
    proxies = load_proxies()
    proxy = random.choice(proxies) if proxies else None
    if not proxies:
        logger.info("Прокси не найдено, работа будет выполнена локально.")

    try:
        proxy_config = parse_proxy(proxy) if proxy else None
        async with async_playwright() as p:
            browser = (
                await p.chromium.launch(proxy=proxy_config, headless=False)
                if proxy
                else await p.chromium.launch(headless=False)
            )
            context = await browser.new_context(accept_downloads=True)
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
            for url in urls:
                # Переход на страницу и ожидание полной загрузки
                await page.goto(url, timeout=60000, wait_until="networkidle")

                # Находим элемент "Generar PDF" и кликаем по нему, как только он доступен
                try:
                    await page.wait_for_selector(
                        "span.d-none.d-xs-block:text('Generar PDF')"
                    )
                    await page.click("span.d-none.d-xs-block:text('Generar PDF')")
                except:
                    continue

                # Находим элемент "Todo el documento" и кликаем, как только он доступен
                await page.wait_for_selector(
                    "label.custom-control-label[for='pdf-Todo']"
                )
                await page.click("label.custom-control-label[for='pdf-Todo']")

                # Находим элемент "Continuar" и кликаем, как только он доступен
                await page.wait_for_selector("button#btn-continue-to-pdf")
                await page.click("button#btn-continue-to-pdf")

                # Ожидание формирования PDF и скачивания
                download = await page.wait_for_event("download")
                await download.save_as(
                    pdf_files_directory / download.suggested_filename
                )

            await context.close()
            await browser.close()
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


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


# Функция для выполнения основной логики
def main():
    urls = get_urls(output_csv_file)
    asyncio.run(single_html(urls))


if __name__ == "__main__":
    main()
