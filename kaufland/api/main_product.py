import csv
import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path

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


class KauflandAPI:
    """
    Клиент для работы с Kaufland Marketplace Seller API
    """

    def __init__(
        self, client_key, secret_key, base_url="https://sellerapi.kaufland.com/v2"
    ):
        """
        Инициализация клиента API

        :param client_key: Ключ клиента (32 символа)
        :param secret_key: Секретный ключ (64 символа)
        :param base_url: Базовый URL API
        """
        self.client_key = client_key
        self.secret_key = secret_key
        self.base_url = base_url

    def sign_request(self, method, uri, body, timestamp):
        """
        Создание подписи для запроса

        :param method: HTTP метод (GET, POST, PATCH, DELETE)
        :param uri: Полный URI запроса (включая параметры запроса)
        :param body: Тело запроса (или пустая строка)
        :param timestamp: Unix timestamp
        :return: HMAC подпись
        """
        plain_text = "\n".join([method, uri, body, str(timestamp)])

        # Вывод отладочной информации
        logger.debug(f"Строка для подписи: \n{plain_text}")

        # Создание HMAC SHA-256 подписи
        digest_maker = hmac.new(self.secret_key.encode(), None, hashlib.sha256)
        digest_maker.update(plain_text.encode())
        signature = digest_maker.hexdigest()

        # Логирование для отладки
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

        # Создаем сессию для использования с параметрами запроса
        session = requests.Session()
        request = requests.Request(method.upper(), base_url, params=params)
        prepared_request = request.prepare()

        # Полный URL включая параметры запроса
        full_url = prepared_request.url

        # Время для запроса и подписи
        timestamp = int(time.time())

        # Подготовка тела запроса
        body = ""
        if data:
            body = json.dumps(data)

        # Создание подписи с полным URL включая параметры запроса
        signature = self.sign_request(method.upper(), full_url, body, timestamp)

        # Подготовка заголовков
        headers = {
            "Accept": "application/json",
            "Shop-Client-Key": self.client_key,
            "Shop-Timestamp": str(timestamp),
            "Shop-Signature": signature,
            "User-Agent": "Inhouse_development",
        }

        # Добавление Content-Type для POST/PATCH запросов
        if method.upper() in ["POST", "PATCH", "PUT"] and data:
            headers["Content-Type"] = "application/json"

        logger.debug(f"Отправка {method} запроса к {full_url}")
        logger.debug(f"Подпись создана для URL: {full_url}")

        # Выполнение запроса
        try:
            response = requests.request(
                method=method.upper(),
                url=base_url,
                params=params,
                data=body if body else None,
                headers=headers,
                timeout=30,
            )

            # Проверка статуса ответа
            response.raise_for_status()

            # Обработка ответа
            if response.content:
                response_data = response.json()

                # Сохранение ответа в файл
                if save_to_file:
                    self.save_response_to_file(endpoint, params, response_data)

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

        :param endpoint: Конечная точка API
        :param params: Параметры запроса
        :param response_data: Данные ответа
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
        except Exception as e:
            logger.error(f"Ошибка при сохранении ответа в файл: {e}")

    # Методы для работы с продуктами (товарами)

    def upload_product_data(self, product_data, ean=None):
        """
        Загрузка данных о товаре через API

        :param product_data: Данные о товаре в формате словаря
        :param ean: EAN товара (если не указан в product_data)
        :return: Ответ от API
        """
        # Если EAN передан отдельно, добавляем его в данные
        if ean and "ean" not in product_data.get("attributes", {}):
            if "attributes" not in product_data:
                product_data["attributes"] = {}
            product_data["attributes"]["ean"] = [ean]

        # Проверка наличия EAN в данных
        if "ean" not in product_data and "attributes" not in product_data:
            raise ValueError(
                "EAN товара должен быть указан в product_data или передан отдельно"
            )

        logger.info(f"Загрузка данных о товаре через API: {product_data}")

        # Выполнение PUT-запроса к API
        return self.make_request("PUT", "/product-data/", data=product_data)

    def update_product_data(self, product_data, ean=None):
        """
        Обновление данных о товаре через API (частичное обновление)

        :param product_data: Данные о товаре для обновления
        :param ean: EAN товара (если не указан в product_data)
        :return: Ответ от API
        """
        # Если EAN передан отдельно, добавляем его в данные
        if ean and "ean" not in product_data.get("attributes", {}):
            if "attributes" not in product_data:
                product_data["attributes"] = {}
            product_data["attributes"]["ean"] = [ean]

        # Проверка наличия EAN в данных
        if "ean" not in product_data and "attributes" not in product_data:
            raise ValueError(
                "EAN товара должен быть указан в product_data или передан отдельно"
            )

        logger.info(f"Обновление данных о товаре через API: {product_data}")

        # Выполнение PATCH-запроса к API
        return self.make_request("PATCH", "/product-data/", data=product_data)

    def get_product_data_status(self, ean):
        """
        Получение статуса загрузки данных о товаре

        :param ean: EAN товара
        :return: Статус загрузки
        """
        logger.info(f"Получение статуса загрузки данных о товаре с EAN: {ean}")

        # Выполнение GET-запроса к API
        return self.make_request("GET", f"/product-data/status/{ean}")

    def import_product_data_csv(self, csv_url):
        """
        Загрузка данных о товарах из CSV-файла

        :param csv_url: URL к CSV-файлу с данными о товарах
        :return: Ответ от API
        """
        data = {"url": csv_url}

        logger.info(f"Загрузка данных о товарах из CSV-файла: {csv_url}")

        # Выполнение POST-запроса к API
        return self.make_request("POST", "/product-data/import-file", data=data)

    def get_import_files_status(self):
        """
        Получение статуса загрузки CSV-файлов

        :return: Статус загрузки CSV-файлов
        """
        logger.info("Получение статуса загрузки CSV-файлов")

        # Выполнение GET-запроса к API
        return self.make_request("GET", "/product-data/import-file")

    def create_product_data_csv(self, products, output_file="products.csv"):
        """
        Создание CSV-файла с данными о товарах

        :param products: Список словарей с данными о товарах
        :param output_file: Имя выходного файла
        :return: Путь к созданному файлу
        """
        logger.info(f"Создание CSV-файла с данными о товарах: {output_file}")

        # Получение всех уникальных атрибутов из всех товаров
        all_attributes = set()
        for product in products:
            if "attributes" in product:
                all_attributes.update(product["attributes"].keys())

        # Создание заголовков CSV (EAN + все атрибуты)
        headers = ["ean"] + list(all_attributes)

        # Путь к файлу
        output_path = data_directory / output_file

        # Запись данных в CSV
        try:
            with open(output_path, "w", encoding="utf-8", newline="") as csvfile:
                writer = csv.writer(
                    csvfile, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
                )

                # Запись заголовков
                writer.writerow(headers)

                # Запись данных о товарах
                for product in products:
                    row = []

                    # Получение EAN
                    if "ean" in product:
                        row.append(
                            product["ean"][0]
                            if isinstance(product["ean"], list)
                            else product["ean"]
                        )
                    elif "attributes" in product and "ean" in product["attributes"]:
                        row.append(
                            product["attributes"]["ean"][0]
                            if isinstance(product["attributes"]["ean"], list)
                            else product["attributes"]["ean"]
                        )
                    else:
                        row.append("")

                    # Получение значений атрибутов
                    for attr in headers[1:]:  # Пропускаем первый заголовок (EAN)
                        if "attributes" in product and attr in product["attributes"]:
                            value = product["attributes"][attr]
                            if isinstance(value, list):
                                row.append(value[0] if value else "")
                            else:
                                row.append(value)
                        else:
                            row.append("")

                    writer.writerow(row)

            logger.info(f"CSV-файл успешно создан: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка при создании CSV-файла: {e}")
            raise


# Пример использования
if __name__ == "__main__":
    # Замените на ваши ключи
    CLIENT_KEY = "ваш_client_key_здесь"
    SECRET_KEY = "ваш_secret_key_здесь"

    # Создаем API клиент
    api = KauflandAPI(CLIENT_KEY, SECRET_KEY)

    # Пример данных о товаре для загрузки через API
    product_data = {
        "ean": ["4009750243800"],
        "attributes": {
            "title": ["Шоколадная плитка"],
            "description": ["Вкусная шоколадная плитка с орехами."],
            "category": ["Продукты питания"],
        },
    }

    # Пример загрузки данных о товаре через API
    try:
        response = api.upload_product_data(product_data)
        logger.info(f"Ответ от API при загрузке товара: {response}")
    except Exception as e:
        logger.error(f"Ошибка при загрузке товара: {e}")

    # Пример создания CSV-файла с данными о товарах
    products = [
        {
            "attributes": {
                "ean": ["4009750243800"],
                "title": ["Шоколадная плитка"],
                "description": ["Вкусная шоколадная плитка с орехами."],
                "category": ["Продукты питания"],
                "manufacturer": ["Шоколадная фабрика"],
            }
        },
        {
            "attributes": {
                "ean": ["4009750243801"],
                "title": ["Молочный шоколад"],
                "description": ["Нежный молочный шоколад."],
                "category": ["Продукты питания"],
                "manufacturer": ["Шоколадная фабрика"],
            }
        },
    ]

    try:
        csv_path = api.create_product_data_csv(products, "products_example.csv")
        logger.info(f"CSV-файл создан: {csv_path}")

        # Для реального импорта файла нужно загрузить его на публично доступный сервер
        # и получить URL для скачивания
        # csv_url = "https://example.com/products_example.csv"
        # response = api.import_product_data_csv(csv_url)
        # logger.info(f"Ответ от API при импорте CSV: {response}")
    except Exception as e:
        logger.error(f"Ошибка при работе с CSV: {e}")

    # Пример получения статуса загрузки CSV-файлов
    try:
        status = api.get_import_files_status()
        logger.info(f"Статус загрузки CSV-файлов: {status}")
    except Exception as e:
        logger.error(f"Ошибка при получении статуса загрузки CSV-файлов: {e}")
