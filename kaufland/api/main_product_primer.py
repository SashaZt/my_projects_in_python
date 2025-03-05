import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from loguru import logger

# Настройка логирования
current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"

logger.remove()
# Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


class KauflandProductAPI:
    """
    Клиент для работы с API товаров Kaufland Marketplace
    """

    def __init__(
        self, client_key, secret_key, base_url="https://sellerapi.kaufland.com/v2"
    ):
        """
        Инициализация клиента API
        """
        self.client_key = client_key
        self.secret_key = secret_key
        self.base_url = base_url

    def sign_request(self, method, uri, body, timestamp):
        """
        Создание подписи для запроса
        """
        plain_text = "\n".join([method, uri, body, str(timestamp)])

        logger.debug(f"Строка для подписи: \n{plain_text}")

        digest_maker = hmac.new(self.secret_key.encode(), None, hashlib.sha256)
        digest_maker.update(plain_text.encode())
        signature = digest_maker.hexdigest()

        logger.debug(f"Создана подпись: {signature}")

        return signature

    def calculate_signature(self, method, uri, body, timestamp):
        """
        Создание подписи для запроса с корректной обработкой Unicode

        :param method: HTTP метод (GET, POST, PATCH, DELETE)
        :param uri: Полный URI запроса
        :param body: Тело запроса (или пустая строка)
        :param timestamp: Unix timestamp
        :return: HMAC подпись
        """
        # Формирование строки для подписи
        plain_text = "\n".join([method, uri, body, str(timestamp)])

        logger.debug(f"Строка для подписи (длина: {len(plain_text)}): \n{plain_text}")

        # Создание HMAC SHA-256 подписи
        message = plain_text.encode("utf-8")
        key = self.secret_key.encode("utf-8")
        signature = hmac.new(key, message, hashlib.sha256).hexdigest()

        logger.debug(f"Создана подпись: {signature}")

        return signature

    def make_request(self, method, endpoint, params=None, data=None, save_to_file=True):
        """
        Выполнение запроса к API

        :param method: HTTP метод (GET, POST, PATCH, DELETE)
        :param endpoint: Конечная точка API (например, "/units/")
        :param params: Параметры запроса для GET
        :param data: Данные для отправки в теле запроса
        :param save_to_file: Флаг для сохранения ответа в файл
        :return: Ответ от API
        """
        # Базовый URL
        base_url = f"{self.base_url}{endpoint}"

        # Создаем запрос с параметрами
        url = base_url
        if params:
            # Добавляем параметры к URL
            url_parts = list(urlparse(url))
            query = urlencode(params)
            url_parts[4] = query
            full_url = urlunparse(url_parts)
        else:
            full_url = url

        # Время для запроса и подписи
        timestamp = int(time.time())

        # Подготовка тела запроса
        if data:
            body = json.dumps(data, ensure_ascii=False)
        else:
            body = ""

        # Создание подписи
        signature = self.calculate_signature(method, full_url, body, timestamp)

        # Подготовка заголовков
        headers = {
            "Accept": "application/json",
            "Shop-Client-Key": self.client_key,
            "Shop-Timestamp": str(timestamp),
            "Shop-Signature": signature,
            "User-Agent": "Inhouse_development",
        }

        # Добавление Content-Type для POST/PATCH/PUT запросов
        if method.upper() in ["POST", "PATCH", "PUT"] and data:
            headers["Content-Type"] = "application/json; charset=utf-8"

        logger.debug(f"Отправка {method} запроса к {full_url}")
        logger.debug(f"Заголовки: {headers}")
        if data:
            logger.debug(f"Тело запроса: {body[:500]}...")

        # Выполнение запроса
        try:
            if data:
                # Используем сырой запрос с явным преобразованием тела в UTF-8
                response = requests.request(
                    method=method.upper(),
                    url=full_url,
                    data=body.encode("utf-8"),
                    headers=headers,
                    timeout=30,
                )
            else:
                # Запрос без тела
                response = requests.request(
                    method=method.upper(), url=full_url, headers=headers, timeout=30
                )

            # Проверка статуса ответа
            response.raise_for_status()

            # Обработка ответа
            if response.content:
                response_data = response.json()

                # Сохранение ответа в файл
                if save_to_file:
                    file_name = self.save_response_to_file(
                        endpoint, params, response_data
                    )
                    logger.info(f"Ответ сохранен в файл: {file_name}")

                return response_data
            else:
                logger.info(f"Получен пустой ответ от {endpoint}")
                return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при выполнении запроса к {endpoint}: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Статус ответа: {e.response.status_code}")
                logger.error(f"Текст ответа: {e.response.text}")
            raise

    def save_response_to_file(self, endpoint, params, response_data):
        """
        Сохранение ответа API в файл
        """
        # Создание имени файла на основе эндпоинта и параметров
        endpoint_clean = endpoint.strip("/").replace("/", "_")

        # Добавление параметров в имя файла
        param_str = ""
        if params:
            param_str = "_" + "_".join([f"{k}-{v}" for k, v in params.items()])

        # Получение текущего времени для имени файла
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Формирование полного пути к файлу
        filename = f"{endpoint_clean}{param_str}_{timestamp}.json"
        file_path = data_directory / filename

        # Сохранение данных в файл
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump(response_data, file, ensure_ascii=False, indent=2)
            logger.info(f"Ответ успешно сохранен в файл: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Ошибка при сохранении ответа в файл: {e}")
            return None

    def upload_product_data(self, ean, attributes, locale="de-DE"):
        """
        Загрузка данных о товаре

        :param ean: EAN товара
        :param attributes: Словарь с атрибутами товара
        :param locale: Локаль (язык)
        :return: Результат загрузки
        """
        data = {"ean": [ean], "attributes": attributes}

        logger.info(f"Загрузка данных товара с EAN: {ean}")

        # Формирование запроса на загрузку данных о товаре
        response = self.make_request(
            method="PUT", endpoint="/product-data", params={"locale": locale}, data=data
        )

        return response

    def get_product_data_status(self, ean, locale="de-DE"):
        """
        Получение статуса загрузки данных о товаре

        :param ean: EAN товара
        :param locale: Локаль (язык)
        :return: Статус загрузки
        """
        logger.info(f"Получение статуса загрузки товара с EAN: {ean}")

        # Формирование запроса на получение статуса загрузки данных о товаре
        response = self.make_request(
            method="GET",
            endpoint=f"/product-data/status/{ean}",
            params={"locale": locale},
        )

        return response

    def import_product_data_csv(self, csv_url, locale="de-DE"):
        """
        Загрузка данных о товарах из CSV-файла

        :param csv_url: URL к CSV-файлу с данными о товарах
        :param locale: Локаль (язык)
        :return: Результат загрузки
        """
        data = {"url": csv_url}

        logger.info(f"Загрузка CSV-файла с данными о товарах: {csv_url}")

        # Формирование запроса на загрузку CSV-файла
        response = self.make_request(
            method="POST",
            endpoint="/product-data/import-file",
            params={"locale": locale},
            data=data,
        )

        return response

    def get_import_files_status(self):
        """
        Получение статуса загрузки CSV-файлов

        :return: Статус загрузки CSV-файлов
        """
        logger.info("Получение статуса загрузки CSV-файлов")

        # Формирование запроса на получение статуса загрузки CSV-файлов
        response = self.make_request(method="GET", endpoint="/product-data/import-file")

        return response

    def get_categories(
        self, storefront="de", query=None, parent_id=None, limit=20, offset=0
    ):
        """
        Получение списка категорий

        :param storefront: Торговая площадка (страна)
        :param query: Поисковый запрос для категорий
        :param parent_id: ID родительской категории
        :param limit: Максимальное количество записей
        :param offset: Смещение для пагинации
        :return: Список категорий
        """
        params = {"storefront": storefront, "limit": limit, "offset": offset}

        if query:
            params["q"] = query

        if parent_id:
            params["id_parent"] = parent_id

        logger.info(f"Получение списка категорий для {storefront}")

        # Формирование запроса на получение списка категорий
        response = self.make_request(
            method="GET", endpoint="/categories", params=params
        )

        return response

    def get_category_attributes(self, category_id, storefront="de"):
        """
        Получение атрибутов категории

        :param category_id: ID категории
        :param storefront: Торговая площадка (страна)
        :return: Атрибуты категории
        """
        params = {
            "storefront": storefront,
            "embedded": ["optional_attributes", "required_attributes"],
        }

        logger.info(f"Получение атрибутов категории {category_id}")

        # Формирование запроса на получение атрибутов категории
        response = self.make_request(
            method="GET", endpoint=f"/categories/{category_id}", params=params
        )

        return response

    def suggest_category(self, product_data, price=None, storefront="de"):
        """
        Получение предложений категорий для товара

        :param product_data: Словарь с данными о товаре (title, description, manufacturer)
        :param price: Цена товара в центах
        :param storefront: Торговая площадка (страна)
        :return: Предложения категорий
        """
        data = {"item": product_data}

        if price:
            data["price"] = price

        logger.info(f"Получение предложений категорий для товара")

        # Формирование запроса на получение предложений категорий
        response = self.make_request(
            method="POST",
            endpoint="/categories/decide",
            params={"storefront": storefront},
            data=data,
        )

        return response


def read_product_data_from_json(file_path):
    """
    Чтение данных о товаре из JSON-файла

    :param file_path: Путь к JSON-файлу с данными о товаре
    :return: Данные о товаре в формате для API Kaufland
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            product_data = json.load(file)

        logger.info(f"Прочитан JSON-файл: {file_path}")

        # Проверяем, что файл имеет правильную структуру
        if "ean" in product_data and "attributes" in product_data:
            return product_data
        else:
            logger.error(
                "Неверный формат JSON-файла: отсутствуют обязательные поля 'ean' и/или 'attributes'"
            )
            return None
    except Exception as e:
        logger.error(f"Ошибка при чтении JSON-файла: {e}")
        return None


# Пример использования API для загрузки товаров
if __name__ == "__main__":
    # Замените на ваши ключи API
    CLIENT_KEY = "d87e10e9e4286a12e09dfa0ab5636234"
    SECRET_KEY = "eb38965918f5349c951d3a2ed18b58cb4fb45fcf0e247e272a83a95a618cc430"

    # Создание клиента API
    api = KauflandProductAPI(CLIENT_KEY, SECRET_KEY)
    product_data = read_product_data_from_json("product.json")
    if product_data:
        # Загрузка данных о товаре
        try:
            ean = product_data["ean"][0]
            attributes = product_data["attributes"]

            logger.info(f"Загрузка товара с EAN: {ean}")

            response = api.upload_product_data(ean, attributes)
            logger.info(f"Ответ API при загрузке товара: {response}")

            # Проверка статуса загрузки
            status_response = api.get_product_data_status(ean)
            logger.info(f"Статус загрузки товара: {status_response}")
        except Exception as e:
            logger.error(f"Ошибка при загрузке товара: {e}")
    else:
        logger.error("Не удалось прочитать данные о товаре из JSON-файла")

    # # Получение списка категорий
    # try:
    #     categories = api.get_categories(query="handtasche")
    #     logger.info(f"Получено категорий: {len(categories.get('data', []))}")

    #     # Вывод найденных категорий
    #     for category in categories.get("data", []):
    #         logger.info(
    #             f"Категория: {category.get('title_plural')} (ID: {category.get('id_category')})"
    #         )
    # except Exception as e:
    #     logger.error(f"Ошибка при получении категорий: {e}")

    # # Предположим, что мы нашли нужную категорию с ID 25671 (Handtasche)
    # try:
    #     category_id = 25671
    #     category_attributes = api.get_category_attributes(category_id)

    #     # Вывод обязательных атрибутов категории
    #     required_attrs = category_attributes.get("data", {}).get(
    #         "required_attributes", []
    #     )
    #     logger.info(f"Обязательные атрибуты для категории {category_id}:")
    #     for attr in required_attrs:
    #         logger.info(
    #             f"- {attr.get('title')} ({attr.get('name')}), тип: {attr.get('type')}"
    #         )

    #     # Вывод необязательных атрибутов категории
    #     optional_attrs = category_attributes.get("data", {}).get(
    #         "optional_attributes", []
    #     )
    #     logger.info(f"Необязательные атрибуты для категории {category_id}:")
    #     for attr in optional_attrs:
    #         logger.info(
    #             f"- {attr.get('title')} ({attr.get('name')}), тип: {attr.get('type')}"
    #         )
    # except Exception as e:
    #     logger.error(f"Ошибка при получении атрибутов категории: {e}")

    # # Создание примера данных о товаре
    # product_data = create_product_data_example()

    # # Загрузка данных о товаре
    # try:
    #     ean = product_data["ean"][0]
    #     attributes = product_data["attributes"]

    #     response = api.upload_product_data(ean, attributes)
    #     logger.info(f"Ответ API при загрузке товара: {response}")

    #     # Проверка статуса загрузки
    #     status_response = api.get_product_data_status(ean)
    #     logger.info(f"Статус загрузки товара: {status_response}")
    # except Exception as e:
    #     logger.error(f"Ошибка при загрузке товара: {e}")
