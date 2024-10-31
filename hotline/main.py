import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright
import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from urllib.parse import quote
import shutil
import json
import traceback
import os
import re


# Путь к папкам
current_directory = Path.cwd()
json_files_directory = current_directory / "json_files"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
json_files_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(exist_ok=True, parents=True)

output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"
error_json_file = data_directory / "error_product.json"
proxy_file = configuration_directory / "proxy.txt"


# Функция загрузки списка прокси
def load_proxies():
    if proxy_file.exists():
        with open(proxy_file, "r", encoding="utf-8") as file:
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


def encode_product_name(product_name: str) -> str:
    encoded_product = quote(product_name, safe="")

    return encoded_product


# Асинхронная функция для сохранения HTML и получения ссылок по XPath
async def single_html_one():
    timeout = 10000
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
            all_error = []
            all_product = read_json_file()
            # Читаем список товаров с ошибками
            error_products = read_error_products()
            for product in all_product:
                find_product = product["Название товара"]

                # Проверяем, если товар уже есть в списке ошибок, то пропускаем его
                if any(
                    item["error_product"] == find_product for item in error_products
                ):
                    logger.info(find_product)
                    continue
                encoded_product = encode_product_name(find_product)
                url = f"https://hotline.ua/sr/?q={encoded_product}"
                find_product = find_product.replace("/", "_")
                json_file_path = json_files_directory / f"{find_product}.json"
                if json_file_path.exists():
                    # logger.warning(f"Файл {json_file_path} уже существует, пропускаем.")
                    continue  # Переходим к следующей итерации цикла

                try:
                    await page.goto(url, timeout=timeout, wait_until="networkidle")
                except asyncio.TimeoutError:
                    logger.error(f"Тайм-аут при переходе на URL: {url}")
                    continue  # Переходим к следующему URL
                except Exception as e:
                    logger.error(f"Ошибка при переходе на {url}: {e}")
                    continue
                # Ждем появления элемента с нужным классом
                try:
                    no_items_title = await page.wait_for_selector(
                        "//div[@class='search__no-items-title text-center']",
                        timeout=10000,
                    )
                    # Извлекаем текст из элемента
                    text_content = await no_items_title.inner_text()

                    # Проверяем, содержит ли текст "ничего не найдено"
                    if "ничего не найдено" in text_content:
                        error_product = product["Название товара"]
                        error_data = {
                            "error_product": error_product,
                            "1С": product["1С"],
                        }
                        all_error.append(error_data)
                        continue

                except Exception as e:
                    logger.error(
                        "Элемент 'search__no-items-title text-center' не появился на странице:",
                        e,
                    )

                # Ожидаем появления кнопки смены языка
                await page.wait_for_selector(
                    "div.lang-button.flex.middle-xs.center-xs.header__lang-icon"
                )

                # Ищем элемент с кнопкой языка
                lang_button = await page.query_selector(
                    "div.lang-button.flex.middle-xs.center-xs.header__lang-icon"
                )

                if lang_button:
                    # Извлекаем текст из кнопки и проверяем, является ли он 'UA'
                    button_text = await lang_button.inner_text()
                    if button_text.strip() == "UA":
                        await lang_button.click()

                        # Ждем появления элементов для выбора языка
                        await page.wait_for_selector("div.lang-item", timeout=timeout)

                        # Извлекаем все элементы с классом lang-item
                        lang_items = await page.query_selector_all("div.lang-item")

                        # Проходим по всем элементам и ищем тот, где текст равен 'RU'
                        for item in lang_items:
                            inner_text = await item.inner_text()
                            if inner_text.strip() == "RU":
                                await item.click()
                                break
                        else:
                            logger.error("Элемент с текстом 'RU' не найден.")

                else:
                    logger.error("Кнопка смены языка не найдена.")
                # закончили работу с языками
                # Ищем все результаты с классом 'list-item flex'
                list_items = await page.query_selector_all(
                    "//div[@class='list-item flex']"
                )
                for list_item in list_items:
                    title_text = None
                    title_link = await list_item.query_selector(
                        "div.list-item__title-container.m_b-5 a"
                    )
                    if title_link:
                        # Выполняем необходимые действия, например, извлекаем текст
                        title_text = (await title_link.inner_text()).strip()
                    # Используем регулярное выражение для разделения строки

                    find_product = product["Название товара"]
                    match = re.match(r"^(.*?)(\s*\(.*\))$", find_product)
                    main_name = match.group(1).strip()  # Основное название
                    code = match.group(2).strip()  # Часть в скобках
                    if title_text == main_name or f"{main_name}{code}":
                        # Извлекаем элемент <a> и выполняем клик
                        link_element = await page.query_selector(
                            "div.list-item__title-container.m_b-5 a"
                        )
                        if link_element:
                            await link_element.click()  # Клик на элементе <a>
                        else:
                            continue

                        try:
                            await page.wait_for_selector(
                                "#__layout > div > div.default-layout__content-container > div:nth-child(3) > div.container > div.header > div.title > h1",
                                timeout=timeout,
                            )
                        except asyncio.TimeoutError:
                            logger.error(f"Тайм-аут при переходе на URL: {url}")
                            continue  # Переходим к следующему URL
                        except Exception as e:
                            logger.error(
                                f"Непредвиденная ошибка: {e}\n{traceback.format_exc()}"
                            )
                            continue
                        content = await page.content()
                        # find_product = find_product.replace("/", "_")
                        # json_file_path = json_files_directory / f"{find_product}.json"
                        with open(json_file_path, "w", encoding="utf-8") as f:
                            f.write(content)
                        soup = BeautifulSoup(content, "lxml")
                        script_tags = soup.find_all(
                            "script", attrs={"type": "application/ld+json"}
                        )

                        if script_tags:
                            try:
                                json_data = json.loads(script_tags[0].string)
                                sku = json_data.get("sku")
                                if sku:
                                    with open(
                                        json_file_path, "w", encoding="utf-8"
                                    ) as f:
                                        json.dump(
                                            json_data, f, ensure_ascii=False, indent=4
                                        )
                                else:
                                    json_data = json.loads(script_tags[1].string)
                                    sku = json_data.get("sku")
                                    if sku:
                                        with open(
                                            json_file_path, "w", encoding="utf-8"
                                        ) as f:
                                            json.dump(
                                                json_data,
                                                f,
                                                ensure_ascii=False,
                                                indent=4,
                                            )

                            except Exception as e:
                                logger.error(
                                    f"Непредвиденная ошибка: {e}\n{traceback.format_exc()}"
                                )
                                continue

                        logger.info(f"json сохранен для {find_product}")
                        break
                    else:
                        continue

            await context.close()
            await browser.close()
            # Запись all_error в CSV файл после завершения обработки всех товаров
            # После завершения обработки записываем данные в JSON
            if all_error:
                with open(error_json_file, "w", encoding="utf-8") as f:
                    json.dump(all_error, f, ensure_ascii=False, indent=4)
                print(f"Ошибки записаны в файл {error_json_file}")
            else:
                print("Нет данных для записи в файл ошибок.")
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


# Функция для чтения JSON и возврата списка товаров с ошибками
def read_error_products():
    """
    Читает файл error_product.json и возвращает список товаров с ошибками.
    Если файл не существует, возвращает пустой список.
    """
    if os.path.exists(error_json_file):
        with open(error_json_file, "r", encoding="utf-8") as f:
            error_products = json.load(f)
    else:
        error_products = []  # Возвращаем пустой список, если файл не существует

    return error_products


def extract_product_name_from_file(file_path: Path) -> str:
    """Извлечение названия товара из имени HTML файла."""
    return file_path.stem  # Возвращает имя файла без расширения


def find_product_1c(product_name: str, all_product: list) -> str:
    """Поиск значения '1С' для товара по его названию."""
    for product in all_product:
        if product["Название товара"] == product_name:
            return product["1С"]
    logger.warning(f"Товар '{product_name}' не найден в all_product.")
    return None


def parsing_html():
    """Парсинг HTML файлов и сопоставление с данными из JSON."""
    all_product = read_json_file()  # Загружаем список товаров
    all_data = []
    for json_file in json_files_directory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)
        product_name = extract_product_name_from_file(json_file)  # Имя товара из файла
        product_1c = find_product_1c(product_name, all_product)  # Поиск '1С'

        data = {
            "name": data.get("name"),
            "sku": data.get("sku"),
            "url": data.get("url"),
            "1С": product_1c,
        }
        all_data.append(data)

    # Создаем DataFrame и сохраняем в Excel
    df = pd.DataFrame(all_data)
    df.to_excel("output_xlsx_file.xlsx", index=False)
    logger.info("Файл output_xlsx_file.xlsx успешно сохранен.")
    # shutil.rmtree(html_files_directory)


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


async def run_data_collection():
    """Функция для повторного запуска задачи по сбору данных."""
    while True:
        try:
            print("Сбор данных начат...")
            csv_to_json()
            await single_html_one()  # Асинхронный запуск сбора данных
            print("Сбор данных завершен.")
            break  # Если выполнение успешно, выходим из цикла
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            print("Перезапуск сбора данных...")


async def wait_for_user_input():
    """Асинхронный ввод с таймаутом на ожидание."""
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(input, "Выберите действие: "), timeout=10.0
        )
    except asyncio.TimeoutError:
        print("Время ожидания истекло. Автоматический выбор действия 1.")
        return "1"  # Возвращаем выбор 1


async def main():
    while True:
        print(
            "Введите 1 для сбора данных с сайта"
            "\nВведите 2 для получения Excel файла"
            "\nВведите 3 для удаления временных файлов"
            "\nВведите 0 для закрытия программы"
        )

        user_input = await wait_for_user_input()  # Ожидание ввода с таймаутом
        print("У вас 10сек что выбрать, если нет, продолжаем сбор данных")
        try:
            user_input = int(user_input)
        except ValueError:
            print("Ошибка: введите целое число от 0 до 3.")
            continue  # Возвращаемся к началу цикла

        if user_input == 1:
            await run_data_collection()  # Асинхронный запуск задачи с перезапуском
        elif user_input == 2:
            try:
                print("Парсинг данных и создание Excel-файла...")
                parsing_html()
                print("Excel-файл успешно создан.")
            except Exception as e:
                print(f"Ошибка при создании Excel: {e}")
        elif user_input == 3:
            if os.path.exists(json_files_directory):
                shutil.rmtree(json_files_directory)
                print("Временные файлы удалены.")
            else:
                print("Временные файлы не найдены.")
        elif user_input == 0:
            print("Программа завершена.")
            break  # Завершение программы
        else:
            print("Неверный ввод, пожалуйста, введите число от 0 до 3.")


if __name__ == "__main__":
    asyncio.run(main())
