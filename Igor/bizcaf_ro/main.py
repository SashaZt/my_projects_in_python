import requests
import random
import csv
from pathlib import Path
from selectolax.parser import HTMLParser
from configuration.logger_setup import logger
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import requests
import random
import csv
from pathlib import Path
from selectolax.parser import HTMLParser
from configuration.logger_setup import logger
import ssl
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed


# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
# Файлы для записи и проверки URL
csv_file_path = Path("data/output.csv")
csv_file_successful = Path("data/urls_successful.csv")


headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Connection": "keep-alive",
    "Referer": "https://www.bizcaf.ro/foisor-patrat-cu-masa-si-banci-tip-picnic-rexal-ro_bizcafAd_2321294.dhtml",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}


class SSLAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(*args, **kwargs)


# Создание SSL-контекста с понижением уровня безопасности
ssl_context = ssl.create_default_context()
ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")

# Создание сессии requests с использованием адаптера SSL
session = requests.Session()
adapter = SSLAdapter(ssl_context=ssl_context)
session.mount("https://", adapter)


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "1000 ip.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_total_pages():
    proxies = load_proxies()
    """Определяет общее количество страниц с объявлениями на сайте."""
    url = "https://www.bizcaf.ro/"
    proxy = random.choice(proxies)
    proxies_dict = {"http": proxy, "https": proxy}
    try:
        response = session.get(
            url,
            headers=headers,
            proxies=proxies_dict,
            timeout=10,
        )
        if response.status_code == 200:
            tree = HTMLParser(response.text)

            # Извлечение количества объявлений
            total_ads_text = tree.css_first(
                "#main_content1 > div > div.links > table > tbody > tr:nth-child(1) > td > table > tbody > tr > td:nth-child(1)"
            ).text()
            total_ads = int(
                total_ads_text.split("din")[1]
                .split("anunturi")[0]
                .strip()
                .replace(".", "")
            )

            # Вычисление количества страниц
            ads_per_page = 24
            total_pages = (total_ads // ads_per_page) + (
                1 if total_ads % ads_per_page > 0 else 0
            )
            logger.info(f"Найдено {total_ads} объявлений на {total_pages} страницах.")
            return total_pages
        else:
            logger.error(f"Ошибка: статус код {response.status_code}")
            return 0

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении количества страниц: {e}")
        return 0


def collect_urls(total_pages):
    proxies = load_proxies()
    """Проходит по страницам и собирает URL-адреса объявлений, записывая их в CSV файл с использованием многопоточности."""
    # Создание SSL-контекста с понижением уровня безопасности
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")

    # Создание сессии requests с использованием адаптера SSL
    session = requests.Session()
    adapter = SSLAdapter(ssl_context=ssl_context)
    session.mount("https://", adapter)

    # Загружаем успешные URL из csv_file_successful
    successful_urls = set()
    if csv_file_successful.exists():
        with open(csv_file_successful, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            successful_urls = {row[0] for row in reader}

    with open(csv_file_path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_page = {
                executor.submit(
                    collect_urls_from_page, page_num, proxies, session
                ): page_num
                for page_num in range(1, total_pages + 1)
            }
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    urls = future.result()
                    for ad_url in urls:
                        if ad_url in successful_urls:
                            logger.info(
                                f"URL {ad_url} уже был успешно обработан. Прекращение сбора."
                            )
                            return
                        else:
                            writer.writerow([ad_url])
                            logger.info(f"URL {ad_url} добавлен в файл.")
                except Exception as exc:
                    logger.error(f"Ошибка при обработке страницы {page_num}: {exc}")


def collect_urls_from_page(page_num, proxies, session):
    proxies = load_proxies()
    """Функция для сбора URL с одной страницы."""
    proxy = random.choice(proxies)
    proxies_dict = {"http": proxy, "https": proxy}
    url = f"https://www.bizcaf.ro/anunturi/?pg={page_num}"
    try:
        response = session.get(url, headers=headers, proxies=proxies_dict, timeout=10)
        if response.status_code == 200:
            tree = HTMLParser(response.text)

            # Используем CSS-селектор для поиска всех элементов <tr> с атрибутом itemprop="itemListElement"
            tr_elements = tree.css('tr[itemprop="itemListElement"]')

            urls = []
            for tr in tr_elements:
                # Внутри каждого <tr> ищем ссылку с атрибутом itemprop="url"
                a_element = tr.css_first('a[itemprop="url"]')
                if a_element:
                    urls.append(a_element.attributes["href"])

            return urls
        else:
            logger.error(
                f"Ошибка: статус код {response.status_code} на странице {page_num}"
            )
            return []

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при обработке страницы {page_num}: {e}")
        return []


if __name__ == "__main__":

    total_pages = get_total_pages()
    if total_pages > 0:
        collect_urls(total_pages)
