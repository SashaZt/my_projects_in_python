import pandas as pd
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
import random

cookies = {
    "PHPSESSID": "730dc0a4626c6a26f96032a603aea285",
    "newgorod2": "%CB%FE%E1%FB%E5+%E3%EE%F0%EE%E4%E0",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # 'Cookie': 'PHPSESSID=730dc0a4626c6a26f96032a603aea285; newgorod2=%CB%FE%E1%FB%E5+%E3%EE%F0%EE%E4%E0',
    "DNT": "1",
    "Pragma": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = data_directory / "xml"
png_directory = data_directory / "png"
data_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
png_directory.mkdir(parents=True, exist_ok=True)

csv_main_categories_urls = data_directory / "main_categories_urls.csv"
csv_file_successful = data_directory / "urls_successful.csv"
csv_result = current_directory / "result.csv"


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "1000 ip.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_main_categories_urls():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    response = requests.get(
        "https://1000dosok.ru/",
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        src = response.text

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(src, "html.parser")

        # Find all <a class="r"> elements
        links = soup.find_all("a", class_="r")

        # Extract 'href' attributes
        hrefs = [
            f"https://1000dosok.ru{link.get('href')}"
            for link in links
            if link.get("href")
        ]

        # Remove duplicates by converting the list to a set
        unique_hrefs = set(hrefs)

        # Create a DataFrame and save to 'url_category.csv'
        df = pd.DataFrame({"url": list(unique_hrefs)})
        df.to_csv(csv_main_categories_urls, index=False)
    else:
        logger.error(response.status_code)


def get_urls_from_csv():
    try:
        # Проверяем, существует ли файл
        csv_path = Path(csv_main_categories_urls)
        if not csv_path.exists():
            logger.error(f"Файл {file_path} не существует.")
            return []

        # Чтение CSV файла
        df = pd.read_csv(csv_path)

        # Проверяем наличие столбца 'url'
        if "url" not in df.columns:
            logger.error(f"В файле {file_path} нет столбца 'url'.")
            return []

        # Возвращаем список URL
        urls = df["url"].tolist()
        logger.info(f"Из файла {file_path} было извлечено {len(urls)} URL.")
        return urls

    except Exception as e:
        logger.error(f"Ошибка при чтении файла {file_path}: {e}")
        return []


def get_allurls_category():
    response = requests.get("https://1000dosok.ru/", cookies=cookies, headers=headers)


if __name__ == "__main__":
    get_main_categories_urls()
