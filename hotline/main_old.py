import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright
import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
import os
import re

import shutil
import json

# Путь к папкам
current_directory = Path.cwd()
html_files_directory = current_directory / "html_files"
data_directory = current_directory / "data"

data_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(exist_ok=True, parents=True)

output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"


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

            all_data = []
            all_product = read_json_file()
            for product in all_product:
                product_1c = product["1С"]
                find_product = re.sub(r"\(.*\)", "", product["Название товара"]).strip()

                url = f"https://hotline.ua/ua/sr/?q={find_product}"
                # Переход на страницу и ожидание полной загрузки
                await page.goto(url, timeout=60000, wait_until="networkidle")
                logger.info(find_product)
                # Ищем все результаты с классом 'list-item flex'
                list_items = await page.query_selector_all(
                    "//div[@class='list-item flex']"
                )
                if len(list_items) == 1:
                    # Если элемент один, сразу находим и нажимаем на кнопку "Порівняти Ціни"
                    await page.wait_for_selector("text=Порівняти Ціни", timeout=60000)
                    await page.click("text=Порівняти Ціни")
                else:
                    # Если элементов больше одного, проверяем текст внутри каждого
                    for list_item in list_items:
                        title_element = await list_item.query_selector(
                            "div.list-item__title-container.list-item__title-container--mobile.m_b-10 a.item-title.text-md.link.link--black"
                        )
                        if title_element:
                            title_text = (await title_element.inner_text()).strip()
                            logger.info(title_text)
                            if title_text.strip() == find_product:
                                logger.info(f"Совпадают названия {find_product}")
                                # Нажимаем на кнопку "Порівняти Ціни" внутри найденного элемента
                                compare_button = await list_item.query_selector(
                                    "text=Порівняти Ціни"
                                )
                                if compare_button:
                                    await compare_button.click()
                                break
                            else:
                                for list_item in list_items:
                                    link_element = await list_item.query_selector("a")
                                    if link_element:
                                        href_raw = await link_element.get_attribute(
                                            "href"
                                        )
                                        href = f"https://hotline.ua{href_raw}"
                                        logger.info(f"Найденная ссылка: {href}")
                                        await page.goto(
                                            href, timeout=60000, wait_until="load"
                                        )
                                        # break
                                # find_product = re.search(
                                #     r"\(([^)]+)\)", product["Название товара"]
                                # )
                                # if find_product:
                                #     find_product = find_product.group(1)
                                # url = f"https://hotline.ua/ua/sr/?q={find_product}"
                                # # Закрываем старую страницу и создаем новую
                                # # await page.close()
                                # # page = await context.new_page()
                                # # Переход на страницу и ожидание полной загрузки
                                # await context.close()  # Закрываем старый контекст
                                # context = await browser.new_context()
                                # page = (
                                #     await context.new_page()
                                # )  # Создаем новую страницу
                                # # Отключаем все возможные ресурсы, кроме основного HTML и JavaScript
                                # await page.route(
                                #     "**/*",
                                #     lambda route: (
                                #         route.abort()
                                #         if route.request.resource_type
                                #         not in ["document", "script"]
                                #         else route.continue_()
                                #     ),
                                # )

                                # await page.goto(url, timeout=60000, wait_until="load")

                                # try:
                                #     await asyncio.sleep(
                                #         1
                                #     )  # Пауза для полной загрузки страницы
                                #     logger.info("Была пауза")
                                #     # Проверяем, существует ли элемент с кнопкой "Порівняти Ціни"
                                #     compare_button = await page.query_selector(
                                #         "a.btn.btn--orange"
                                #     )
                                #     if compare_button:
                                #         await compare_button.click()
                                #     else:
                                #         logger.warning(
                                #             "Кнопка 'Порівняти Ціни' не найдена на странице."
                                #         )
                                # except Exception as e:
                                #     logger.error(f"Нету кнопки: {e}")

                                # # # Ищем все результаты с классом 'list-item flex'
                                # # list_items = await page.query_selector_all(
                                # #     "//div[@class='list-item flex']"
                                # # )
                                # # if len(list_items) == 1:
                                # #     # Если элемент один, сразу находим и нажимаем на кнопку "Порівняти Ціни"
                                # #     await page.wait_for_selector(
                                # #         "text=Порівняти Ціни", timeout=60000
                                # #     )
                                # #     await page.click("text=Порівняти Ціни")

                # Ожидание появления необходимого элемента
                await page.wait_for_selector(
                    "#__layout > div > div.default-layout__content-container > div:nth-child(3) > div.container > div.header > div.title > h1",
                    timeout=60000,
                )

                # Сохранение HTML контента
                content = await page.content()
                html_file_path = html_files_directory / f"{find_product}.html"
                with open(html_file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                soup = BeautifulSoup(content, "lxml")
                script_tag = soup.find_all(
                    "script", attrs={"type": "application/ld+json"}
                )
                if script_tag:
                    try:
                        json_data = json.loads(script_tag[1].string)
                        sku = json_data["sku"]
                        url = json_data["url"]
                        name = json_data["name"]
                        data = {"name": name, "sku": sku, "url": url, "1C": product_1c}
                        all_data.append(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка при разборе JSON в товаре {product}: {e}")

            df = pd.DataFrame(all_data)

            # Сохраняем DataFrame в Excel файл
            df.to_excel("output_xlsx_file.xlsx", index=False)
            shutil.rmtree(html_files_directory)
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


# Функция для чтения CSV и сохранения в JSON с использованием pandas
def csv_to_json():
    if output_csv_file.exists():
        try:
            df = pd.read_csv(
                output_csv_file, header=None, names=["Название товара", "1С"]
            )
            data_list = df.to_dict(orient="records")
            with open(output_json_file, "w", encoding="utf-8") as json_file:
                json.dump(data_list, json_file, ensure_ascii=False, indent=4)
            logger.info(
                f"Данные из {output_csv_file.name} сохранены в {output_json_file.name}"
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке CSV файла {output_csv_file.name}: {e}")
    else:
        logger.error(f"Файл {output_csv_file.name} не найден")


# Функция для чтения JSON файла и возврата списка словарей
def read_json_file():
    if output_json_file.exists():
        try:
            with open(output_json_file, "r", encoding="utf-8") as json_file:
                data_list = json.load(json_file)
                return data_list
        except Exception as e:
            logger.error(f"Ошибка при чтении JSON файла {output_json_file.name}: {e}")
            return []
    else:
        logger.error(f"Файл {output_json_file.name} не найден")
        return []


# Функция для выполнения основной логики
def main():
    csv_to_json()
    asyncio.run(single_html_one())
    # parsing_html()


if __name__ == "__main__":
    main()
