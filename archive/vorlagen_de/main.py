import json
import os
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = current_directory / "xml_file"
html_directory = current_directory / "html"
documents_directory = current_directory / "documents"
configuration_directory = current_directory / "configuration"

documents_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(exist_ok=True, parents=True)
xml_directory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

start_sitemap = xml_directory / "sitemap.xml"
all_urls_page = data_directory / "all_urls.csv"
all_url_sitemap = data_directory / "sitemap.csv"
all_url_sitemap = data_directory / "sitemap.csv"

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "DNT": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def download_xml():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        "PHPSESSID": "rc24jkodfmn9eh93aa8pdauaca",
        "SERVERID": "s1",
        "OptanonAlertBoxClosed": "2024-12-02T06:56:42.204Z",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Wed+Dec+04+2024+22%3A01%3A02+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.32.0&isIABGlobal=false&consentId=a958fe43-04b3-41e4-9a14-ffbbe3f2baa2&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1%2CC0005%3A1&hosts=H446%3A1%2CH724%3A1%2CH568%3A1%2CH9%3A1%2CH648%3A1%2CH571%3A1%2CH49%3A1%2CH65%3A1%2CH626%3A1%2CH13%3A1%2CH14%3A1%2CH15%3A1%2CH717%3A1%2CH45%3A1%2CH2%3A1%2CH695%3A1%2CH584%3A1%2CH494%3A1%2CH46%3A1%2CH589%3A1%2CH497%3A1%2CH498%3A1%2CH627%3A1%2CH35%3A1%2CH725%3A1%2CH20%3A1%2CH646%3A1%2CH445%3A1%2CH539%3A1%2CH540%3A1%2CH729%3A1%2CH39%3A1%2CH541%3A1%2CH506%3A1%2CH17%3A1&genVendors=&geolocation=UA%3B18&AwaitingReconsent=false",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    for i in range(1, 9):
        sitemap_name = xml_directory / f"sitemap_0{i}.xml"
        response = requests.get(
            f"https://www.vorlagen.de/sitemaps/products/{i}.xml",
            cookies=cookies,
            proxies=proxies_dict,
            headers=headers,
            timeout=30,
        )

        # Проверка успешности запроса
        if response.status_code == 200:
            # Сохранение содержимого в файл
            with open(sitemap_name, "wb") as file:
                file.write(response.content)
            logger.info(f"Файл успешно сохранен в: {sitemap_name}")
        else:
            logger.error(f"Ошибка при скачивании файла: {response.status_code}")


def extract_urls_from_xml(file_path):
    """
    Извлекает все URL из XML-файла.
    """
    urls = []
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Пространство имен, используемое в XML
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Поиск всех элементов <loc>
        for loc in root.findall(".//ns:loc", namespaces=namespace):
            urls.append(loc.text.strip())
    except Exception as e:
        print(f"Ошибка обработки файла {file_path}: {e}")
    return urls


def process_all_xml_files_to_dataframe(xml_directory):
    """
    Обрабатывает все XML-файлы в указанной директории и возвращает DataFrame с URL.
    """
    all_urls = []
    for xml_file in xml_directory.glob("*.xml"):
        print(f"Обрабатываем файл: {xml_file}")
        urls = extract_urls_from_xml(xml_file)
        all_urls.extend(urls)

    # Создаем DataFrame
    return pd.DataFrame(all_urls, columns=["URL"])


def save_dataframe_to_csv(dataframe, csv_path):
    """
    Сохраняет DataFrame в CSV-файл.
    """
    dataframe.to_csv(csv_path, index=False, encoding="utf-8")
    print(f"Все URL сохранены в {csv_path}")


def get_html():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        "PHPSESSID": "rc24jkodfmn9eh93aa8pdauaca",
        "SERVERID": "s1",
        "OptanonAlertBoxClosed": "2024-12-02T06:56:42.204Z",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Wed+Dec+04+2024+22%3A41%3A58+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.32.0&isIABGlobal=false&consentId=a958fe43-04b3-41e4-9a14-ffbbe3f2baa2&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1%2CC0005%3A1&hosts=H446%3A1%2CH724%3A1%2CH568%3A1%2CH9%3A1%2CH648%3A1%2CH571%3A1%2CH49%3A1%2CH65%3A1%2CH626%3A1%2CH13%3A1%2CH14%3A1%2CH15%3A1%2CH717%3A1%2CH45%3A1%2CH2%3A1%2CH695%3A1%2CH584%3A1%2CH494%3A1%2CH46%3A1%2CH589%3A1%2CH497%3A1%2CH498%3A1%2CH627%3A1%2CH35%3A1%2CH725%3A1%2CH20%3A1%2CH646%3A1%2CH445%3A1%2CH539%3A1%2CH540%3A1%2CH729%3A1%2CH39%3A1%2CH541%3A1%2CH506%3A1%2CH17%3A1&genVendors=&geolocation=UA%3B18&AwaitingReconsent=false",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    url = "https://www.vorlagen.de/vollmachten-muster/bestattungswille"
    name = "_".join(url.rsplit("/", 2)[-2:]).replace("-", "_")
    file_name = html_directory / f"{name}.html"
    if file_name.exists():
        pass
    response = requests.get(
        url,
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
        timeout=30,
    )

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(response.text)
    logger.info(response.status_code)


# Функция для удаления запрещенных символов из строки
def sanitize_path_name(name):
    # Заменяем запрещенные символы на подчеркивание
    return re.sub(r'[<>:"/\\|?*]', "_", name)


# Создание полной структуры папок
def create_directory_structure(breadcrumb, base_dir):
    # Обрабатываем каждый элемент breadcrumb, убирая спецсимволы
    sanitized_breadcrumb = [sanitize_path_name(part) for part in breadcrumb]

    # Полный путь к корневой папке
    path = base_dir.joinpath(
        *sanitized_breadcrumb[:-1]
    )  # Все элементы, кроме последнего
    path.mkdir(parents=True, exist_ok=True)  # Создаем папки, если их нет

    # Имя файла
    file_name = (
        sanitize_path_name(sanitized_breadcrumb[-1]) + ".txt"
    )  # Последний элемент в качестве имени файла
    file_path_txt = path / file_name

    return file_path_txt


def save_images(images, file_path_txt):
    """
    Скачивает и сохраняет изображения из списка, используя базовый путь файла.

    :param images: Список URL изображений.
    :param file_path_txt: Путь к файлу .txt, который будет преобразован в базовое имя файла .jpeg.
    """
    # Преобразуем путь файла .txt в базовое имя для изображений
    base_dir = file_path_txt.parent  # Директория, где будут сохраняться изображения
    file_name_base = file_path_txt.stem  # Имя файла без расширения

    for index, image_url in enumerate(images, start=1):
        try:
            # Формируем имя файла с новым расширением
            file_name = f"{file_name_base}_{index:02}.jpeg"
            file_path = base_dir / file_name
            # Проверяем, существует ли файл
            if file_path.exists():
                logger.info(f"Файл уже существует, пропускаем: {file_path}")
                continue
            # Скачиваем изображение
            response = requests.get(image_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()  # Проверяем статус запроса

            # Сохраняем изображение в файл
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            logger.info(f"Изображение сохранено: {file_path}")

        except requests.RequestException as e:
            logger.error(f"Ошибка при скачивании изображения {image_url}: {e}")


def scrap_html():
    all_data = []
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

            soup = BeautifulSoup(content, "lxml")
            product_description = None
            description = None
            sales = None
            images = None
            # Находим все элементы li
            breadcrumb_items = soup.select("ul.breadcrumb > li")
            # Пропускаем первые два и извлекаем текст из остальных
            result_breadcrumb = [
                item.find("span", {"itemprop": "name"}).text.strip()
                for item in breadcrumb_items[2:]  # Пропускаем первые два
            ]
            product_description_raw = soup.find(
                "section", {"class": "product-description"}
            ).find("h1")
            if product_description_raw:
                product_description = product_description_raw.text.strip()
            description_raw = soup.find("section", {"id": "description_section"})
            if description_raw:
                description = " ".join(description_raw.stripped_strings)

            # Создаем структуру папок и получаем путь к файлу
            file_path_txt = create_directory_structure(
                result_breadcrumb, documents_directory
            )

            # Проверяем, существует ли файл
            if not file_path_txt.exists():
                # Если файл не существует, создаем структуру и возвращаем путь
                file_path_txt.parent.mkdir(parents=True, exist_ok=True)

            dtpopup_gallery_raw = soup.find_all("li", {"class": "dtpopup-gallery"})
            images = []
            for galery in dtpopup_gallery_raw:
                href = galery.find("a").get("href")
                images.append(href)
            save_images(images, file_path_txt)

            sales = None
            sales_raw = soup.find("div", {"class": "verkauft"})
            if sales_raw:
                sales = sales_raw.find("span").text.strip()
            # Преобразуем WindowsPath или PosixPath в строку для сохранения
            data = {"sales": sales, "file_path_txt": file_path_txt}
            if isinstance(data.get("file_path_txt"), Path):
                data["file_path_txt"] = str(data["file_path_txt"])

            all_data.append(data)
    with open("output_file.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=4)


def create_tree_from_directory():
    """
    Создает дерево из структуры папок и файлов .txt в указанной директории,
    добавляет значения sales из JSON файла и записывает результат в Excel.

    :param documents_directory: Директория с документами.
    :param json_file: Путь к JSON файлу с данными sales.
    :param excel_file: Путь к выходному Excel файлу.
    """

    # Считываем JSON файл
    with open("output_file.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Создаем словарь для быстрого доступа к sales
    sales_mapping = {
        Path(entry["file_path_txt"]).as_posix(): entry["sales"] or "0"
        for entry in json_data
    }

    # Собираем данные из папки
    all_data = []
    for file_path in documents_directory.rglob("*.txt"):
        relative_path = file_path.relative_to(documents_directory).as_posix()
        # Берем значение sales из mapping или "0"
        sales = sales_mapping.get(f"/{relative_path}", "0")
        all_data.append({"File": relative_path, "Sales": sales})

    # Создаем DataFrame и записываем в Excel
    df = pd.DataFrame(all_data)
    df.to_excel("document_structure.xlsx", index=False, sheet_name="Structure")
    print(f"Данные записаны в {"document_structure.xlsx"}")


if __name__ == "__main__":
    # download_xml()
    # df_urls = process_all_xml_files_to_dataframe(xml_directory)
    # save_dataframe_to_csv(df_urls, all_urls_page)
    # get_html()
    # scrap_html()
    # create_tree_from_directory()
