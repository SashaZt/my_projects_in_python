import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright
import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
import os

import shutil
import json

# Путь к папкам
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"

html_files_directory.mkdir(exist_ok=True, parents=True)

output_csv_file = data_directory / "output.csv"


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


# Асинхронная функция для сохранения HTML и получения ссылок по XPath
async def single_html_one():
    logger.info("Начало работы скрипта")
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
            inns = [
                "JBLT720BTBLU",
                "JBLT720BTPUR",
                "JBLT720BTWHT",
                "JBLT770NCBLK",
                "JBLT770NCBLU",
                "JBLT770NCPUR",
            ]
            for inn in inns:
                url = f"https://hotline.ua/ua/sr/?q={inn}"
                # Переход на страницу и ожидание полной загрузки
                await page.goto(url, timeout=60000, wait_until="networkidle")
                await page.wait_for_selector("text=Порівняти Ціни", timeout=60000)
                await page.click("text=Порівняти Ціни")
                # Ожидание появления необходимого элемента
                await page.wait_for_selector(
                    "#__layout > div > div.default-layout__content-container > div:nth-child(3) > div.container > div.header > div.title > h1",
                    timeout=60000,
                )

                # Сохранение HTML контента
                content = await page.content()
                html_file_path = html_files_directory / f"{inn}.html"
                with open(html_file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            await context.close()
            await browser.close()
            logger.info("Конец работы скрипта")
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


def parsing_html():
    all_data = []
    for html_file in html_files_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content: str = file.read()
        soup = BeautifulSoup(content, "lxml")
        script_tag = soup.find_all("script", attrs={"type": "application/ld+json"})
        if script_tag:
            try:
                json_data = json.loads(script_tag[1].string)
                sku = json_data["sku"]
                url = json_data["url"]
                name = json_data["name"]
                data = {"name": name, "sku": sku, "url": url}
                all_data.append(data)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка при разборе JSON в файле {html_file.name}: {e}")
    df = pd.DataFrame(all_data)

    # Сохраняем DataFrame в Excel файл
    df.to_excel("output_xlsx_file.xlsx", index=False)
    shutil.rmtree(html_files_directory)


# Функция для выполнения основной логики
def main():

    # asyncio.run(single_html_one())
    parsing_html()


if __name__ == "__main__":
    main()
