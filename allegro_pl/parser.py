import json
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm

# Указать путь к .env файлу
env_path = os.path.join(os.getcwd(), "configuration", ".env")

# Используем строку "20" как значение по умолчанию
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "20"))
# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"


class Parser:

    def __init__(self, html_files_directory, html_page_directory, csv_output_file):
        self.html_files_directory = html_files_directory
        self.html_page_directory = html_page_directory
        self.csv_output_file = csv_output_file

    def parsin_page(self):
        max_page = None
        html_company = self.html_page_directory / "url_start.html"

        with open(html_company, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")

        pagination_div = soup.find("div", {"aria-label": "paginacja"})
        if pagination_div:
            span_element = pagination_div.find("span")
            if span_element:
                try:
                    max_page_text = span_element.get_text(strip=True)
                    max_page = int(max_page_text)
                except ValueError:
                    logger.error("Не удалось преобразовать max_page_text в число")
            else:
                logger.error(
                    "Элемент span не найден или не является объектом BeautifulSoup"
                )
        else:
            logger.error("Элемент div с aria-label='paginacja' не найден")

        return max_page

    # Добавьте сюда другие функции для парсинга
    def parsing_html(self):
        """Выполняет многопоточный парсинг всех HTML-файлов в директории.

        Returns:
            list: Список словарей с данными о продуктах из всех файлов.
        """

        all_files = self.list_html()
        # Инициализация прогресс-бараedrpou.csv
        total_urls = len(all_files)
        progress_bar = tqdm(
            total=total_urls,
            desc="Обработка файлов",
            bar_format="{l_bar}{bar} | Время: {elapsed} | Осталось: {remaining} | Скорость: {rate_fmt}",
        )

        # Многопоточная обработка файлов
        all_results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.parse_single_html, file_html): file_html
                for file_html in all_files
            }

            # Сбор результатов по мере завершения каждого потока
            for future in as_completed(futures):
                file_html = futures[future]
                try:
                    result = future.result()
                    if result is not None:
                        all_results.append(result)
                except Exception as e:
                    logger.error(
                        f"Ошибка при обработке файла {
                        file_html}: {e}"
                    )
                    # Добавление трассировки стека
                    logger.error(traceback.format_exc())
                finally:
                    # Обновляем прогресс-бар после завершения обработки каждого файла
                    progress_bar.update(1)

        # Закрываем прогресс-бар
        progress_bar.close()
        return all_results

    def list_html(self):
        """Возвращает список HTML-файлов в заданной директории.

        Returns:
            list: Список файлов (Path) в директории html_files_directory.
        """

        # Получаем список всех файлов в html_files_directory
        file_list = [
            file for file in self.html_files_directory.iterdir() if file.is_file()
        ]

        logger.info(f"Всего файлов для обработки: {len(file_list)}")
        return file_list

    def parse_single_html(self, file_html):
        """Парсит один HTML-файл для извлечения данных о продукте.

        Args:
            file_html (Path): Путь к HTML-файлу.

        Returns:
            dict or None: Словарь с данными о продукте или None, если данные не найдены.
        """
        with open(file_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")

        company_data = {
            "EAN_product": self.parse_ean_product(soup),
            "brand_product": self.parse_brand_product(soup),
            "name_product": self.parse_name_product(soup),
            "url_product": self.parse_url_product(soup),
            "price_product": self.parse_price_product(soup),
            "sales_product": self.parse_sales_product(soup),
            "weight_product": self.parse_weight_product(soup),
            "condition": self.parse_condition(soup),
            "warehouse_balances": self.parse_warehouse_balances(soup),
            "average_rating": self.parse_average_rating(soup),
        }

        return company_data

    def parse_ean_product(self, soup):
        """Извлекает EAN продукта."""
        ean_tag = soup.find("meta", itemprop="gtin")
        return ean_tag["content"] if ean_tag else None

    def parse_brand_product(self, soup):
        """Извлекает бренд продукта."""
        brand_tag = soup.find("meta", itemprop="brand")
        return brand_tag["content"] if brand_tag else None

    def parse_name_product(self, soup):
        """Извлекает название продукта."""
        name_tag = soup.find("meta", itemprop="name")
        return name_tag["content"] if name_tag else None

    def parse_url_product(self, soup):
        """Извлекает URL продукта."""
        url_tag = soup.find("meta", itemprop="url")
        return url_tag["content"] if url_tag else None

    def parse_price_product(self, soup):
        """Извлекает цену продукта."""
        price_tag = soup.find("meta", itemprop="price")
        return price_tag["content"] if price_tag else None

    def parse_sales_product(self, soup):
        """Извлекает количество продаж продукта."""
        sales_tag = soup.find(string=lambda text: text and "tę ofertę" in text)
        if sales_tag:
            sales_text = sales_tag.strip()
            sales_number = "".join(filter(str.isdigit, sales_text))
            return int(sales_number) if sales_number else None
        return None

    def parse_average_rating(self, soup):
        """Извлекает средний рейтинг продукта."""
        rating_tag = soup.find(
            "span", {"aria-label": lambda value: value and value.startswith("ocena:")}
        )
        if rating_tag:
            rating_text = rating_tag.text.strip()
            return rating_text
        return None

    def parse_weight_product(self, soup):
        """Извлекает вес продукта."""
        weight_tag = soup.find(
            "td", string=lambda text: text and "Waga produktu" in text
        )
        if weight_tag:
            weight_value_tag = weight_tag.find_next_sibling("td")
            if weight_value_tag:
                weight_text = weight_value_tag.text.strip()
                return weight_text
        return None

    def parse_condition(self, soup):
        """Извлекает состояние продукта."""
        condition_tag = soup.find("meta", itemprop="itemCondition")
        return condition_tag["content"].split("/")[-1] if condition_tag else None

    def parse_warehouse_balances(self, soup):
        """Извлекает количество товара на складе."""
        script_tags = soup.find_all("script", type="application/json")
        for script_tag in script_tags:
            try:
                data = json.loads(script_tag.string)
                if isinstance(data, dict):
                    # Проверка в структуре данных на наличие количества товара
                    if (
                        "watchButtonProps" in data
                        and "watchEventCustomParams" in data["watchButtonProps"]
                    ):
                        item_data = data["watchButtonProps"][
                            "watchEventCustomParams"
                        ].get("item", {})
                        if "quantity" in item_data:
                            return item_data["quantity"]
            except (json.JSONDecodeError, TypeError, KeyError):
                continue
        return None

    def get_url_html_csv(self):
        # Инициализируем set для хранения уникальных ссылок
        unique_links = set()
        for html_file in self.html_page_directory.glob("*.html"):
            # Открываем локально сохранённый файл первой страницы
            with open(html_file, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, "lxml")
            # Находим контейнер для всех товаров
            search_results_div = soup.select_one(
                "#search-results > div:nth-child(5) > div > div > div > div > div > div"
            )

            # Проверяем каждый <article> элемент с учетом диапазона от 2 до 73
            if search_results_div:
                # Проверяем, что контейнер найден и содержит достаточное количество article
                articles = search_results_div.find_all("article")

                for ar in articles:
                    # Ищем ссылку внутри целевого article
                    link = ar.find("a", href=True)
                    # Проверяем, что ссылка найдена, и добавляем в set
                    if link:
                        unique_links.add(link["href"])
        logger.info(len(unique_links))
        # Преобразуем set в DataFrame и сохраняем в CSV
        df = pd.DataFrame(list(unique_links), columns=["url"])
        df.to_csv(self.csv_output_file, index=False, encoding="utf-8")

        logger.info(f"Ссылки успешно сохранены в {self.csv_output_file}")

    # def parsin_page(self):
    #     max_page = None
    #     html_company = html_page_directory / "url_start.html"

    #     # Открываем локально сохранённый файл первой страницы
    #     with open(html_company, encoding="utf-8") as file:
    #         src = file.read()
    #     soup = BeautifulSoup(src, "lxml")

    #     # Находим div с атрибутом aria-label="paginacja"
    #     pagination_div = soup.find("div", {"aria-label": "paginacja"})

    #     # Извлекаем максимальное количество страниц
    #     if pagination_div:
    #         span_element = pagination_div.find("span")
    #         if span_element:
    #             try:
    #                 max_page_text = span_element.get_text(strip=True)
    #                 max_page = int(max_page_text)
    #             except ValueError:
    #                 logger.error("Не удалось преобразовать max_page_text в число")
    #         else:
    #             logger.error(
    #                 "Элемент span не найден или не является объектом BeautifulSoup"
    #             )
    #     else:
    #         logger.error("Элемент div с aria-label='paginacja' не найден")

    #     return max_page
