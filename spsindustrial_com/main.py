from pathlib import Path
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import random
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from configuration.logger_setup import logger
from bs4 import BeautifulSoup
from io import BytesIO
import threading
import json


# Получаем текущую директорию
current_directory = Path.cwd()

# Загружаем файл конфигурации
config_directory = current_directory / "configuration"
config_file = config_directory / "config_directory.json"
with open(config_file, "r", encoding="utf-8") as f:
    config = json.load(f)


# Установка директорий на основе конфигурационного файла
temp_directory = current_directory / config["temp_directory"]
data_directory = current_directory / config["data_directory"]
logging_directory = current_directory / config["logging_directory"]

# Создание директорий, если их нет
temp_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
logging_directory.mkdir(parents=True, exist_ok=True)

# Указываем файлы для дальнейшего использования
xml_sitemap = data_directory / "sitemap_index.xml"
csv_url_site_maps = data_directory / "url_site_maps.csv"
csv_url_products = data_directory / "url_products.csv"
csv_file_successful = data_directory / "urls_successful.csv"
csv_result = data_directory / "result.csv"
file_proxies = current_directory / "configuration" / "proxies.txt"

# Файлы для сохранения cookies и headers
# Перед использованием используй код из файла save_cookies_headers.py
cookies_file = current_directory / "configuration" / "cookies.json"
headers_file = current_directory / "configuration" / "headers.json"

# Загрузка cookies из JSON файла
with open(cookies_file, "r", encoding="utf-8") as f:
    cookies = json.load(f)

# Загрузка headers из JSON файла
with open(headers_file, "r", encoding="utf-8") as f:
    headers = json.load(f)


# def load_proxies():
#     file_path = "1000 ip.txt"
#     # Загрузка списка прокси из файла
#     # with open(file_proxies, "r", encoding="utf-8") as file:
#     with open(file_path, "r", encoding="utf-8") as file:
#         proxies = [line.strip() for line in file]
#     return proxies


# Загрузка прокси
def load_proxies():

    # Проверяем, существует ли файл с прокси и не пуст ли он
    if file_proxies.exists() and file_proxies.stat().st_size > 0:
        # Открываем файл с прокси в режиме чтения с указанием кодировки utf-8
        with file_proxies.open("r", encoding="utf-8") as file:
            # Читаем файл построчно, удаляя пробелы с начала и конца строки.
            # Игнорируем пустые строки и собираем оставшиеся строки в список
            proxies = [line.strip() for line in file if line.strip()]
        # Возвращаем список прокси
        return proxies
    else:
        # Если файл не существует или пуст, выводим сообщение и возвращаем None
        # logger.error("Файл с прокси не найден или пуст.")
        return None


# Функция для скачивания XML по URL
def download_xml(url):
    proxies = load_proxies()  # Загружаем список всех прокси

    if proxies:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
        logger.info(f"Используем прокси: {proxy}")
    else:
        proxies_dict = None  # Если прокси нет, делаем запрос без прокси
        # print("Прокси не используем")

    response = requests.get(
        url,
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
    )
    response.raise_for_status()  # Если ошибка - выбросить исключение
    logger.info(response.status_code)
    return response.content


# Функция для парсинга основного sitemap и получения ссылок на другие sitemaps
def parse_main_sitemap(xml_content):
    # Инициализируем пустой список для хранения ссылок на подкарты (sitemaps)
    sitemap_urls = []

    # Парсим XML контент и создаем корневой элемент дерева XML
    root = ET.fromstring(xml_content)

    # Находим все элементы <sitemap> в XML, используя пространство имен "sitemap"
    for sitemap in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
        # В каждом элементе <sitemap> находим элемент <loc>, который содержит ссылку
        loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        # Добавляем ссылку в список
        sitemap_urls.append(loc)

    # Логируем количество найденных ссылок на подкарты
    logger.info(len(sitemap_urls))

    # Возвращаем список собранных ссылок
    return sitemap_urls


# Функция для парсинга каждого подкарты и получения всех URL
def parse_sub_sitemap(xml_content):
    # Инициализируем пустой список для хранения ссылок на страницы
    urls = []

    # Парсим XML контент и создаем корневой элемент дерева XML
    root = ET.fromstring(xml_content)

    # Находим все элементы <url> в XML, используя пространство имен "sitemaps.org"
    for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
        # В каждом элементе <url> находим элемент <loc>, который содержит ссылку на страницу
        loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        # Добавляем ссылку в список
        urls.append(loc)

    # Возвращаем список всех собранных ссылок на страницы
    return urls


# Основная функция для сбора всех URL из sitemaps
def collect_sitemap_urls():
    # URL основного файла sitemap
    main_sitemap_url = "https://www.spsindustrial.com/sitemap.xml"

    # Скачиваем XML содержимое основного sitemap
    main_sitemap_content = download_xml(main_sitemap_url)

    # Парсим основной sitemap и извлекаем ссылки на подкарты
    sitemap_urls = parse_main_sitemap(main_sitemap_content)

    # Инициализируем пустой список для хранения всех URL
    all_urls = []

    # Для каждой ссылки на подкарту:
    for sitemap_url in sitemap_urls:
        # Скачиваем XML содержимое подкарты
        sitemap_content = download_xml(sitemap_url)

        # Парсим подкарту и извлекаем все URL
        urls = parse_sub_sitemap(sitemap_content)

        # Добавляем извлеченные URL в общий список
        all_urls.extend(urls)

    # Создаем DataFrame из списка URL
    df = pd.DataFrame(all_urls, columns=["url"])

    # Записываем DataFrame в CSV файл
    df.to_csv(csv_url_products, index=False)

    # Логируем успешное завершение операции с указанием имени файла
    logger.info(f"Ссылки успешно записаны в {csv_url_products}")


def get_successful_urls(csv_file_successful):
    """Читает успешные URL из CSV-файла и возвращает их в виде множества."""

    # Проверяем, существует ли указанный CSV-файл
    if not Path(csv_file_successful).exists():
        # Если файл не найден, возвращаем пустое множество
        return set()

    # Открываем CSV-файл в режиме чтения с указанием кодировки utf-8
    with open(csv_file_successful, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)

        # Читаем строки из файла и собираем первый элемент каждой строки (URL) в множество
        # Пустые строки игнорируются
        successful_urls = {row[0] for row in reader if row}

    # Возвращаем множество успешных URL
    return successful_urls


def get_html(max_workers):
    # Получение списка уже успешных URL из CSV-файла
    successful_urls = get_successful_urls(csv_file_successful)

    # Загрузка списка всех прокси из файла
    proxies = load_proxies()

    # Чтение всех URL из CSV файла с продуктами
    urls_df = pd.read_csv(csv_url_products)

    # Если прокси есть, используем их
    if proxies and len(proxies) > 0:
        logger.info("Прокси загружены, используем прокси для запросов.")

        # Используем ThreadPoolExecutor для многопоточной обработки URL с прокси
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    fetch_url,  # Функция, которая будет выполняться в потоке
                    url,  # URL для запроса
                    proxies,  # Передаем список прокси
                    csv_file_successful,  # Файл для записи успешных URL
                    successful_urls,  # Множество уже успешных URL
                )
                for count, url in enumerate(
                    urls_df["url"], start=1
                )  # Перебираем URL из DataFrame
            ]

            # Обрабатываем задачи по мере их завершения
            for future in as_completed(futures):
                try:
                    result = future.result()

                    # Если результат равен 403, возвращаем код 403 для обработки в основной программе
                    if result == 403:
                        return 403
                except Exception as e:
                    logger.error(f"Error occurred: {e}")

    # Если прокси нет, выполняем запросы без прокси
    else:
        logger.warning(
            "Прокси не загружены или пусты. Запросы будут выполнены без прокси."
        )

        # Используем ThreadPoolExecutor для многопоточной обработки URL без прокси
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    fetch_url,  # Функция, которая будет выполняться в потоке
                    url,  # URL для запроса
                    None,  # Не передаем прокси
                    csv_file_successful,  # Файл для записи успешных URL
                    successful_urls,  # Множество уже успешных URL
                )
                for count, url in enumerate(
                    urls_df["url"], start=1
                )  # Перебираем URL из DataFrame
            ]

            # Обрабатываем задачи по мере их завершения
            for future in as_completed(futures):
                try:
                    result = future.result()

                    # Если результат равен 403, возвращаем код 403 для обработки в основной программе
                    if result == 403:
                        return 403
                except Exception as e:
                    logger.error(f"Error occurred: {e}")


def fetch_url(url, proxies, csv_file_successful, successful_urls):
    fetch_lock = (
        threading.Lock()
    )  # Лок для синхронизации записи в общий ресурс (множество и файл)

    # Проверяем, был ли уже обработан данный URL
    if url in successful_urls:
        logger.info(f"| Объявление уже было обработано, пропускаем. |")
        return

    # Если прокси есть, выбираем случайный
    if proxies and len(proxies) > 0:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
        # logger.info(f"Используем прокси: {proxy}")
    else:
        # Если прокси не загружены или их нет, делаем запрос без прокси
        proxies_dict = None
        # logger.info("Прокси не используем")

    try:
        # Отправляем GET-запрос с использованием заголовков, cookies и прокси (если есть)
        response = requests.get(
            url,
            headers=headers,  # Заголовки для запроса
            cookies=cookies,  # Cookies для запроса
            proxies=proxies_dict,  # Прокси, если указаны
            timeout=60,  # Тайм-аут на 60 секунд, чтобы избежать зависания
        )

        # Если статус-код 200, то запрос успешен
        if response.status_code == 200:
            # Парсим HTML с использованием BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            # Выполняем парсинг и записываем успех
            success = parsing(soup, url)

            if success:
                # Если парсинг успешен, добавляем URL в список успешных с использованием локального замка
                with fetch_lock:
                    successful_urls.add(url)  # Добавляем URL в множество
                    write_to_csv(url, csv_file_successful)  # Записываем URL в CSV файл
            return

        # Если возвращен статус-код 403, доступ запрещен
        elif response.status_code == 403:
            logger.error("Ошибка 403: доступ запрещен. Возвращаемся к выбору действий.")
            return 403  # Возвращаем код 403 для обработки в основном коде

        # Если получен любой другой код ошибки, логируем его
        else:
            logger.error(f"Ошибка {response.status_code}")

    # Обрабатываем любые исключения, возникающие в процессе
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")


def parsing(soup, url):
    try:
        page_title = None
        price = None
        description = None
        sku_item_n = None
        brand = None
        part = None
        upc = None
        min_order_qty = None
        page_title = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(1) > h1"
        )
        if page_title:
            page_title = page_title.text
        else:
            page_title = None

        description = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(3) > div > div > div > div > div:nth-child(1) > div"
        )
        if description:
            description = description.text.replace("Description", "")
        else:
            description = None

        price = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(10) > div > span"
        )
        if price:
            price = price.text
        else:
            price = None

        sku_item_n = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(2) > div"
        )
        if sku_item_n:
            sku_item_n = sku_item_n.text.replace("Item No.", "")
        else:
            sku_item_n = None

        upc_element = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(4) > div > span:nth-child(2)"
        )

        if upc_element:
            upc = upc_element.text
        else:
            upc = None  # Или любое другое значение по умолчанию

        brand = soup.select_one(
            "#content > div.fresnel-container.fresnel-greaterThanOrEqual-sm > div:nth-child(2) > div > div > div:nth-child(2) > div > div:nth-child(3) > div > span:nth-child(2)"
        )
        if brand:
            brand = brand.text
        else:
            brand = None

        manufacturer_name = brand
        part = upc
        data = data = (
            f"{url};{page_title};{description};{price};{min_order_qty};{sku_item_n};{upc};{brand};{manufacturer_name};{part}"
        )
        logger.info(data)
        write_to_csv(data, csv_result)
        return True
    except Exception as ex:
        logger.error(ex)


def write_to_csv(data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{data}\n")


def remove_successful_urls():
    # Проверяем, если файл с успешными URL пустой
    if csv_file_successful.stat().st_size == 0:
        logger.info("Файл urls_successful.csv пуст, ничего не делаем.")
        return

    # Загружаем данные из обоих CSV файлов
    try:
        # Читаем csv_url_products с заголовком
        df_products = pd.read_csv(csv_url_products)

        # Читаем csv_file_successful без заголовка и присваиваем имя столбцу
        df_successful = pd.read_csv(csv_file_successful, header=None, names=["url"])
    except FileNotFoundError as e:
        logger.error(f"Ошибка: {e}")
        return

    # Проверка на наличие столбца 'url' в df_products
    if "url" not in df_products.columns:
        logger.info("Файл url_products.csv не содержит колонку 'url'.")
        return

    # Удаляем успешные URL из списка продуктов
    initial_count = len(df_products)
    df_products = df_products[~df_products["url"].isin(df_successful["url"])]
    final_count = len(df_products)

    # Если были удалены какие-то записи
    if initial_count != final_count:
        # Перезаписываем файл csv_url_products
        df_products.to_csv(csv_url_products, index=False)
        logger.info(
            f"Удалено {initial_count - final_count} записей из {csv_url_products.name}."
        )

        # Очищаем файл csv_file_successful
        open(csv_file_successful, "w").close()
        logger.info(f"Файл {csv_file_successful.name} очищен.")
    else:
        print("Не было найдено совпадающих URL для удаления.")


def cookies_headers():
    # Директория для конфигурации
    # Пути к файлам
    raw_cookies_file = config_directory / "raw_cookies.txt"
    cookies_file = config_directory / "cookies.json"
    headers_file = config_directory / "headers.json"

    # Чтение данных из файла raw_cookies.txt
    with open(raw_cookies_file, "r", encoding="utf-8") as f:
        raw_data = f.read()

    # Выполнение кода из файла для создания переменных cookies и headers
    exec(raw_data)

    # Сохранение cookies в JSON файл
    with open(cookies_file, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=4)

    # Сохранение headers в JSON файл
    with open(headers_file, "w", encoding="utf-8") as f:
        json.dump(headers, f, ensure_ascii=False, indent=4)

    logger.info(f"Cookies сохранены в {cookies_file}")
    logger.info(f"Headers сохранены в {headers_file}")


# if __name__ == "__main__":
#     # Пример использования

#     collect_sitemap_urls()
#     remove_successful_urls()
#     max_workers = 50
#     result = get_html(max_workers)

while True:

    remove_successful_urls()
    # Запрос ввода от пользователя
    print(
        "Введите 1 для получения всех ссылок"
        "\nВведите 2 для получения данных в csv"
        "\nВведите 0 для закрытия программы"
    )
    user_input = int(input("Выберите действие: "))

    if user_input == 1:
        cookies_headers()
        collect_sitemap_urls()
    elif user_input == 2:
        cookies_headers()
        max_workers = int(input("Введите количество потоков: "))
        result = get_html(max_workers)

        if result == 403:
            logger.info("Ошибка 403, Обнови cookies")
            continue  # Возвращаемся к выбору действий
    elif user_input == 0:
        print("Программа завершена.")
        break  # Выход из цикла, завершение программы
    else:
        print("Неверный ввод, пожалуйста, введите корректный номер действия.")
