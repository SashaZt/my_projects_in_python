import asyncio
from pathlib import Path

import nodriver as uc
import pandas as pd
from configuration.logger_setup import logger
import asyncio
import csv
import json
import os
import random
import re
from pathlib import Path

import aiofiles
import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_files_page_directory = current_directory / "html_files_page"
configuration_directory = current_directory / "configuration"
json_directory = current_directory / "json"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_files_page_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)

file_proxy = configuration_directory / "roman.txt"
csv_output_file = current_directory / "inn_data.csv"


async def get_url():
    href_set = set()
    # Запуск браузера
    browser = await uc.start(
        headless=False
    )  # Установите headless=False, если хотите видеть браузер
    tab = await browser.get(
        "https://optlist.ru/suppliers/promishlennoe-oborudovanie-optom/rossiia--2017370?pay=2&q=&sa=1&saveQuery=true&sort="
    )
    await asyncio.sleep(5)

    # Задача 3: Клик по селектору div:nth-child(19) > ul > li:nth-child(12) > a, пока он существует
    try:
        while True:

            # Задача 2: Извлечение текста из селектора ul > li.page-item.active
            try:
                active_page = await tab.select("ul > li.page-item.active")
                active_text = active_page.text
                logger.info(f"Старница {active_text}")
            except Exception as e:
                logger.error(f"Ошибка при извлечении текста: {e}")
            elements_find = await tab.select_all("li.page-item > a.page-link")
            next_button = None

            for element in elements_find:
                # Проверяем текст внутри ссылки
                text = element.text
                if text and "Далее" in text:
                    next_button = element
                    break
            # Задача 1: Извлечение всех уникальных href из тега <a>, вложенного в div.row.align-items-center > div > h2
            try:
                elements_find = await tab.select_all(
                    "div.row.align-items-center > div > h2"
                )

                for element in elements_find:
                    # Внутри каждого найденного элемента ищем тег <a>
                    a_tag = await element.query_selector("a")
                    if a_tag and "href" in a_tag.attributes:
                        url = f"https://optlist.ru{a_tag["href"]}"
                        href_set.add(url)

            except Exception as e:
                logger.error(f"Ошибка при извлечении href: {e}")
            if next_button:
                await next_button.click()
                await asyncio.sleep(2)  # Задержка для загрузки новой страницы
            else:
                print("Элемент для клика не найден.")
                break
    except Exception as e:
        print(f"Ошибка при клике: {e}")
    save_to_csv(href_set)
    # Закрытие вкладки и остановка браузера
    await tab.close()
    browser.stop()  # Остановка браузера


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def save_to_csv(href_set):
    # Создаем DataFrame из уникальных ссылок
    df = pd.DataFrame(href_set, columns=["url"])
    # Сохраняем DataFrame в CSV файл
    df.to_csv(csv_output_file, index=False, encoding="utf-8")
    logger.info(f"Данные успешно сохранены в {csv_output_file}")


async def get_company():
    all_urls = read_cities_from_csv(csv_output_file)  # Чтение URL из CSV файла
    browser = await uc.Browser.create(headless=False)
    # Переход на страницу логина и выполнение входа

    for url in all_urls:  # Ограничено одной URL для теста
        html_company = html_files_directory / f"{url.split('/')[-1]}.html"

        if html_company.exists():
            logger.warning(f"Файл {html_company} уже существует, пропускаем.")
            continue  # Переходим к следующей итерации цикла
        tab = await browser.get(url)
        # Check for CAPTCHA element

        # Wait for the CAPTCHA element to appear with a 30-second timeout
        try:
            captcha_element = await tab.select("div.captcha__human__title", timeout=5)
            if captcha_element:
                logger.info("CAPTCHA detected. Pausing for 30 seconds.")
                await asyncio.sleep(30)
        except asyncio.TimeoutError:
            # If the CAPTCHA element does not appear within 30 seconds, continue
            logger.info(
                "CAPTCHA not detected. Proceeding with data extraction.")

        html_content = await tab.get_content()
        with open(html_company, "w", encoding="utf-8") as file:
            file.write(html_content)
        logger.info(html_company)
    await browser.close()

    #     ema


def save_to_excel(data_list, filename="output.xlsx"):
    """
    Записывает список словарей в Excel-файл.

    :param data_list: Список словарей, где каждый словарь представляет одну запись
    :param filename: Имя файла Excel для сохранения данных
    """
    # Создаем DataFrame из списка словарей
    df = pd.DataFrame(data_list)

    # Сохраняем DataFrame в Excel
    df.to_excel(filename, index=False)
    print(f"Данные успешно сохранены в {filename}")


def parsing_html():


if __name__ == "__main__":
    # asyncio.run(get_url())
    # uc.loop().run_until_complete(get_company())
    parsing_html()
