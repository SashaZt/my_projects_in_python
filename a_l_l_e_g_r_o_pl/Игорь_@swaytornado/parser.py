import json
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import demjson3
import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm


class Parser:

    def __init__(
        self,
        html_files_directory,
        html_page_directory,
        csv_output_file,
        max_workers,
        json_files_directory,
        json_page_directory,
    ):
        self.html_files_directory = html_files_directory
        self.html_page_directory = html_page_directory
        self.csv_output_file = csv_output_file
        self.max_workers = max_workers
        self.json_files_directory = json_files_directory
        self.json_page_directory = json_page_directory

    def parsing_page_max_page(self, src):
        """Парсит HTML-страницу и возвращает максимальный номер страницы из блока пагинации.

        Args:
            src (str): HTML-код страницы, который необходимо распарсить.

        Returns:
            int: Максимальный номер страницы, найденный в блоке пагинации, или 1, если пагинация отсутствует.
        """
        soup = BeautifulSoup(src, "lxml")
        pagination_div = soup.find("ul", {"aria-label": "paginacja"})
        max_page = 1  # Значение по умолчанию, если пагинации нет
        if pagination_div:
            span_element = pagination_div.find("span")
            if span_element:
                try:
                    max_page_text = span_element.get_text(strip=True)
                    max_page = int(max_page_text)
                except ValueError:
                    logger.error("Не удалось преобразовать max_page_text в число")
            else:
                logger.error("Элемент span не найден в пагинации")
        else:
            logger.error("Элемент пагинации не найден")

        return max_page

    def parsin_page_json(self, src, page_number):
        """
        Находит первый тег <script type="application/json">, который начинается с '{"__listing_StoreState'`.
        Преобразует содержимое тега в JSON, исправляет распространённые проблемы и извлекает URL через parse_listing_store_state.

        :param src: HTML-код страницы
        :return: Список URL или None, если данные не найдены
        """
        soup = BeautifulSoup(src, "lxml")

        # Поиск всех тэгов <script type="application/json">
        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
            if script.string and script.string.strip().startswith(
                '{"__listing_StoreState'
            ):
                try:
                    # Читаем содержимое и исправляем распространённые проблемы
                    raw_content = script.string

                    # Исправляем 'True', 'False', 'None' в корректные JSON-значения
                    corrected_content = re.sub(r"\bTrue\b", "true", raw_content)
                    corrected_content = re.sub(r"\bFalse\b", "false", corrected_content)
                    corrected_content = re.sub(r"\bNone\b", "null", corrected_content)

                    # Разбираем исправленный JSON
                    json_data = demjson3.decode(corrected_content, strict=False)

                    # Логируем успешную загрузку JSON
                    json_result = (
                        self.json_page_directory / f"result_{page_number}.json"
                    )
                    # Записываем JSON в файл для проверки
                    with open(json_result, "w", encoding="utf-8") as json_file:
                        json.dump(json_data, json_file, indent=4, ensure_ascii=False)

                    # Загружаем JSON из файла для теста
                    with open(json_result, "r", encoding="utf-8") as json_file:
                        loaded_json_data = json.load(json_file)
                    # Извлекаем URL через parse_listing_store_state
                    return self.parse_listing_store_state(loaded_json_data)

                except demjson3.JSONDecodeError as e:
                    # Логируем ошибку при декодировании JSON
                    logger.error(f"Ошибка")
                    return None

        # Логируем отсутствие подходящего JSON
        return None

    def parse_listing_store_state(self, json_data):
        """
        Парсит JSON-данные из __listing_StoreState, извлекает URL, если count >= 50.

        :param json_data: JSON-объект, содержащий __listing_StoreState
        :return: Список URL, где count >= 50
        """
        urls = set()

        try:
            # Navigate to elements under items
            elements = json_data["__listing_StoreState"]["items"]["elements"]

            for element in elements:
                # Extract URL
                url = element.get("url", None)

                # Extract productPopularity label and parse count
                product_popularity = element.get("productPopularity", {})
                label = product_popularity.get("label", "")

                # Extract the numeric value from the label (e.g., "614 osób kupiło ostatnio")
                count = None
                # Регулярное выражение для извлечения числа перед 'osoby', 'osób', или 'osoba'
                match = re.search(r"(\d+)\s+(osoby|osób|osoba)", label)
                count = int(match.group(1)) if match else 0
                if count >= 50 and url:
                    urls.add(url)

        except KeyError as e:
            pass
        except Exception as e:
            pass

        return urls

    # def parsin_page(self, src):
    #     """Парсит HTML-страницу и извлекает ссылки на статьи с числом упоминаний "osób" больше или равно 50.

    #     Args:
    #         src (str): HTML-код страницы, который необходимо распарсить.

    #     Returns:
    #         set: Множество URL-адресов, извлеченных из статей, соответствующих условию.
    #     """
    #     soup = BeautifulSoup(src, "lxml")
    #     url_r = set()

    #     result = soup.find_all("span", string=lambda t: t and "osób" in t)
    #     for rs in result:
    #         osob = int(rs.text.replace(" osób", ""))
    #         if osob >= 50:
    #             article = rs.find_parent("article")
    #             if article:
    #                 link_raw = article.find("a", href=True)
    #                 if link_raw:
    #                     url_r.add(link_raw["href"])

    #     return url_r

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
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
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
                    logger.error(f"Ошибка при обработке файла {file_html}: {e}")
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
        foto_01 = self.parse_foto_01(soup)
        fotos = self.parse_photos(soup)
        max_photos = 9  # Максимальное количество полей Фото_X в company_data
        company_data = {
            "Категория": self.pares_category(soup),
            "ShopID": self.pares_sellerid(soup),
            "Наш ID": f"{self.pares_productid(soup)}-{self.pares_iditem(soup)}",
            "ID_MP": self.pares_iditem(soup),
            "SO_ID": self.pares_productid(soup),
            "SO_CNT": self.parse_other_product_offers(soup),
            "EAN": self.parse_ean_product(soup),
            "Марка": self.parse_brand_product(soup),
            "Название товара": self.parse_name_product(soup),
            "URL": self.parse_url_product(soup),
            "Дата": self.get_current_date(),
            "FOTO_1": foto_01.replace("s512", "original"),
            "Цена, ZLT": self.parse_price_product(soup),
            "Цена, $": "",
            "Sales": self.parse_sales_product(soup),
            "Sales_all": self.parse_sales_all_product(soup),
            "All_Buyers": self.parse_other_product_offers(soup),
            "Вес": "",
            "Длина": "",
            "Ширина": "",
            "Высота": "",
            "FOTO_0": foto_01.replace("s512", "s360"),
            "Состояние": self.parse_condition(soup),
            "Остатки на складах": self.parse_warehouse_balances(soup),
            "Средняя оценка": self.parse_average_rating(soup),
            "Количество оценок": self.parse_number_ratings(soup),
            "Количество отзывов": self.parse_number_of_reviews(soup),
            "Описание": self.extract_description_texts(soup),
            # "sellername": self.pares_sellername(soup),  # В JSON
        }
        # Заполнение полей Фото_1 - Фото_9
        for i in range(min(len(fotos), max_photos)):
            company_data[f"Фото_{i + 1}"] = fotos[i]

        return company_data

    def parse_foto_01(self, soup):
        """
        Извлекает ссылку на изображение из тега <link> с атрибутом as="image".

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Строка с URL изображения или None, если элемент не найден
        """
        ean_tag = soup.find("link", {"as": "image"})  # Поиск тега с указанным атрибутом
        return ean_tag["href"] if ean_tag and "href" in ean_tag.attrs else None

    def get_current_date(self):
        """
        Возвращает текущую дату в формате YYYY-MM-DD.

        :return: Строка с текущей датой
        """
        return datetime.now().strftime("%Y-%m-%d")

    def pares_sellername(self, soup):
        """
        Извлекает имя продавца (sellerName) из dataLayer JSON.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Имя продавца (sellerName) или None, если данные не найдены
        """
        # Извлекаем JSON из dataLayer
        json_data = self.extract_datalayer_json(soup)

        if json_data:
            # Безопасно извлекаем sellerName через метод get
            sellername = (
                json_data[0].get("sellerName") if isinstance(json_data, list) else None
            )
            return sellername

        return None

    def pares_sellerid(self, soup):
        """
        Извлекает имя продавца (sellerName) из dataLayer JSON.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Имя продавца (sellerName) или None, если данные не найдены
        """
        # Извлекаем JSON из dataLayer
        json_data = self.extract_datalayer_json(soup)

        if json_data:
            # Безопасно извлекаем sellerName через метод get
            sellername = (
                json_data[0].get("sellerId") if isinstance(json_data, list) else None
            )
            return sellername

        return None

    def parse_other_product_offers(self, soup):
        """
        Извлекает данные из объекта `otherProductOffers` в JSON.

        :param json_data: Данные JSON.
        :return: Словарь с `productId` и `linkName` или сообщение об отсутствии данных.
        """
        json_data = self.extract_price_json(soup)
        try:
            # Проверяем наличие ключа `otherProductOffers` в JSON
            other_product_offers = json_data.get("otherProductOffers", {})
            if other_product_offers:
                # product_id = other_product_offers.get("productId", "Не найдено")
                link_name = other_product_offers.get("linkName", "Не найдено")
                match = re.search(r"\d+", link_name)
                number = None
                if match:
                    number = int(match.group(0))  # Преобразуем найденное число в int
                return number
            else:
                return {"error": "Данные `otherProductOffers` отсутствуют"}
        except Exception as e:
            return {"error": f"Ошибка при извлечении данных: {e}"}

    def pares_iditem(self, soup):
        """
        Извлекает имя продавца (sellerName) из dataLayer JSON.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Имя продавца (sellerName) или None, если данные не найдены
        """
        # Извлекаем JSON из dataLayer
        json_data = self.extract_datalayer_json(soup)

        if json_data:
            # Безопасно извлекаем sellerName через метод get
            sellername = (
                json_data[0].get("idItem") if isinstance(json_data, list) else None
            )
            return sellername

        return None

    def pares_productid(self, soup):
        """
        Извлекает идентификатор продукта (productId) из JSON <script>.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Идентификатор продукта (productId) или None, если данные не найдены
        """
        # Извлекаем JSON из <script> с sourceType:product
        json_data = self.extract_product_json(soup)

        try:
            # Проверяем, что json_data — это словарь
            if isinstance(json_data, dict):
                product_id = json_data.get("productId")
                return product_id

            logger.warning("JSON data не является словарём. Возвращён None.")
            return None

        except Exception as e:
            logger.error(f"Произошла ошибка при извлечении productId: {e}")
            return None

    def parse_photos(self, soup):
        json_data = self.extract_photo_json(soup)
        image_urls = []
        for section in json_data.get("standardized", {}).get("sections", []):
            for item in section.get("items", []):
                if item.get("type") == "IMAGE":
                    image_urls.append(item.get("url"))
        return image_urls

    """
    Блок извлечения из страницы все json
    """

    def extract_datalayer_json(self, soup):
        """
        Извлекает JSON из тега <script>, содержащего 'dataLayer='.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Python-объект, разобранный из JSON, или None, если данные не найдены
        """
        try:
            # Поиск всех тегов <script>
            script_tags = soup.find_all("script")

            for script in script_tags:
                # Используем script.text для извлечения всего содержимого внутри <script>
                if script.text and "dataLayer=" in script.text:
                    # Логируем текст найденного тега

                    # Попробуем извлечь dataLayer с помощью регулярного выражения
                    match = re.search(
                        r"dataLayer\s*=\s*(\[\{.*?\}\])", script.text, re.DOTALL
                    )
                    if match:
                        json_content = match.group(1)  # Извлекаем JSON-строку
                        return json.loads(json_content)  # Преобразуем в Python-объект

            return None

        except json.JSONDecodeError as e:
            return None
        except Exception as e:
            return None

    def extract_product_json(self, soup):
        """
        Извлекает JSON из всех <script type="application/json"> с началом '{"sourceType":"product"}'.
        Для productid
        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Список JSON-объектов или пустой список, если данные не найдены
        """

        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
            # Проверяем, что содержимое начинается с '{"sourceType":"product"'
            if script.string and script.string.strip().startswith(
                '{"sourceType":"product"'
            ):
                try:
                    raw_content = script.string
                    # Исправляем 'True', 'False', 'None' в корректные JSON-значения
                    corrected_content = re.sub(r"\bTrue\b", "true", raw_content)
                    corrected_content = re.sub(r"\bFalse\b", "false", corrected_content)
                    corrected_content = re.sub(r"\bNone\b", "null", corrected_content)
                    # Парсим JSON
                    json_data = demjson3.decode(corrected_content, strict=False)
                    return json_data
                except json.JSONDecodeError as e:
                    # Логируем ошибку декодирования JSON
                    logger.error(f"Ошибка декодирования JSON: {e}")
                    continue

    def extract_price_json(self, soup):
        """
        Извлекает JSON из всех <script type="application/json"> с началом '{"price":{"formattedPric'.
        Для productid
        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Список JSON-объектов или пустой список, если данные не найдены
        """

        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
            # Проверяем, что содержимое начинается с '{"sourceType":"product"'
            if script.string and script.string.strip().startswith(
                '{"price":{"formattedPric'
            ):
                try:
                    raw_content = script.string
                    # Исправляем 'True', 'False', 'None' в корректные JSON-значения
                    corrected_content = re.sub(r"\bTrue\b", "true", raw_content)
                    corrected_content = re.sub(r"\bFalse\b", "false", corrected_content)
                    corrected_content = re.sub(r"\bNone\b", "null", corrected_content)
                    # Парсим JSON
                    json_data = demjson3.decode(corrected_content, strict=False)
                    return json_data
                except json.JSONDecodeError as e:
                    # Логируем ошибку декодирования JSON
                    logger.error(f"Ошибка декодирования JSON: {e}")
                    continue

    def extract_photo_json(self, soup):
        """
        Извлекает JSON из всех <script type="application/json"> с началом '{"price":{"formattedPric'.
        Для productid
        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Список JSON-объектов или пустой список, если данные не найдены
        """

        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
            # Проверяем, что содержимое начинается с '{"sourceType":"product"'
            if script.string and script.string.strip().startswith(
                '{"standardized":{"sections"'
            ):
                try:
                    raw_content = script.string
                    # Исправляем 'True', 'False', 'None' в корректные JSON-значения
                    corrected_content = re.sub(r"\bTrue\b", "true", raw_content)
                    corrected_content = re.sub(r"\bFalse\b", "false", corrected_content)
                    corrected_content = re.sub(r"\bNone\b", "null", corrected_content)
                    # Парсим JSON
                    json_data = demjson3.decode(corrected_content, strict=False)
                    return json_data
                except json.JSONDecodeError as e:
                    # Логируем ошибку декодирования JSON
                    logger.error(f"Ошибка декодирования JSON: {e}")
                    continue

    def pares_category(self, soup):
        """Извлекает EAN продукта."""
        category_tag = soup.select_one(
            "header > div.false > div > div > div > form > div > span > span"
        )
        return category_tag.text if category_tag else None

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

    def parse_sales_all_product(self, soup):
        """Извлекает количество продаж из JSON-данных на странице."""
        script_tags = soup.find_all("script", type="application/json")
        sales_product = None

        for script_tag in script_tags:
            try:
                data = json.loads(script_tag.string)
                if isinstance(data, dict):
                    if (
                        "productPopularityLabel" in data
                        and "label" in data["productPopularityLabel"]
                    ):
                        label_text = data["productPopularityLabel"]["label"]
                        match = re.search(r"(\d+)", label_text)
                        if match:
                            sales_product = int(match.group(1))
                            break
            except (json.JSONDecodeError, TypeError):
                continue

        return sales_product

    def parse_sales_product(self, soup):
        """
        Извлекает информацию о покупке из указанного HTML.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Строка с текстом покупки или None, если элемент не найден
        """
        try:
            # Ищем контейнер data-role="app-container"
            app_container = soup.find("div", {"data-box-name": "summaryOneColumn"})
            if not app_container:
                logger.warning("Контейнер с data-role='app-container' не найден.")
                return None

            # Внутри контейнера ищем div с текстом "osób kupiło"
            target_div = app_container.find(
                "div", string=lambda text: text and "osób kupiło" in text
            )
            # Если элемент найден, возвращаем его текст
            if target_div:
                all_sellers = target_div.get_text(strip=True)
                match = re.search(r"\d+", all_sellers)
                number = None
                if match:
                    number = int(match.group(0))  # Преобразуем найденное число в int
                return number
            else:
                return None
            # # Если текст в дочерних элементах
            # parent_div = app_container.find("div", {"class": "mpof_vs"})
            # if parent_div:
            #     return parent_div.get_text(strip=True)

            # # Если ничего не найдено, возвращаем None
            # logger.warning("Информация о покупках не найдена в app-container.")
            # return None

        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о покупке: {e}")
            return None

    def parse_average_rating(self, soup):
        """Извлекает средний рейтинг из JSON-данных на странице."""
        script_tags = soup.find_all("script", type="application/json")
        average_rating = None

        for script_tag in script_tags:
            try:
                data = json.loads(script_tag.string)
                if isinstance(data, dict):
                    if "rating" in data and "ratingValue" in data["rating"]:
                        average_rating = data["rating"]["ratingValue"]
                        break
            except (json.JSONDecodeError, TypeError):
                continue

        return average_rating

    def parse_number_ratings(self, soup):
        """Извлекает средний рейтинг из JSON-данных на странице."""
        script_tags = soup.find_all("script", type="application/json")
        average_rating = None

        for script_tag in script_tags:
            try:
                data = json.loads(script_tag.string)
                if isinstance(data, dict):
                    if "rating" in data and "ratingValue" in data["rating"]:
                        average_rating = data["rating"]["ratingCount"]
                        break
            except (json.JSONDecodeError, TypeError):
                continue

        return average_rating

    def extract_description_texts(self, soup):
        """
        Извлекает теги (h1, h2, p, b) внутри div с data-box-name="Description".

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Список тегов (элементов BeautifulSoup)
        """
        # Находим div с атрибутом data-box-name="Description"
        description_div = soup.find("div", {"data-box-name": "Description"})

        if not description_div:
            return ""  # Возвращаем пустую строку, если div не найден

        # Извлекаем текстовые теги внутри найденного div
        tags = description_div.find_all(["h1", "h2", "p", "b"])

        # Преобразуем все теги в строки и объединяем их через join
        return "".join(str(tag) for tag in tags)

    def parse_number_of_reviews(self, soup):
        """Извлекает средний рейтинг из JSON-данных на странице."""
        script_tags = soup.find_all("script", type="application/json")
        average_rating = None

        for script_tag in script_tags:
            try:
                data = json.loads(script_tag.string)
                if isinstance(data, dict):
                    if "rating" in data and "ratingValue" in data["rating"]:
                        average_rating = data["rating"]["ratingCountLabel"]
                        match = re.search(r"(\d+)\s+recenzj", average_rating)
                        if match:
                            return int(match.group(1))
                        break
            except (json.JSONDecodeError, TypeError):
                continue

        return average_rating

    def parse_weight_product(self, soup):
        """Извлекает вес продукта."""
        weight_tag = soup.find("td", string=lambda text: text and "Waga" in text)
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

            if search_results_div:
                # Проверяем, что контейнер найден и содержит достаточное количество article
                articles = search_results_div.find_all("article")
                for ar in articles:
                    # Ищем ссылку внутри целевого article
                    link = ar.find("a", href=True)
                    href = link["href"]
                    # Проверяем, что ссылка найдена, содержит нужную часть и добавляем в set
                    if link and "https://allegro.pl/oferta/" in href:
                        unique_links.add(href)
        # Преобразуем set в DataFrame и сохраняем в CSV
        df = pd.DataFrame(list(unique_links), columns=["url"])
        df.to_csv(self.csv_output_file, index=False, encoding="utf-8")

        logger.info(f"Парсинг завершен, ссылки сохранены в {self.csv_output_file}")
