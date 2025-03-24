import json
import random
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_directory = current_directory / "html"
log_directory = current_directory / "log"
img_directory = current_directory / "img"

img_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
output_html_file = html_directory / "output.html"
output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"
categories_file = current_directory / "category.txt"
BASE_URL = "https://altstar.ua/"

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


class AltStarScraper:
    def __init__(self, base_url="https://altstar.ua", category_url="/salniki"):
        self.base_url = base_url
        self.category_url = category_url
        self.full_url = base_url + category_url
        self.cookies = {
            "PHPSESSID": "4u34v9cjpr22r449jev8j5ho40",
            "PHPSESSID": "4u34v9cjpr22r449jev8j5ho40",
            "PHPSESSID": "4u34v9cjpr22r449jev8j5ho40",
            "language": "uk-ua",
            "currency": "UAH",
        }

        self.headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "ru,en;q=0.9,uk;q=0.8",
            "cache-control": "no-cache",
            "dnt": "1",
            "pragma": "no-cache",
            "priority": "u=0, i",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            # 'cookie': 'PHPSESSID=4u34v9cjpr22r449jev8j5ho40; PHPSESSID=4u34v9cjpr22r449jev8j5ho40; PHPSESSID=4u34v9cjpr22r449jev8j5ho40; language=uk-ua; currency=UAH',
        }
        self.products_links = []

        # Создаем директорию для текущей категории
        category_name = category_url.strip("/")
        self.category_dir = data_directory / category_name
        self.category_dir.mkdir(exist_ok=True)

        self.links_file = self.category_dir / "product_links.json"

    def get_page(self, url):
        """Получает и возвращает HTML-страницу"""
        try:
            response = requests.get(
                url, cookies=self.cookies, headers=self.headers, timeout=30
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Ошибка при загрузке страницы {url}: {e}")
            return None

    def extract_product_links(self, html):
        """Извлекает ссылки на товары со страницы категории"""
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        links = []

        # Находим все элементы с ссылками на товары
        product_elements = soup.find_all("span", class_="crr-cnt")
        for element in product_elements:
            product_url = element.get("data-crr-url")
            if product_url:
                links.append(product_url)
                logger.info(f"Найдена ссылка на товар: {product_url}")

        return links

    def get_total_pages(self, html):
        """Определяет общее количество страниц пагинации"""
        if not html:
            return 1

        soup = BeautifulSoup(html, "lxml")
        pagination_info = soup.find("div", class_="col-sm-4 text-right")

        if pagination_info:
            # Извлекаем число из текста "Відображено 1 по 20 з 121"
            text = pagination_info.text
            match = re.search(r"з (\d+)", text)
            if match:
                total_items = int(match.group(1))
                items_per_page = 20  # Количество товаров на странице
                total_pages = (total_items // items_per_page) + (
                    1 if total_items % items_per_page > 0 else 0
                )
                logger.info(f"Всего товаров: {total_items}, страниц: {total_pages}")
                return total_pages

        logger.warning("Не удалось определить общее количество страниц, возвращаем 1")
        return 1

    def collect_all_product_links(self):
        """Собирает ссылки на все товары со всех страниц категории"""
        # Если файл со ссылками уже существует, загружаем его
        if self.links_file.exists():
            try:
                with open(self.links_file, "r", encoding="utf-8") as f:
                    self.products_links = json.load(f)
                logger.info(f"Загружено {len(self.products_links)} ссылок из файла")
                return self.products_links
            except Exception as e:
                logger.error(f"Ошибка при загрузке файла ссылок: {e}")
                # Если ошибка при загрузке, создаем пустой список
                self.products_links = []

        # Получаем первую страницу категории
        first_page_html = self.get_page(self.full_url)
        if not first_page_html:
            logger.error("Не удалось загрузить первую страницу категории")
            return []

        # Получаем общее количество страниц
        total_pages = self.get_total_pages(first_page_html)

        # Собираем ссылки с первой страницы
        links = self.extract_product_links(first_page_html)
        self.products_links.extend(links)

        # Обходим остальные страницы (со 2-й по последнюю)
        for page in range(2, total_pages + 1):
            page_url = f"{self.full_url}?page={page}"
            logger.info(f"Обрабатываем страницу {page}/{total_pages}: {page_url}")

            page_html = self.get_page(page_url)
            if page_html:
                page_links = self.extract_product_links(page_html)
                self.products_links.extend(page_links)

                # Сохраняем промежуточные результаты
                self.save_links()

                # Делаем паузу между запросами
                time.sleep(random.uniform(1.0, 3.0))
            else:
                logger.error(f"Не удалось загрузить страницу {page}")

        logger.info(f"Всего собрано ссылок на товары: {len(self.products_links)}")
        return self.products_links

    def save_links(self):
        """Сохраняет ссылки на товары в JSON-файл"""
        try:
            with open(self.links_file, "w", encoding="utf-8") as f:
                json.dump(self.products_links, f, ensure_ascii=False)
            logger.info(f"Ссылки сохранены в файл: {self.links_file}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении ссылок: {e}")

    def download_product_pages(self):
        """Скачивает страницы всех товаров"""
        if not self.products_links:
            logger.warning("Список ссылок пуст, сначала соберите ссылки")
            return

        # Создаем директорию для HTML-файлов текущей категории
        category_name = self.category_url.strip("/")
        category_html_dir = html_directory / category_name
        category_html_dir.mkdir(exist_ok=True)

        total = len(self.products_links)
        for i, url in enumerate(self.products_links, 1):
            # Извлекаем имя файла из URL
            # Пример: https://altstar.ua/f032111123/cargo -> f032111123_cargo.html
            url_parts = url.split("/")
            if len(url_parts) >= 2:
                product_id = url_parts[-2]
                brand = url_parts[-1]
                filename = f"{product_id}_{brand}.html"

                output_file = category_html_dir / filename

                # Проверяем, существует ли файл
                if output_file.exists():
                    logger.info(
                        f"[{i}/{total}] Файл {filename} уже существует, пропускаем"
                    )
                    continue

                logger.info(f"[{i}/{total}] Скачиваем {url}")
                html_content = self.get_page(url)

                if html_content:
                    try:
                        with open(output_file, "w", encoding="utf-8") as f:
                            f.write(html_content)
                        logger.info(f"Сохранено в {output_file}")
                    except Exception as e:
                        logger.error(f"Ошибка при сохранении {filename}: {e}")

                # Делаем паузу между запросами
                time.sleep(random.uniform(1.5, 4.0))
            else:
                logger.warning(f"Некорректный URL: {url}")

    def run(self):
        """Запускает полный процесс сбора и скачивания"""
        logger.info(f"Обрабатываем категорию: {self.category_url}")

        logger.info("Начинаем сбор ссылок на товары...")
        self.collect_all_product_links()

        logger.info("Начинаем скачивание страниц товаров...")
        self.download_product_pages()

        logger.info(f"Обработка категории {self.category_url} завершена!")


def read_categories(file_path):
    """Чтение списка категорий из файла"""
    categories = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            categories = [line.strip() for line in f if line.strip()]
        logger.info(f"Загружено {len(categories)} категорий из файла")
    except Exception as e:
        logger.error(f"Ошибка при чтении файла категорий: {e}")
    return categories


if __name__ == "__main__":
    # Путь к файлу с категориями

    if not categories_file.exists():
        logger.error(f"Файл с категориями не найден: {categories_file}")
        sys.exit(1)

    # Чтение категорий из файла
    categories = read_categories(categories_file)

    # Обработка каждой категории
    for i, category in enumerate(categories, 1):
        logger.info(f"Обработка категории {i}/{len(categories)}: {category}")

        # Форматируем URL категории
        category_url = f"/{category}"

        # Создаем скрапер для текущей категории
        scraper = AltStarScraper(category_url=category_url)

        # Запускаем процесс
        scraper.run()

        # Пауза между обработкой категорий
        if i < len(categories):
            sleep_time = random.uniform(5.0, 10.0)
            logger.info(f"Пауза {sleep_time:.1f} секунд перед следующей категорией...")
            time.sleep(sleep_time)

    logger.info("Обработка всех категорий завершена!")
