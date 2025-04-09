import datetime
import http.client
import json
from typing import Any, Dict, List, Optional, Union

from logger import logger


class HTTPError(Exception):
    """Исключение при ошибках HTTP-запросов"""

    pass


class PromProductsClient:
    """Клиент для работы с товарами API Prom.ua"""

    def __init__(self, token: str, host: str = "my.prom.ua"):
        """
        Инициализация клиента

        :param token: Токен авторизации
        :param host: Хост API (по умолчанию: my.prom.ua)
        """
        self.token = token
        self.host = host

    def make_request(
        self, method: str, url: str, body: Union[Dict, List] = None
    ) -> Dict:
        """
        Выполнение HTTP-запроса к API

        :param method: HTTP-метод (GET, POST и т.д.)
        :param url: URL-адрес
        :param body: Тело запроса (для POST)
        :return: Ответ API в формате JSON
        """
        connection = http.client.HTTPSConnection(self.host)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-type": "application/json",
        }

        if body:
            body = json.dumps(body)

        logger.debug(f"Отправка запроса: {method} {self.host}{url}")
        if body:
            logger.debug(f"Тело запроса: {body}")

        connection.request(method, url, body=body, headers=headers)
        response = connection.getresponse()

        if response.status != 200:
            try:
                error_data = response.read().decode()
                logger.error(f"Ошибка ответа: {error_data}")
            except Exception as e:
                logger.error(f"Не удалось прочитать тело ошибки: {e}")
            raise HTTPError(f"{response.status}: {response.reason}")

        response_data = response.read()
        return json.loads(response_data.decode())

    def get_products_list(
        self,
        last_modified_from: Optional[datetime.datetime] = None,
        last_modified_to: Optional[datetime.datetime] = None,
        limit: Optional[int] = None,
        last_id: Optional[int] = None,
        group_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Получение списка товаров

        :param last_modified_from: Товары, измененные после указанной даты
        :param last_modified_to: Товары, измененные до указанной даты
        :param limit: Ограничение количества товаров в ответе
        :param last_id: Ограничить выборку товаров с идентификаторами не выше указанного
        :param group_id: Идентификатор группы
        :return: Список товаров
        """
        url = "/api/v1/products/list"
        params = []

        if last_modified_from:
            params.append(
                f'last_modified_from={last_modified_from.strftime("%Y-%m-%dT%H:%M:%S")}'
            )

        if last_modified_to:
            params.append(
                f'last_modified_to={last_modified_to.strftime("%Y-%m-%dT%H:%M:%S")}'
            )

        if limit:
            params.append(f"limit={limit}")

        if last_id:
            params.append(f"last_id={last_id}")

        if group_id:
            params.append(f"group_id={group_id}")

        if params:
            url = f'{url}?{"&".join(params)}'

        return self.make_request("GET", url)

    def get_product(self, product_id: int) -> Dict[str, Any]:
        """
        Получение информации о конкретном товаре

        :param product_id: ID товара
        :return: Информация о товаре
        """
        url = f"/api/v1/products/{product_id}"
        return self.make_request("GET", url)

    def edit_products(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Редактирование списка товаров

        :param products: Список словарей с данными товаров для обновления
        :return: Результат операции

        Пример структуры словаря товара:
        {
            "id": 123456,                   # ID товара (обязательное поле)
            "presence": "available",        # Статус наличия
            "in_stock": True,               # Наличие товара
            "price": 299.99,                # Цена товара
            "status": "on_display",         # Статус отображения
            "name": "Новое название",       # Новое название товара
            "description": "Описание",      # Новое описание
            "quantity_in_stock": 10,        # Количество на складе
            "oldprice": 349.99,             # Старая цена (для отображения скидки)
            "prices": [                     # Цены для оптовых покупок
                {
                    "price": 279.99,
                    "minimum_order_quantity": 5
                }
            ],
            "discount": {                   # Информация о скидке
                "value": 50,
                "type": "amount",           # amount - сумма, percent - процент
                "date_start": "2025-04-01T00:00:00",
                "date_end": "2025-04-30T23:59:59"
            }
        }
        """
        url = "/api/v1/products/edit"
        return self.make_request("POST", url, products)


# Пример использования
if __name__ == "__main__":

    # Конфигурация
    AUTH_TOKEN = "1c0ff60edd2f7af71b56da6a104d7f67abb483a5"  # Ваш токен авторизации

    logger.info("Запуск клиента API Prom.ua для работы с товарами")

    try:
        # Инициализация клиента с правильным хостом
        client = PromProductsClient(AUTH_TOKEN)
        logger.info(f"Клиент инициализирован с хостом: {client.host}")

        # Получение списка товаров (с лимитом в 10 товаров)
        logger.info("Запрос списка товаров...")
        products = client.get_products_list(limit=50, group_id=141682480)
        logger.info(f"Получено товаров: {len(products.get('products', []))}")
        with open("output_json.json", "w", encoding="utf-8") as json_file:
            json.dump(products, json_file, ensure_ascii=False, indent=4)

        # for product in products.get("products", []):
        #     logger.info(f"ID: {product.get('id')}, Название: {product.get('name')}")

        # # Если есть хотя бы один товар, получаем подробную информацию о нем
        # if products.get("products"):
        #     product_id = products["products"][0]["id"]
        #     logger.info(f"Запрос информации о товаре с ID: {product_id}")
        #     product_details = client.get_product(product_id)
        #     logger.info(f"Подробная информация о товаре {product_id}:")
        #     logger.info(json.dumps(product_details, indent=2, ensure_ascii=False))

        #     # Пример редактирования товара (изменение цены и количества)
        #     logger.info(f"Редактирование товара с ID: {product_id}")

        #     # Получаем текущую цену
        #     current_price = product_details.get("price", 0)
        #     current_quantity = product_details.get("quantity_in_stock", 0)

        #     # Создаем данные для обновления
        #     product_update = [
        #         {
        #             "id": product_id,
        #             "price": current_price,  # Оставляем ту же цену или меняем
        #             "quantity_in_stock": current_quantity
        #             + 1,  # Увеличиваем количество на 1
        #         }
        #     ]

        #     # Не выполняем в демо-режиме, раскомментируйте строку ниже для реального обновления
        #     # update_result = client.edit_products(product_update)
        #     # logger.info(f"Результат обновления: {update_result}")
        #     logger.info("Редактирование товара пропущено в демонстрационном режиме")

        # # Создаем данные для обновления
        # product_update = [
        #     {
        #         "id": 2565350561,
        #         "price": "1060",  # Оставляем ту же цену или меняем
        #     }
        # ]

        # # Не выполняем в демо-режиме, раскомментируйте строку ниже для реального обновления
        # update_result = client.edit_products(product_update)
        # logger.info(f"Результат обновления: {update_result}")
    except HTTPError as e:
        logger.error(f"Ошибка API: {e}")
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
