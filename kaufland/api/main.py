import hashlib
import hmac
import json
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
        :param uri: Полный URI запроса
        :param body: Тело запроса (или пустая строка)
        :param timestamp: Unix timestamp
        :return: HMAC подпись
        """
        plain_text = "\n".join([method, uri, body, str(timestamp)])

        digest_maker = hmac.new(self.secret_key.encode(), None, hashlib.sha256)
        digest_maker.update(plain_text.encode())
        return digest_maker.hexdigest()

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
        if method.upper() in ["POST", "PATCH"] and data:
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

    # Примеры методов для работы с API

    def get_categories(self, limit=20, offset=0):
        """
        Получение списка категорий

        :param limit: Максимальное количество записей
        :param offset: Смещение для пагинации
        :return: Список категорий
        """
        params = {"limit": limit, "offset": offset}
        return self.make_request("GET", "/categories/", params=params)

    def get_product(self, product_id, embedded=None):
        """
        Получение информации о товаре

        :param product_id: ID товара
        :param embedded: Дополнительные поля (например, "category,units")
        :return: Информация о товаре
        """
        params = {}
        if embedded:
            params["embedded"] = embedded

        return self.make_request("GET", f"/products/{product_id}", params=params)

    def get_units(self, limit=None, offset=None):
        """
        Получение списка товарных единиц продавца

        :param limit: Максимальное количество записей
        :param offset: Смещение для пагинации
        :return: Список товарных единиц
        """
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        return self.make_request("GET", "/units/", params=params)

    # Дополнительные методы API
    def get_storefront_info(self):
        """
        Получение информации о доступных торговых площадках

        :return: Список доступных торговых площадок
        """
        return self.make_request("GET", "/info/storefront")

    def get_locale_info(self):
        """
        Получение информации о доступных локалях

        :return: Список доступных локалей
        """
        return self.make_request("GET", "/info/locale")

    def search_products(self, query, storefront="de", limit=20, offset=0):
        """
        Поиск товаров

        :param query: Поисковый запрос
        :param storefront: Торговая площадка (страна)
        :param limit: Максимальное количество записей
        :param offset: Смещение для пагинации
        :return: Результаты поиска
        """
        params = {
            "q": query,
            "storefront": storefront,
            "limit": limit,
            "offset": offset,
        }
        return self.make_request("GET", "/products/search", params=params)

    def get_orders(
        self, limit=20, offset=0, status=None, ts_created_from=None, ts_created_to=None
    ):
        """
        Получение списка заказов

        :param limit: Максимальное количество записей
        :param offset: Смещение для пагинации
        :param status: Фильтр по статусу заказа
        :param ts_created_from: Фильтр по дате создания (от)
        :param ts_created_to: Фильтр по дате создания (до)
        :return: Список заказов
        """
        params = {"limit": limit, "offset": offset}

        if status:
            params["status"] = status
        if ts_created_from:
            params["ts_created:from"] = ts_created_from
        if ts_created_to:
            params["ts_created:to"] = ts_created_to

        return self.make_request("GET", "/orders/", params=params)

    def get_inventory(self, limit=20, offset=0):
        """
        Получение информации о складских запасах

        :param limit: Максимальное количество записей
        :param offset: Смещение для пагинации
        :return: Информация о запасах
        """
        params = {"limit": limit, "offset": offset}
        return self.make_request("GET", "/inventory/", params=params)


# Функция для тестирования подписи на конкретном примере из документации
def test_signature_example():
    """
    Проверяет корректность создания подписи на примере из документации API
    """
    method = "POST"
    uri = "https://sellerapi.kaufland.com/v2/units/"
    body = ""
    timestamp = int(time.time())
    secret_key = "a7d0cb1da1ddbc86c96ee5fedd341b7d8ebfbb2f5c83cfe0909f4e57f05dd403"

    # Ожидаемая подпись из документации
    expected_signature = (
        "da0b65f51c0716c1d3fa658b7eaf710583630a762a98c9af8e9b392bd9df2e2a"
    )

    # Создаем объект API клиента с тестовым ключом
    test_api = KauflandAPI("test_client_key", secret_key)

    # Получаем подпись
    signature = test_api.sign_request(method, uri, body, timestamp)

    # Проверяем соответствие
    logger.info(f"Пример из документации:")
    logger.info(f"- Ожидаемая подпись: {expected_signature}")
    logger.info(f"- Полученная подпись: {signature}")
    logger.info(f"- Подписи совпадают: {signature == expected_signature}")

    return signature == expected_signature


# Пример использования
if __name__ == "__main__":
    # Замените на ваши ключи
    CLIENT_KEY = "d87e10e9e4286a12e09dfa0ab5636234"
    SECRET_KEY = "eb38965918f5349c951d3a2ed18b58cb4fb45fcf0e247e272a83a95a618cc430"

    # Сначала протестируем правильность генерации подписи
    logger.info("Проверка корректности генерации подписи...")
    signature_correct = test_signature_example()

    # if not signature_correct:
    #     logger.error("Генерация подписи работает некорректно! Проверьте алгоритм.")
    # else:
    #     logger.info("Генерация подписи работает корректно.")

    # # Создаем API клиент с реальными ключами
    # api = KauflandAPI(CLIENT_KEY, SECRET_KEY)

    # # Пример получения информации о доступных торговых площадках
    # try:
    #     logger.info("Запрос информации о торговых площадках...")
    #     storefronts = api.get_storefront_info()
    #     logger.info(f"Получена информация о торговых площадках")
    # except Exception as e:
    #     logger.error(f"Ошибка при получении информации о торговых площадках: {e}")

    # # Пример получения информации о категориях
    # try:
    #     logger.info("Запрос категорий...")
    #     categories = api.get_categories(limit=5)
    #     logger.info(f"Получено {len(categories.get('data', []))} категорий")
    # except Exception as e:
    #     logger.error(f"Ошибка при получении категорий: {e}")

    # # Пример поиска товаров
    # try:
    #     logger.info("Поиск товаров...")
    #     search_results = api.search_products("smartphone", limit=10)
    #     logger.info(f"Найдено {len(search_results.get('data', []))} товаров по запросу")
    # except Exception as e:
    #     logger.error(f"Ошибка при поиске товаров: {e}")
