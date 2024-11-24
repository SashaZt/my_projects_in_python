import asyncio
import json
import os
import random
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import aiofiles
import pandas as pd
import requests
from configuration.logger_setup import logger
from playwright.async_api import async_playwright
from tqdm import tqdm

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


def read_from_csv(input_csv_file):
    # Загрузка CSV-файла с указанием, что столбец "url" является строкой
    df = pd.read_csv(input_csv_file, dtype={"url": str})
    return df["url"].tolist()


# Функция для сохранения страницы
async def save_page(url):
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
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
        identifier = url.split("/")[-2]
        file_path = html_files_directory / f"{identifier}.html"
        if file_path.exists():
            continue
        # Переход на страницу и ожидание полной загрузки
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        content = await page.content()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        await context.close()
        await browser.close()
        logger.info(f"Страница сохранена: {file_path}")


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
    asyncio.run(save_page(url))


# Функция для выполнения основной логики
def main():

    urls = read_from_csv(output_csv_file)
    process_urls_multithread(urls)


if __name__ == "__main__":
    main()
