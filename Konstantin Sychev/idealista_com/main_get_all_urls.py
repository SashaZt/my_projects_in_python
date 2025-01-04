import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()
html_page_directory = current_directory / "html_page"
data_directory = current_directory / "data"
html_page_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

output_csv_file_all_category = data_directory / "output_all_category.csv"


# Ваш ключ ScraperAPI
API_KEY = "7757eea384bafff7726179e7855bb664"

# Базовый URL ScraperAPI
SCRAPER_API_BASE_URL = "http://api.scraperapi.com"


def read_csv_to_list(output_file):
    """
    Reads a CSV file with a column named 'url' and returns a list of URLs.

    :param file_path: Path to the CSV file.
    :return: List of URLs from the 'url' column.
    """
    try:
        # Читаем CSV файл
        df = pd.read_csv(output_file)

        # Проверяем, содержит ли файл столбец 'url'
        if "url" not in df.columns:
            raise ValueError("The CSV file does not contain a 'url' column.")

        # Преобразуем столбец 'url' в список
        url_list = df["url"].dropna().tolist()
        return url_list

    except Exception as e:
        print(f"An error occurred while reading the CSV file: {e}")
        return []


# Функция для извлечения номера страницы из URL
def extract_page_number(url):
    """
    Извлекает номер страницы из URL. Если номер не найден, возвращает 1.
    """
    match = re.search(r"pagina-(\d+)", url)
    return int(match.group(1)) if match else 1


# Функция для формирования имени файла из URL
def generate_filename_from_url(url):
    """
    Формирует имя файла на основе URL и номера страницы.
    """
    # Убираем базовый URL
    base_part = url.replace("https://www.idealista.com/en/", "").strip("/")

    # Удаляем суффиксы вроде "pagina-2.htm", если они есть
    base_part = base_part.split("/pagina-")[0]

    # Заменяем символы "/" и "." на "_"
    base_part = base_part.replace("/", "_").replace(".", "_")

    # Извлекаем номер страницы
    page_number = extract_page_number(url)

    # Формируем имя файла
    filename = html_page_directory / f"{base_part}_{page_number:02}.html"
    return filename


# Функция для сохранения HTML в файл
def save_html_to_file(html, filename):
    """
    Сохраняет HTML-код в указанный файл.
    """
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html)
    logger.info(f"HTML сохранен: {filename}")


# Функция для запроса через API
def fetch_html_via_scraperapi(url):
    params = {
        "api_key": API_KEY,
        "url": url,
    }
    response = requests.get(SCRAPER_API_BASE_URL, params=params)
    if response.status_code != 200:
        raise Exception(f"Ошибка запроса: {response.status_code}")

    # Сохраняем HTML с именем, основанным на URL
    html = response.text
    filename = generate_filename_from_url(url)
    save_html_to_file(html, filename)
    return html


# Парсинг HTML для получения URL и ссылки на следующую страницу
def parse_page(html, base_url="https://www.idealista.com"):
    soup = BeautifulSoup(html, "lxml")

    # Извлекаем все ссылки на странице с классом "item-link"
    page_urls = []
    for a in soup.find_all("a", {"class": "item-link"}):
        href = a["href"]
        # Добавляем базовый URL, если ссылка относительная
        if href.startswith("/"):
            href = base_url + href
        page_urls.append(href)

    # Ищем блок пагинации
    pagination_block = soup.find("div", {"class": "pagination"})

    # Ищем кнопку "Следующая страница" в блоке пагинации
    next_page_url = None
    if pagination_block:
        next_button = pagination_block.find("li", {"class": "next"})
        if next_button:
            next_page = next_button.find("a")
            if next_page and "href" in next_page.attrs:
                next_page_url = next_page["href"]
                # Добавляем базовый URL, если ссылка относительная
                if next_page_url.startswith("/"):
                    next_page_url = base_url + next_page_url

    return page_urls, next_page_url


# Обработка одной категории
def process_category(category_url):
    all_urls = []  # Для хранения всех URL категории
    next_page_url = category_url

    while next_page_url:
        logger.info(f"Запрос страницы: {next_page_url}")
        try:
            # Запрос HTML через ScraperAPI
            html = fetch_html_via_scraperapi(next_page_url)
            # Парсим URL и кнопку следующей страницы
            page_urls, next_page_url = parse_page(html)
            all_urls.extend(page_urls)  # Добавляем найденные URL
        except Exception as e:
            logger.error(f"Ошибка обработки страницы {next_page_url}: {e}")
            break  # Останавливаем цикл при ошибке

    return all_urls


# Обработка всех категорий
def process_all_categories(category_urls):
    all_category_urls = []
    for category_url in category_urls:
        logger.info(f"Обрабатываем категорию: {category_url}")
        category_urls = process_category(category_url)
        all_category_urls.extend(category_urls)  # Накопительно добавляем URL
    return all_category_urls


# Пример использования
if __name__ == "__main__":
    # Пример списка категорий
    # category_urls = [
    #     "https://www.idealista.com/en/venta-obranueva/cadiz-provincia/",
    # ]
    category_urls = read_csv_to_list(output_csv_file_all_category)
    # Обработка категорий
    all_urls = process_all_categories(category_urls)

    # Сохранение всех URL в файл
    with open("urls.txt", "w", encoding="utf-8") as file:
        for url in all_urls:
            file.write(f"{url}\n")

    logger.info(f"Всего URL собрано: {len(all_urls)}")
