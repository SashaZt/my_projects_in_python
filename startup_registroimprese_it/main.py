import asyncio
from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser
from pathlib import Path
import pandas as pd
from configuration.logger_setup import logger
import aiofiles
import glob
import json
import csv
from playwright.async_api import async_playwright
import random

# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
html_directory = temp_path / "html"
pages_directory = temp_path / "pages"
data_directory = current_directory / "data"


html_directory.mkdir(parents=True, exist_ok=True)
pages_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)


# Функция для загрузки прокси из JSON файла
def load_proxies():
    filename = "proxi.json"
    with open(filename, "r") as f:
        return json.load(f)


# Генератор для итерации по списку прокси
def proxy_generator(proxies):
    num_proxies = len(proxies)
    index = 0
    while True:
        proxy = proxies[index]
        yield proxy
        index = (index + 1) % num_proxies


# Асинхронная функция для сохранения HTML-страницы
async def save_html(page_content, directory: Path, file_counter: int):
    file_name = f"page_{file_counter}.html"
    file_path = directory / file_name
    async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
        await file.write(page_content)
    logger.info(f"HTML сохранен в: {file_path}")


async def handle_pagination(page, pages_directory):
    file_counter = 1

    while True:
        # Сохранение текущей страницы
        logger.info(f"Сохранение страницы {file_counter}")
        page_content = await page.content()
        await save_html(page_content, pages_directory, file_counter)
        file_counter += 1

        # Проверка доступности кнопки "Перейти на последнюю страницу" через ID
        logger.info("Проверка доступности кнопки 'Перейти на последнюю страницу' по ID")

        last_page_button_locator = page.locator("#id3c")

        # Проверяем, доступна ли кнопка (не имеет атрибута disabled)
        last_page_button_disabled = await last_page_button_locator.get_attribute(
            "disabled"
        )

        if last_page_button_disabled == "disabled":
            logger.info("Последняя страница достигнута.")
            break

        # Если кнопка "Перейти на следующую страницу" доступна, нажимаем на неё
        logger.info(f"Переход на следующую страницу {file_counter}")
        await page.locator("#id3b").click()
        await asyncio.sleep(20)  # Пауза после перехода на следующую страницу


# Асинхронная функция для загрузки страницы и взаимодействия с ней
async def download_pages(url):
    async with async_playwright() as playwright:
        logger.info(f"Запуск браузера и загрузка страницы: {url}")

        browser = await playwright.chromium.launch(headless=False)

        # Настройка контекста с пользовательским User-Agent
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        )

        # Отключение загрузки изображений
        await context.route(
            "**/*",
            lambda route, request: (
                route.continue_() if request.resource_type != "image" else route.abort()
            ),
        )

        page = await context.new_page()
        await page.goto(url, wait_until="load", timeout=60000)
        # Выбираем язык
        logger.info("Выбор языка")
        await page.locator(
            "span.ui.basic.large.label.horizontalMarginAuto.langToolbarLabel"
        ).click()
        await asyncio.sleep(20)

        # Начинаем обработку пагинации
        await handle_pagination(page, pages_directory)

        logger.info("Закрытие браузера")
        await browser.close()


if __name__ == "__main__":
    url = "https://startup.registroimprese.it/isin/search?0"
    asyncio.run(download_pages(url))
