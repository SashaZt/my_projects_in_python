import hashlib
import hmac
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

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
    Класс для работы с Kaufland Marketplace API.
    Переписан с PHP примера на Python.
    """

    def __init__(
        self, client_key, secret_key, base_url="https://sellerapi.kaufland.com/v2"
    ):
        self.client_key = client_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.user_agent = "Inhouse_development"

    def sign_request(self, method, uri, body, timestamp):
        """
        Создание подписи для запроса в точности так, как в PHP примере.
        """
        # Конкатенация метода, URI, тела и timestamp с \n как разделителем
        message = f"{method}\n{uri}\n{body}\n{timestamp}"
        # Подпись с использованием HMAC SHA-256
        signature = hmac.new(
            self.secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return signature

    def make_request(self, method, endpoint, params=None, data=None):
        """
        Выполнение запроса к API.
        """
        # Формирование URL
        url = f"{self.base_url}{endpoint}"

        # Добавление параметров к URL, если они есть
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"

        # Формирование тела запроса
        body = ""
        if data:
            body = json.dumps(data, ensure_ascii=False)

        # Timestamp - текущее время в секундах
        timestamp = int(time.time())

        # Создание подписи
        signature = self.sign_request(method, url, body, timestamp)

        # Формирование заголовков
        headers = {
            "Accept": "application/json",
            "Shop-Client-Key": self.client_key,
            "Shop-Timestamp": str(timestamp),
            "Shop-Signature": signature,
            "User-Agent": self.user_agent,
        }

        # Добавление Content-Type для запросов с телом
        if method.upper() in ["POST", "PUT", "PATCH"] and data:
            headers["Content-Type"] = "application/json; charset=utf-8"

        logger.info(f"Отправка {method} запроса к {url}")
        logger.info(f"Заголовки: {headers}")
        if data:
            logger.info(f"Тело запроса: {body[:100]}...")

        # Выполнение запроса
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=body.encode("utf-8") if body else None,
        )

        # Вывод информации о запросе
        logger.info(f"Статус ответа: {response.status_code}")
        logger.info(f"Заголовки ответа: {response.headers}")
        # Проверка на ошибки
        response.raise_for_status()

        # Возврат ответа в JSON, если есть содержимое
        if response.content:
            return response.json()
        return None

    # Методы для работы с товарами

    def get_product(self, product_id, embedded=None, storefront="de"):
        """
        Получение информации о товаре по ID.

        :param product_id: ID товара в Kaufland
        :param embedded: Дополнительные данные (category, units)
        :param storefront: Торговая площадка
        :return: Информация о товаре
        """
        params = {"storefront": storefront}
        if embedded:
            params["embedded"] = embedded

        return self.make_request("GET", f"/products/{product_id}", params=params)

    def upload_product_data(self, ean, attributes, locale="de-DE"):
        """
        Загрузка данных о товаре.

        :param ean: EAN товара
        :param attributes: Атрибуты товара
        :param locale: Локаль
        :return: Результат загрузки
        """
        data = {
            "ean": [ean] if not isinstance(ean, list) else ean,
            "attributes": attributes,
        }

        return self.make_request(
            "PUT", "/product-data", params={"locale": locale}, data=data
        )

    # def add_unit(self, unit_data, storefront="de"):
    #     """
    #     Добавление единицы товара (предложения).

    #     :param unit_data: Данные о единице товара
    #     :param storefront: Торговая площадка
    #     :return: Результат добавления
    #     """
    #     return self.make_request(
    #         "POST", "/units/", params={"storefront": storefront}, data=unit_data
    #     )

    def add_unit(self, unit_data, storefront="de"):
        """
        Добавление единицы товара (предложения)

        :param unit_data: Данные о единице товара
        :param storefront: Торговая площадка
        :return: Результат добавления
        """
        try:
            # Отправка запроса на добавление единицы товара
            response = self.make_request(
                method="POST",
                endpoint="/units/",
                params={"storefront": storefront},
                data=unit_data,
            )

            logger.info(f"Единица товара успешно добавлена: {response}")
            return response
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка при добавлении единицы товара: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Текст ответа: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при добавлении единицы товара: {e}")
            return None

    def delete_unit(self, unit_id, storefront="de"):
        """
        Удаление единицы товара.

        :param unit_id: ID единицы товара
        :param storefront: Торговая площадка
        :return: Результат удаления
        """
        return self.make_request(
            "DELETE", f"/units/{unit_id}/", params={"storefront": storefront}
        )

    def open_ticket(self, order_unit_ids, reason, message):
        """
        Открытие тикета на заказ.

        :param order_unit_ids: ID единиц заказа
        :param reason: Причина
        :param message: Сообщение
        :return: Результат открытия тикета
        """
        data = {
            "id_order_unit": (
                order_unit_ids if isinstance(order_unit_ids, list) else [order_unit_ids]
            ),
            "reason": reason,
            "message": message,
        }

        return self.make_request("POST", "/tickets", data=data)

    def close_ticket(self, ticket_id):
        """
        Закрытие тикета.

        :param ticket_id: ID тикета
        :return: Результат закрытия тикета
        """
        return self.make_request("PATCH", f"/tickets/{ticket_id}/close")

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

    def get_category_attributes(
        self, category_id, storefront="de", include_parent=False, include_children=False
    ):
        """
        Получение атрибутов категории.

        :param category_id: ID категории
        :param storefront: Торговая площадка (страна)
        :param include_parent: Включить родительскую категорию в ответ
        :param include_children: Включить дочерние категории в ответ
        :return: Информация о категории с атрибутами
        """
        # Формируем базовый URL
        url = f"{self.base_url}/categories/{category_id}"

        # Добавляем параметры
        url += f"?storefront={storefront}"
        url += "&embedded=optional_attributes"
        url += "&embedded=required_attributes"

        if include_parent:
            url += "&embedded=parent"

        if include_children:
            url += "&embedded=children"

        logger.info(f"Получение атрибутов для категории {category_id}: {url}")

        # Текущее время в секундах
        timestamp = int(time.time())

        # Подпись
        signature = self.sign_request("GET", url, "", timestamp)

        # Заголовки
        headers = {
            "Accept": "application/json",
            "Shop-Client-Key": self.client_key,
            "Shop-Timestamp": str(timestamp),
            "Shop-Signature": signature,
            "User-Agent": self.user_agent,
        }

        # Выполнение запроса
        response = requests.get(url, headers=headers, timeout=30)
        logger.info(f"Статус ответа: {response.status_code}")

        # Проверка на ошибки
        response.raise_for_status()

        # Возврат данных
        return response.json()


# Пример использования
if __name__ == "__main__":
    # Ваши ключи API
    CLIENT_KEY = "1db1ea9032e3cc2f128dc44d63c7e56f"
    SECRET_KEY = "52d495269912b7c1ad3220d885b013ae819305f802c58e8d708957c74ea4fbe4"

    api = KauflandAPI(CLIENT_KEY, SECRET_KEY)

    # # Пример 1: Получение товара
    # try:
    #     # Получение товара с включением категории и единиц
    #     product = api.get_product("20574181", embedded="category,units")
    #     logger.info(f"Получен товар: {product['data']['title']}")
    # except Exception as e:
    #     logger.error(f"Ошибка при получении товара: {e}")

    # # Пример 2: Загрузка данных о товаре
    # try:
    #     # Чтение данных о товаре из JSON-файла
    #     with open("product.json", "r", encoding="utf-8") as file:
    #         product_data = json.load(file)

    #     ean = product_data["ean"][0]
    #     attributes = product_data["attributes"]

    #     logger.info(f"Загрузка товара с EAN: {ean}")
    #     response = api.upload_product_data(ean, attributes)
    #     logger.info(f"Результат загрузки товара: {response}")
    # except Exception as e:
    #     logger.error(f"Ошибка при загрузке товара: {e}")

    # # Получение id категории
    # try:
    #     categories = api.get_categories(query="Campingzelte")
    #     logger.info(f"Получено категорий: {len(categories.get('data', []))}")

    #     # Вывод найденных категорий
    #     for category in categories.get("data", []):
    #         logger.info(
    #             f"Категория: {category.get('title_plural')} (ID: {category.get('id_category')})"
    #         )
    # except Exception as e:
    #     logger.error(f"Ошибка при получении категорий: {e}")

    # # Получение атрибутов категории по id категории
    # try:
    #     # Получаем атрибуты для категории Campingzelte (ID: 15261)
    #     category_id = 15261
    #     category_attrs = api.get_category_attributes(category_id)
    #     logger.info(category_attrs)
    #     # Получаем списки обязательных и опциональных атрибутов
    #     required_attrs = category_attrs.get("data", {}).get("required_attributes", [])
    #     optional_attrs = category_attrs.get("data", {}).get("optional_attributes", [])

    #     # Выводим обязательные атрибуты
    #     logger.info(f"Обязательные атрибуты для категории {category_id}:")
    #     for attr in required_attrs:
    #         logger.info(
    #             f"- {attr.get('title')} ({attr.get('name')}), тип: {attr.get('type')}"
    #         )

    #     # Выводим опциональные атрибуты
    #     logger.info(f"Опциональные атрибуты для категории {category_id}:")
    #     for attr in optional_attrs:
    #         logger.info(
    #             f"- {attr.get('title')} ({attr.get('name')}), тип: {attr.get('type')}"
    #         )
    # except Exception as e:
    #     logger.error(f"Ошибка при получении атрибутов категории: {e}")
    # Данные для добавления единицы товара
    unit_data = {
        "ean": "4061173125552",  # EAN товара (обязательно либо ean, либо id_product)
        "condition": "NEW",  # Состояние товара (NEW, USED___GOOD и т.д.)
        "listing_price": 3799,  # Цена в центах (обязательно > 0)
        "minimum_price": 3699,  # Минимальная цена для Smart Pricing (необязательно)
        "amount": 10,  # Количество товара на складе (ограничено до 99999)
        "note": "",  # Примечание (до 250 символов)
        "id_offer": "362524873",  # Получаем через products/ean/{ean} указываем ean
        "handling_time": 2,  # Количество рабочих дней на обработку заказа
        "vat_indicator": "standard_rate",  # Индикатор НДС
    }
    # unit_data = {
    #     "ean": "4061173125552",
    #     "condition": "NEW",
    #     "listing_price": 3799,
    #     "handling_time": 0,  # минимальное значение
    # }
    response = api.add_unit(unit_data, storefront="de")
