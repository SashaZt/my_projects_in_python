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
import sys


# Путь к папкам
current_directory = Path.cwd()
json_files_directory = current_directory / "json_files"
json_error_directory = current_directory / "json_error"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
json_files_directory.mkdir(exist_ok=True, parents=True)
json_error_directory.mkdir(exist_ok=True, parents=True)
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


# Пример кода для проверки наличия файла ошибки
def is_product_in_error_directory(
    find_product: str, json_error_directory: Path
) -> bool:
    """
    Проверяет, существует ли файл с названием товара в папке json_error_directory.
    Если существует, возвращает True; иначе False.
    """
    # Преобразуем название товара в корректное имя файла
    file_name = f"{find_product.replace('/', '_')}.json"
    error_file_path = json_error_directory / file_name

    # Проверяем наличие файла
    return error_file_path.exists()


# Асинхронная функция для сохранения HTML и получения ссылок по XPath
async def single_html_one():
    timeout = 30000
    proxies = load_proxies()
    proxy = random.choice(proxies) if proxies else None
    if not proxies:
        pass

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
                # Использование в основном коде
                if is_product_in_error_directory(find_product, json_error_directory):
                    logger.info(
                        f"Товар '{find_product}' уже в списке ошибок. Пропуск..."
                    )
                    continue  # Переход к следующему товару
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

                # # Ждем появления элемента с нужным классом
                # try:
                #     no_items_title = await page.wait_for_selector(
                #         "//div[@class='search__no-items-title text-center']",
                #         timeout=10000,
                #     )
                # except asyncio.TimeoutError:
                #     logger.info(
                #         "Элемент 'search__no-items-title text-center' не найден, продолжаем выполнение."
                #     )
                #     no_items_title = None  # Устанавливаем None, если элемент не найден
                # except Exception as e:
                #     logger.error(
                #         "Ошибка при проверке элемента 'search__no-items-title text-center':",
                #         exc_info=e,
                #     )
                #     no_items_title = None  # Устанавливаем None и продолжаем выполнение

                # # Если элемент найден, переходим к извлечению текста
                # if no_items_title:
                #     try:
                #         text_content = await no_items_title.inner_text()
                #     except Exception as e:
                #         logger.error(
                #             "Ошибка при извлечении текста из элемента:", exc_info=e
                #         )
                #         text_content = None  # Устанавливаем None, если произошла ошибка при извлечении текста

                #     # Если текст извлечен, проверяем на совпадение с "ничего не найдено"
                #     if text_content and "ничего не найдено" in text_content:
                #         try:
                #             error_product = product.get("Название товара")
                #             error_data = {
                #                 "error_product": error_product,
                #                 "1С": product.get("1С"),
                #             }
                #             all_error.append(error_data)
                #         except KeyError as e:
                #             logger.error(
                #                 "Ошибка доступа к ключам 'Название товара' или '1С' в product:",
                #                 exc_info=e,
                #             )
                #             # Продолжаем выполнение, если ключи не найдены

                # Если не найдено, продолжаем выполнение цикла
                # Устанавливаем флаг для завершения цикла
                element_found = False

                while not element_found:
                    # Пытаемся найти элемент с классом 'search__no-items-title text-center'
                    try:
                        no_items_title = await page.wait_for_selector(
                            "//div[@class='search__no-items-title text-center']",
                            timeout=5000,  # Уменьшаем таймаут для проверки в цикле
                        )
                        if no_items_title:
                            # Если элемент найден, обрабатываем его
                            text_content = await no_items_title.inner_text()
                            if "ничего не найдено" in text_content:
                                try:
                                    error_product = product.get("Название товара")
                                    error_data = {
                                        "error_product": error_product,
                                        "1С": product.get("1С"),
                                    }
                                    find_product = product.get(
                                        "Название товара"
                                    ).replace("/", "_")
                                    json_file_path = (
                                        json_error_directory / f"{find_product}.json"
                                    )
                                    with open(
                                        json_file_path,
                                        "w",
                                        encoding="utf-8",
                                    ) as f:
                                        json.dump(
                                            error_data,
                                            f,
                                            ensure_ascii=False,
                                            indent=4,
                                        )
                                    # all_error.append(error_data)

                                except KeyError as e:
                                    logger.error(
                                        "Ошибка доступа к ключам 'Название товара' или '1С' в product:",
                                        exc_info=e,
                                    )
                            element_found = (
                                True  # Завершаем цикл, если найден первый элемент
                            )
                    except asyncio.TimeoutError:
                        logger.info(
                            "Элемент 'search__no-items-title text-center' не найден, продолжаем проверку других элементов."
                        )
                    except Exception as e:
                        pass
                        # logger.error(
                        #     "Ошибка при проверке элемента 'search__no-items-title text-center':",
                        #     exc_info=e,
                        # )

                    # Проверка второго элемента, если первый не найден
                    if not element_found:
                        list_items = await page.query_selector_all(
                            "//div[@class='list-item flex']"
                        )
                        if list_items:
                            # Если элемент найден, обрабатываем его
                            # logger.info(
                            #     "Обнаружены элементы 'list-item flex'. Выполнение продолжается."
                            # )
                            for list_item in list_items:
                                title_text = None
                                title_link = await list_item.query_selector(
                                    "div.list-item__title-container.m_b-5 a"
                                )
                                if title_link:
                                    title_text = (await title_link.inner_text()).strip()

                                # Проверяем и разделяем строку, если текст найден
                                # find_product = product["Название товара"]
                                # match = re.match(r"^(.*?)(\s*\(.*\))$", find_product)
                                # if match:
                                #     main_name = match.group(
                                #         1
                                #     ).strip()  # Основное название
                                #     code = (
                                #         match.group(2).strip() if match.group(2) else ""
                                #     )  # Часть в скобках, если есть

                                #     # Сравнение найденного текста с элементом на странице
                                #     if title_text and (
                                #         title_text == main_name
                                #         or title_text == f"{main_name}{code}"
                                #     ):
                                #         link_element = await page.query_selector(
                                #             "div.list-item__title-container.m_b-5 a"
                                #         )
                                #         if link_element:
                                #             await link_element.click()  # Клик на элементе <a>
                                #             element_found = True  # Завершаем цикл, если найден и обработан второй элемент
                                #         else:
                                #             logger.info("Элемент для клика не найден.")
                                #             continue
                                # else:
                                #     logger.warning(
                                #         f"Название товара '{find_product}' не соответствует ожидаемому формату."
                                #     )
                                #     continue
                                # Пример использования в основном коде
                                if compare_product_titles(
                                    product["Название товара"], title_text
                                ):
                                    link_element = await page.query_selector(
                                        "div.list-item__title-container.m_b-5 a"
                                    )
                                    if link_element:
                                        await link_element.click()
                                        element_found = True
                                    else:
                                        logger.info("Элемент для клика не найден.")
                                else:
                                    logger.warning(
                                        f"Названия '{product['Название товара']}' и '{title_text}' не совпадают."
                                    )
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
                                soup = BeautifulSoup(content, "lxml")
                                script_tags = soup.find_all(
                                    "script", attrs={"type": "application/ld+json"}
                                )

                                if script_tags:
                                    try:
                                        for script_tag in script_tags[
                                            :2
                                        ]:  # Проходим по первым двум script тегам
                                            if not isinstance(script_tag.string, str):
                                                continue  # Если не строка, переходим к следующему тегу

                                            json_data = json.loads(script_tag.string)

                                            # Проверяем, что json_data является словарём
                                            if isinstance(json_data, dict):
                                                sku = json_data.get("sku")

                                                # Если sku найден, сохраняем json и выходим из цикла
                                                if sku:
                                                    with open(
                                                        json_file_path,
                                                        "w",
                                                        encoding="utf-8",
                                                    ) as f:
                                                        json.dump(
                                                            json_data,
                                                            f,
                                                            ensure_ascii=False,
                                                            indent=4,
                                                        )
                                                    break
                                                else:
                                                    error_product = product.get(
                                                        "Название товара"
                                                    )
                                                    error_data = {
                                                        "error_product": error_product,
                                                        "1С": product.get("1С"),
                                                    }
                                                    find_product = product.get(
                                                        "Название товара"
                                                    ).replace("/", "_")
                                                    json_file_path = (
                                                        json_error_directory
                                                        / f"{find_product}.json"
                                                    )
                                                    with open(
                                                        json_file_path,
                                                        "w",
                                                        encoding="utf-8",
                                                    ) as f:
                                                        json.dump(
                                                            error_data,
                                                            f,
                                                            ensure_ascii=False,
                                                            indent=4,
                                                        )
                                        else:
                                            # Если ни в одном теге не найден sku, пропускаем итерацию
                                            continue

                                    except Exception as e:
                                        logger.error(
                                            f"Непредвиденная ошибка: {e}\n{traceback.format_exc()}"
                                        )
                                        continue

                                logger.info(f"json сохранен для {find_product}")
                                break
                                # else:
                                # continue
                    element_found = True  # Завершаем цикл, если найден второй элемент

                    # Если ни один из элементов не найден, делаем паузу перед повторной проверкой
                    if not element_found:
                        await asyncio.sleep(1)

                # # Ищем все результаты с классом 'list-item flex'
                # list_items = await page.query_selector_all(
                #     "//div[@class='list-item flex']"
                # )
                # for list_item in list_items:
                #     title_text = None
                #     title_link = await list_item.query_selector(
                #         "div.list-item__title-container.m_b-5 a"
                #     )
                #     if title_link:
                #         # Выполняем необходимые действия, например, извлекаем текст
                #         title_text = (await title_link.inner_text()).strip()
                #     # Используем регулярное выражение для разделения строки

                #     find_product = product["Название товара"]
                #     match = re.match(r"^(.*?)(\s*\(.*\))$", find_product)
                #     main_name = match.group(1).strip()  # Основное название
                #     code = match.group(2).strip()  # Часть в скобках
                #     if title_text == main_name or f"{main_name}{code}":
                #         # Извлекаем элемент <a> и выполняем клик
                #         link_element = await page.query_selector(
                #             "div.list-item__title-container.m_b-5 a"
                #         )
                #         if link_element:
                #             await link_element.click()  # Клик на элементе <a>
                #         else:
                #             continue

                #         try:
                #             await page.wait_for_selector(
                #                 "#__layout > div > div.default-layout__content-container > div:nth-child(3) > div.container > div.header > div.title > h1",
                #                 timeout=timeout,
                #             )
                #         except asyncio.TimeoutError:
                #             logger.error(f"Тайм-аут при переходе на URL: {url}")
                #             continue  # Переходим к следующему URL
                #         except Exception as e:
                #             logger.error(
                #                 f"Непредвиденная ошибка: {e}\n{traceback.format_exc()}"
                #             )
                #             continue
                #         content = await page.content()
                #         # find_product = find_product.replace("/", "_")
                #         # json_file_path = json_files_directory / f"{find_product}.json"
                #         with open(json_file_path, "w", encoding="utf-8") as f:
                #             f.write(content)
                #         soup = BeautifulSoup(content, "lxml")
                #         script_tags = soup.find_all(
                #             "script", attrs={"type": "application/ld+json"}
                #         )

                #         if script_tags:
                #             try:
                #                 json_data = json.loads(script_tags[0].string)
                #                 sku = json_data.get("sku")
                #                 if sku:
                #                     with open(
                #                         json_file_path, "w", encoding="utf-8"
                #                     ) as f:
                #                         json.dump(
                #                             json_data, f, ensure_ascii=False, indent=4
                #                         )
                #                 else:
                #                     json_data = json.loads(script_tags[1].string)
                #                     sku = json_data.get("sku")
                #                     if sku:
                #                         with open(
                #                             json_file_path, "w", encoding="utf-8"
                #                         ) as f:
                #                             json.dump(
                #                                 json_data,
                #                                 f,
                #                                 ensure_ascii=False,
                #                                 indent=4,
                #                             )

                #             except Exception as e:
                #                 logger.error(
                #                     f"Непредвиденная ошибка: {e}\n{traceback.format_exc()}"
                #                 )
                #                 continue

                #         logger.info(f"json сохранен для {find_product}")
                #         break
                #     else:
                #         continue

            await context.close()
            await browser.close()
            # Запись all_error в CSV файл после завершения обработки всех товаров
            # После завершения обработки записываем данные в JSON
            # if all_error:
            #     with open(error_json_file, "w", encoding="utf-8") as f:
            #         json.dump(all_error, f, ensure_ascii=False, indent=4)
            #     print(f"Ошибки записаны в файл {error_json_file}")
            # else:
            #     print("Нет данных для записи в файл ошибок.")
    except Exception as e:
        logger.error(f"Ошибка при обработке URL: {e}")


def compare_product_titles(
    product_name: str, title_text: str, match_threshold: float = 0.5
) -> bool:
    """
    Проверяет, совпадают ли названия продукта и заголовок на странице.
    Совпадение считается успешным, если хотя бы `match_threshold` слов из product_name
    содержатся в title_text.
    """
    # Приводим строки к нижнему регистру
    product_name = product_name.lower()
    title_text = title_text.lower()

    # Разбиваем product_name на слова
    product_words = product_name.split()

    # Считаем количество совпадающих слов
    match_count = sum(1 for word in product_words if word in title_text)

    # Рассчитываем долю совпадающих слов
    match_ratio = match_count / len(product_words)

    # Возвращаем True, если совпадение превышает или равно пороговому значению
    return match_ratio >= match_threshold


# def compare_product_titles(product_name: str, title_text: str) -> bool:
#     """
#     Проверяет, совпадают ли названия продукта и заголовок на странице.
#     Сравнение выполняется по наличию всех слов из одного названия в другом.
#     """
#     # Разделяем названия на слова, используя пробел как разделитель
#     product_words = set(product_name.split())
#     title_words = set(title_text.split())

#     # Проверяем, что все слова из title_text содержатся в product_name (и наоборот)
#     return title_words.issubset(product_words) or product_words.issubset(title_words)


def validate_data_completion() -> bool:
    """
    Проверяет, что количество обработанных файлов соответствует количеству товаров,
    за вычетом товаров с ошибками. Если нет, выводит сообщение и завершает скрипт.

    Возвращает True, если валидация пройдена успешно, и False в противном случае.
    """
    # Загружаем все товары
    all_product = read_json_file()
    total_products = len(all_product)

    # Количество товаров с ошибками — количество файлов в json_error_directory
    error_count = len(list(json_error_directory.glob("*.json")))

    # Количество файлов в папке json_files_directory (успешно обработанных)
    processed_files_count = len(list(json_files_directory.glob("*.json")))

    # Проверяем выполнение условия
    if total_products - error_count == processed_files_count:
        logger.info("Все данные успешно обработаны.")
        sys.exit(1)  # Останавливаем скрипт с кодом завершения 1
    else:
        logger.error(
            f"Ошибка: Ожидалось {total_products - error_count} обработанных товаров, "
            f"но найдено только {processed_files_count} файлов. Скрипт продолжает работу."
        )


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
        if compare_product_titles(product["Название товара"], product_name):
            # if product["Название товара"] == product_name:
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
            validate_data_completion()
            await single_html_one()  # Асинхронный запуск сбора данных
            print("Сбор данных завершен.")
            break  # Если выполнение успешно, выходим из цикла
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            print("Перезапуск сбора данных...")


async def countdown():
    """Асинхронный обратный отсчёт с обновлением строки на месте."""
    for remaining in range(20, 0, -1):
        sys.stdout.write(
            f"\rОсталось {remaining} секунд до выбора по умолчанию (1)... "
        )
        sys.stdout.flush()
        await asyncio.sleep(1)
    print("\nВремя ожидания истекло.")  # Сообщение, когда отсчёт завершён


async def wait_for_user_input():
    """Асинхронный ввод с таймаутом и параллельным отсчётом."""
    countdown_task = asyncio.create_task(countdown())  # Запускаем обратный отсчёт

    try:
        user_input = await asyncio.wait_for(
            asyncio.to_thread(
                input, "\nВыберите действие: "
            ),  # Переносим ввод на новую строку
            timeout=20,  # Основной таймаут для ожидания
        )
        countdown_task.cancel()  # Отменяем задачу отсчёта, если получен ввод
        print()  # Переход на новую строку после отмены
        return user_input
    except asyncio.TimeoutError:
        print("\nАвтоматический выбор действия 1.")
        return "1"  # Возвращаем выбор по умолчанию


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
                logger.info("Парсинг данных и создание Excel-файла...")
                parsing_html()
                break  # Завершение программы
            except Exception as e:
                logger.error(f"Ошибка при создании Excel: {e}")
        elif user_input == 3:
            if os.path.exists(json_files_directory):
                shutil.rmtree(json_files_directory)
                logger.info("Временные файлы удалены.")
            else:
                logger.error("Временные файлы не найдены.")
        elif user_input == 0:
            logger.info("Программа завершена.")
            break  # Завершение программы
        else:
            logger.error("Неверный ввод, пожалуйста, введите число от 0 до 3.")


if __name__ == "__main__":
    asyncio.run(main())
