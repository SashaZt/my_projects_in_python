# скачивание поставщиков после сбора ИНН по ссылке http://zakupki.gov.kg/popp/view/services/registry/suppliers.xhtml
import asyncio
import json
import os
import random
import re
from pathlib import Path

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from playwright.async_api import async_playwright

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_files_page_directory = current_directory / "html_files_page"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_files_page_directory.mkdir(parents=True, exist_ok=True)

file_proxy = configuration_directory / "roman.txt"
csv_output_file = current_directory / "inn_data.csv"


# Функция загрузки списка прокси
def load_proxies():
    if os.path.exists(file_proxy):
        with open(file_proxy, "r", encoding="utf-8") as file:
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


# Функция чтения списка ИНН из CSV файла
def read_cities_from_csv(file_path):
    df = pd.read_csv(file_path)
    return df["url"].tolist()


# Функция для распределения ИНН по нескольким потокам
def split_inns_into_batches(inns, num_batches):
    # Определяем размер каждой группы
    batch_size = len(inns) // num_batches
    # Распределяем ИНН по группам
    batches = []
    for i in range(num_batches - 1):
        batches.append(inns[i * batch_size : (i + 1) * batch_size])
    # Последняя группа включает все оставшиеся ИНН
    batches.append(inns[(num_batches - 1) * batch_size :])
    return batches


# Запуск нескольких задач, с прокси или без них
async def run_multiple_tasks(url, inns, proxies=None):
    tasks = []

    # Если есть прокси, используем их
    if proxies and len(proxies) > 0:
        logger.info(f"Запуск с использованием {len(proxies)} прокси.")
        inns_split = split_inns_into_batches(inns, len(proxies))
        for i, proxy in enumerate(proxies):
            task = asyncio.create_task(single_html_one(url, inns_split[i], proxy))
            tasks.append(task)
    else:
        # Если прокси нет, используем 10 потоков локально
        num_threads = 10
        logger.info(f"Запуск без прокси в {num_threads} локальных потоках.")
        inns_split = split_inns_into_batches(inns, num_threads)
        for i in range(num_threads):
            task = asyncio.create_task(single_html_one(url, inns_split[i], None))
            tasks.append(task)

    await asyncio.gather(*tasks)


# Модифицированная функция single_html_one с передачей списка ИНН и прокси
async def single_html_one(url, inns, proxy):
    proxy_config = parse_proxy(proxy) if proxy else None
    try:
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

            # Переход на страницу и ожидание полной загрузки
            await page.goto(url, timeout=60000, wait_until="networkidle")
            await asyncio.sleep(2)

            logger.info(f"Начало обработки группы из {len(inns)} ИНН.")

            for index, inn in enumerate(inns):
                html_file_path = html_files_directory / f"inn_{inn}.html"
                if html_file_path.exists():
                    logger.info(f"Файл для ИНН {inn} уже существует, пропускаем.")
                    continue  # Переходим к следующей итерации цикла

                if index > 0 and index % 10 == 0:
                    logger.info(f"Обработано {index} ИНН из текущей группы.")

                try:
                    await page.wait_for_selector(
                        "input[type='text'][name='j_idt66']", timeout=60000
                    )
                    await page.fill("input[type='text'][name='j_idt66']", inn)
                    # logger.info(f"Вставили в поиск: {inn}")
                except Exception as e:
                    logger.warning(f"Ошибка при заполнении ИНН {inn}: {e}")
                    continue
                await asyncio.sleep(1)
                try:
                    await page.wait_for_selector("input[value='Найти']", timeout=60000)
                    await page.click("input[value='Найти']")
                except Exception as e:
                    logger.warning(
                        f"Ошибка при нажатии на кнопку поиска для ИНН {inn}: {e}"
                    )
                    continue
                await asyncio.sleep(1)
                try:
                    await page.wait_for_selector(
                        "table.display-table.public-table", timeout=60000
                    )
                    first_row_link = await page.query_selector(
                        "table.display-table.public-table tbody tr:first-child a[onclick*='mojarra.jsfcljs']"
                    )
                    if first_row_link:
                        await first_row_link.click()
                except Exception as e:
                    logger.warning(
                        f"Ошибка при выборе первой строки таблицы для ИНН {inn}: {e}"
                    )
                    continue

                # Проверяем наличие ошибки на странице
                error_element = await page.query_selector(
                    "p[style='font-size:24px;color:#1785aa;font-weight: bold;']"
                )
                if error_element:
                    logger.warning(
                        f"Обнаружена ошибка на странице для ИНН {inn}, перезагружаем..."
                    )
                    await page.goto(url, timeout=60000, wait_until="networkidle")
                    continue

                try:
                    inn_element = await page.wait_for_selector(
                        "#j_idt70 > tbody > tr:nth-child(3) > td:nth-child(2)",
                        timeout=60000,
                    )
                    inn_text = await inn_element.text_content()
                    inn_text = inn_text.replace("/", "_")
                    # logger.info(f"Извлекли со страницы: {inn_text}")

                except Exception as e:
                    logger.warning(f"Ошибка при извлечении ИНН {inn}: {e}")
                    continue

                html_content = await page.content()
                html_file_path = html_files_directory / f"inn_{inn_text}.html"
                with open(html_file_path, "w", encoding="utf-8") as file:
                    file.write(html_content)
                if str(inn) == str(inn_text):
                    logger.info(f"Все правильно {inn_text}")
                else:
                    logger.warning(
                        f"Несоответствие ИНН: исходный {inn}, полученный {inn_text}"
                    )

                await page.goto(url, timeout=60000, wait_until="networkidle")

            logger.info(f"Завершена обработка группы из {len(inns)} ИНН.")
            await context.close()
            await browser.close()

    except Exception as e:
        logger.error(f"Общая ошибка при выполнении группы ИНН: {e}")


# Основная функция запуска программы
async def main():
    url = "http://zakupki.gov.kg/popp/view/services/registry/suppliers.xhtml"
    inns = read_cities_from_csv(csv_output_file)
    logger.info(f"Загружено {len(inns)} ИНН из файла.")

    proxies = load_proxies()
    await run_multiple_tasks(url, inns, proxies)


# Запуск программы
if __name__ == "__main__":
    asyncio.run(main())
