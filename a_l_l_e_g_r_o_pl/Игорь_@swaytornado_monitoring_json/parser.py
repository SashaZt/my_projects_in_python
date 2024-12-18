import json
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import demjson3
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from tqdm import tqdm


class Parser:

    def __init__(
        self,
        html_files_directory,
        max_workers,
    ):
        self.html_files_directory = html_files_directory
        self.max_workers = max_workers

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

        # logger.info(f"Всего файлов для обработки: {len(file_list)}")
        return file_list

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
                "div", string=lambda text: text and "osob" in text
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
        except Exception as e:
            logger.error(f"Ошибка при извлечении информации о покупке: {e}")
            return None

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

    # def parse_single_html(self, file_html):
    #     """Парсит один HTML-файл для извлечения данных о продукте.

    #     Args:
    #         file_html (Path): Путь к HTML-файлу.

    #     Returns:
    #         dict or None: Словарь с данными о продукте или None, если данные не найдены.
    #     """
    #     with open(file_html, encoding="utf-8") as file:
    #         src = file.read()
    #     soup = BeautifulSoup(src, "lxml")
    #     data_monotoring = {
    #         "Actuall": True,
    #         "ID_MP": self.pares_iditem(soup),
    #         "Цена, ZLT": self.parse_price_product(soup),
    #         "Sales": self.parse_sales_product(soup),
    #         "Sales_all": self.parse_sales_all_product(soup),
    #         "Остатки на складах": self.parse_warehouse_balances(soup),
    #     }
    #     return data_monotoring

    def parsing_json(self):
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
            # ПОСЕЛ ТЕСТА ОТКРЫТЬ
            # futures = {
            #     executor.submit(self.parse_single_html, file_html): file_html
            #     for file_html in all_files
            # }
            futures = {
                executor.submit(self.parse_single_html_json, file_html): file_html
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

    def extract_price_json(self, soup):
        """
        Извлекает JSON из всех <script type="application/json"> с началом '{"price":{"formattedPric'.
        Для productid
        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Список JSON-объектов или пустой список, если данные не найдены
        """

        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
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
                number = None
                return number
        except Exception as e:
            return {"error": f"Ошибка при извлечении данных: {e}"}

    def parse_name_product(self, soup):
        """Извлекает название продукта."""
        name_tag = soup.find("meta", itemprop="name")
        return name_tag["content"] if name_tag else None

    def parse_url_product(self, soup):
        """Извлекает URL продукта."""
        url_tag = soup.find("meta", itemprop="url")
        return url_tag["content"] if url_tag else None

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

    def extract_breadcrumbs_json(self, soup):
        """
        Извлекает JSON из всех <script type="application/json"> с началом '{"price":{"formattedPric'.
        Для productid
        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Список JSON-объектов или пустой список, если данные не найдены
        """

        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
            if script.string and script.string.strip().startswith('{"breadcrumbs'):
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

    def pares_productid(self, soup):
        """
        Извлекает идентификатор продукта (productId) из JSON <script>.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Идентификатор продукта (productId) или None, если данные не найдены
        """
        # Извлекаем JSON из <script> с sourceType:product
        json_data = self.extract_breadcrumbs_json(soup)

        try:
            # Проверяем, что json_data — это словарь
            if isinstance(json_data, dict):
                # Получаем список breadcrumbs
                breadcrumbs = json_data.get("breadcrumbs", [])

                # Проверяем, что список не пуст, и извлекаем последний элемент
                if breadcrumbs:
                    last_breadcrumb = breadcrumbs[-1]  # Последний элемент
                    last_id = last_breadcrumb.get("id", "ID not found")  # Извлекаем id
                    if last_id is not None:
                        return last_id

            # logger.warning(
            #     "JSON data не является словарём или не содержит productId. Возвращён None."
            # )
            return None

        except Exception as e:
            logger.error(f"Произошла ошибка при извлечении productId: {e}")
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
            # Проверяем, является ли json_data списком и имеет ли он хотя бы один элемент
            if isinstance(json_data, list) and len(json_data) > 0:
                # Безопасно извлекаем sellerId через метод get
                sellername = json_data[0].get("sellerId")
                return sellername if sellername else None

        return None

    def extract_seller_json(self, soup):
        """
        Для productid
        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Список JSON-объектов или пустой список, если данные не найдены
        """

        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
            if script.string and script.string.strip().startswith('{"sellerName'):
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

    def pares_sellername(self, soup):
        """
        ТУТ ЕЩЕ КАТЕГОРИИ
        Извлекает имя продавца (sellerName) из dataLayer JSON.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Имя продавца (sellerName) или None, если данные не найдены
        """
        # Извлекаем JSON из dataLayer
        json_data = self.extract_seller_json(soup)

        # Безопасное извлечение имени продавца
        try:
            if "sellerName" in json_data:
                seller_name = json_data.get("sellerName")
                return seller_name if seller_name else None
        except Exception as e:
            # Логирование или обработка ошибок при необходимости
            pass

        return None

    def extract_photo_json(self, soup):
        """
        Извлекает JSON из всех <script type="application/json"> с началом '{"price":{"formattedPric'.
        Для productid
        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Список JSON-объектов или пустой список, если данные не найдены
        """

        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
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

    def extract_description(self, soup):
        json_data = self.extract_photo_json(soup)

        # Список для хранения всех извлеченных элементов из "sections"
        sections_list = []
        # Проходим по каждому элементу в "sections"
        for section in json_data.get("standardized", {}).get("sections", []):

            section_items = {"items": []}

            for item in section.get("items", []):
                item_data = {}

                if item.get("type") == "IMAGE":
                    item_data = {
                        "type": "IMAGE",
                        "alt": item.get("alt"),
                        "url": item.get("url"),
                    }
                elif item.get("type") == "TEXT":
                    item_data = {"type": "TEXT", "content": item.get("content")}

                # Добавляем данные об элементе, если они существуют
                if item_data:
                    section_items["items"].append(item_data)

            if section_items["items"]:
                sections_list.append(section_items)
        return sections_list

    def pares_seller_rating(self, soup):
        """
        Извлекает рейтинг продавца (sellerRating) из dataLayer JSON.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Рейтинг продавца (sellerRating) в виде float или None, если данные не найдены
        """
        # Извлекаем JSON из dataLayer
        json_data = self.extract_seller_json(soup)

        # Безопасно извлекаем значение "sellerRating"
        rating = json_data.get("sellerRating")

        # Если значение найдено, заменяем запятую на точку и убираем знак процента, затем преобразуем в число
        if rating:
            rating = rating.replace(",", ".").replace("%", "")
            try:
                return float(rating)
            except ValueError:
                return None

        return None

    def extract_breadcrumbs(self, soup):
        json_data = self.extract_breadcrumbs_json(soup)

        breadcrumbs_list = []

        # Проходим по каждому элементу в "breadcrumbs"
        for breadcrumb in json_data.get("breadcrumbs", []):
            # Извлекаем "id", "name" и "url"
            id_br = breadcrumb.get("id")
            name = breadcrumb.get("name")
            url = breadcrumb.get("url")

            # Добавляем элемент в список, если все три поля существуют
            if id_br and name and url:
                breadcrumbs_list.append({"id": id_br, "name": name, "url": url})

        return breadcrumbs_list

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

    def pares_reviews_rating(self, soup):
        """
        Извлекает идентификатор продукта (productId) из JSON <script>.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Идентификатор продукта (productId) или None, если данные не найдены
        """
        # Извлекаем JSON из <script> с sourceType:product
        json_data = self.extract_product_json(soup)
        try:
            if isinstance(json_data, dict):
                # Извлекаем ratingDistribution
                rating_distribution = json_data.get("ratingDistribution", None)

                return rating_distribution

            # logger.warning(
            #     "JSON data не является словарём или не содержит productId. Возвращён None."
            # )
            return None

        except Exception as e:
            logger.error(f"Произошла ошибка при извлечении reviews_rating: {e}")
            return None

    def pares_reviews(self, soup):
        """
        Извлекает идентификатор продукта (productId) из JSON <script>.

        :param soup: Объект BeautifulSoup для HTML-страницы
        :return: Идентификатор продукта (productId) или None, если данные не найдены
        """
        # Извлекаем JSON из <script> с sourceType:product
        json_data = self.extract_product_json(soup)
        try:
            if isinstance(json_data, dict):
                reviews = []
                for review in json_data.get("reviews", []):

                    # Извлекаем "id", "name" и "url"
                    review_text = review.get("content")
                    review_score = review.get("rating")
                    review_date = review.get("datePublished")

                    # Добавляем элемент в список, если все три поля существуют
                    if review_text and review_score and review_date:
                        reviews.append(
                            {
                                "text": review_text,
                                "score": review_score,
                                "date": review_date,
                            }
                        )

                return reviews
            # logger.warning(
            #     "JSON data не является словарём или не содержит pares_reviews. Возвращён None."
            # )
            return None
        except Exception as e:
            logger.error(f"Произошла ошибка при извлечении pares_reviews: {e}")
            return None

    def extract_last_three_urls(self, soup):
        """
        Извлекает последние три URL из списка словарей и возвращает их в виде именованных элементов.

        :param data: Список словарей, содержащих "id", "name" и "url"
        :return: Словарь с именами "parent_directory", "directory" и "file"
        """
        data = self.extract_breadcrumbs(soup)
        # logger.info(data)
        if len(data) < 3:
            raise ValueError("Входной список должен содержать минимум 3 элемента.")

        # Извлекаем последние три элемента
        parent_directory = data[1]["url"].split("/")[-1]
        directory = data[2]["url"].split("/")[-1]
        file_raw = data[-1]["url"].split("/")[-1]
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        match = re.search(uuid_pattern, file_raw)
        file = self.pares_productid(soup)
        # Формируем итоговый словарь
        names = {
            "parent_directory": parent_directory,
            "directory": directory,
            "file": file,
        }
        # logger.info(names)

        return names

    def get_current_date(self):
        """
        Возвращает текущую дату в формате YYYY-MM-DD.

        :return: Строка с текущей датой
        """
        return datetime.now().strftime("%Y-%m-%d")

    def parse_single_html_json(self, file_html):
        """Парсит один HTML-файл для извлечения данных о продукте.

        Args:
            file_html (Path): Путь к HTML-файлу.

        Returns:
            dict or None: Словарь с данными о продукте или None, если данные не найдены.
        """
        with open(file_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        parametry = self.extract_params(soup)
        with open(file_html, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")
        all_data = {
            "success": True,
            "id": self.pares_iditem(soup),
            "title": self.parse_name_product(soup),
            "url": self.parse_url_product(soup),
            "active": True,
            "price": self.parse_price_product(soup),
            "price_with_delivery": 0,
            "availableQuantity": self.parse_warehouse_balances(soup),
            "buyers": self.parse_other_product_offers(soup),
            "rating": self.parse_average_rating(soup),
            "reviews_count": self.parse_number_of_reviews(soup),
            "same_offers_id": self.pares_productid(soup),
            "same_offers_count": self.parse_other_product_offers(soup),
            "seller_id": self.pares_sellerid(soup),
            "seller_login": self.pares_sellername(soup),
            "seller_rating": "",
            "seller_positive_count": "",
            "seller_negative_count": "",
            "delivery_options": {
                "Odbiór w punkcie": {
                    "Punkt DHL POP, DHL": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Automat DHL BOX 24/7, DHL": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Poczta Polska, Allegro Pocztex": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Żabka, Allegro Pocztex": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Lewiatan, Allegro Pocztex": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Sklep ABC, Allegro Pocztex": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Delikatesy Centrum, Allegro Pocztex": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Allegro One Box, Allegro One": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Allegro One Punkt, Allegro One": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Kolporter, Allegro One": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Epaka, Allegro One": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Automat ORLEN Paczka, ORLEN Paczka": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Punkt Orlen Paczka, ORLEN Paczka": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Furgonetka, Allegro One": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Auchan, Allegro One": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Pakersi, Allegro One": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Bonito, Allegro One": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Automat Pocztex, Allegro Pocztex": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Paczkomat InPost, InPost": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "PaczkoPunkt InPost, InPost": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                },
                "Na adres": {
                    "Kurier, DPD": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Kurier": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                },
                "Na adres za pobraniem": {
                    "Kurier pobranie, DPD": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                    "Kurier pobranie": {
                        "price": "",
                        "price_next_item": "",
                        "package_size": "",
                        "time": "",
                    },
                },
            },
            "currency": "PLN",
            "category_path": [
                {"id": "", "name": "", "url": ""},
                {"id": "", "name": "", "url": ""},
                {"id": "", "name": "", "url": ""},
                {"id": "", "name": "", "url": ""},
                {"id": "", "name": "", "url": ""},
                {"id": "", "name": "", "url": ""},
            ],
            "specifications": {"Parametry": {}},
            "images": [
                {"original": "", "thumbnail": "", "embeded": "", "alt": ""},
                {"original": "", "thumbnail": "", "embeded": "", "alt": ""},
                {"original": "", "thumbnail": "", "embeded": "", "alt": ""},
                {"original": "", "thumbnail": "", "embeded": "", "alt": ""},
                {"original": "", "thumbnail": "", "embeded": "", "alt": ""},
                {"original": "", "thumbnail": "", "embeded": "", "alt": ""},
            ],
            "description": {
                "sections": [
                    {
                        "items": [
                            {"type": "", "alt": "", "url": ""},
                            {"type": "", "content": ""},
                        ]
                    },
                    {"items": [{"type": "", "content": ""}]},
                    {"items": [{"type": "", "content": ""}]},
                    {"items": [{"type": "", "content": ""}]},
                    {"items": [{"type": "", "content": ""}]},
                    {"items": [{"type": "", "content": ""}]},
                    {
                        "items": [
                            {"type": "", "alt": "", "url": ""},
                            {"type": "", "alt": "", "url": ""},
                        ]
                    },
                    {
                        "items": [
                            {"type": "", "alt": "", "url": ""},
                            {"type": "", "alt": "", "url": ""},
                        ]
                    },
                    {
                        "items": [
                            {"type": "", "alt": "", "url": ""},
                            {"type": "", "alt": "", "url": ""},
                        ]
                    },
                    {"items": [{"type": "", "content": ""}]},
                ]
            },
            "reviews_rating": {  # Opinie o produkcie
                "5": {"count": "", "percentage": ""},
                "4": {"count": "", "percentage": ""},
                "3": {"count": "", "percentage": ""},
                "2": {"count": "", "percentage": ""},
                "1": {"count": "", "percentage": ""},
            },
            "reviews": [
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
                {"text": "", "score": "", "date": ""},
            ],
            "compatibility": [],
        }
        # Обновляем "all_data" с измененными параметрами
        all_data["specifications"]["Parametry"] = parametry
        # logger.info(parametry)
        seller_rating = self.pares_seller_rating(soup)
        all_data["seller_rating"] = seller_rating

        # br = self.extract_breadcrumbs(soup)
        all_data["category_path"] = self.extract_breadcrumbs(soup)
        all_data["images"] = self.extract_images(soup)
        all_data["description"]["sections"] = self.extract_description(soup)
        # logger.info(br)
        all_data["reviews_rating"] = self.pares_reviews_rating(soup)
        all_data["reviews"] = self.pares_reviews(soup)
        all_names_folders_and_file = self.extract_last_three_urls(soup)
        data_folder = self.get_current_date()

        parent_directory = (
            self.json_products
            / f'{data_folder}-{all_names_folders_and_file["parent_directory"]}'
        )
        directory = (
            parent_directory
            / f'{data_folder}-{all_names_folders_and_file["directory"]}'
        )

        parent_directory.mkdir(parents=True, exist_ok=True)
        directory.mkdir(parents=True, exist_ok=True)

        json_result = directory / f'{all_names_folders_and_file["file"]}.json'
        with open(json_result, "w", encoding="utf-8") as json_file:
            json.dump(all_data, json_file, indent=4, ensure_ascii=False)
