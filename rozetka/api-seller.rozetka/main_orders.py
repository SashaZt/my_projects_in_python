import asyncio
import time
from pathlib import Path

import requests
from logger import logger
from main_tg import send_message
from main_token import get_token, load_product_data, save_json_data, validyty_token

current_directory = Path.cwd()
data_directory = current_directory / "data"
db_directory = current_directory / "db"
db_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)

access_token_json_file = data_directory / "access_token.json"
orders_json_file = data_directory / "orders.json"
roblox_products_json_file = data_directory / "roblox_products.json"
output_xlsx_file = data_directory / "output.xlsx"
output_csv_file = data_directory / "output.csv"
output_xml_file = data_directory / "output.xml"
config_json_file = data_directory / "config.json"


def make_api_request(method, url, params=None, data=None):
    """
    Универсальная функция для выполнения API запросов

    Args:
        method (str): HTTP метод (GET, POST и т.д.)
        url (str): URL для запроса
        params (dict, optional): Параметры запроса
        data (dict, optional): Данные для отправки в теле запроса

    Returns:
        dict or None: Результат запроса или None в случае ошибки
    """
    # Получаем токен (функция get_token() из main_token.py проверяет все возможные источники)
    token = get_token()
    if not token:
        logger.error("Токен не найден, запустите validyty_token() из main_token.py")
        return None

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        # logger.info(f"Выполнение {method} запроса к {url}")
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
            timeout=30,
        )

        # Проверяем статус HTTP
        response.raise_for_status()

        # Парсим ответ
        result = response.json()

        if not result.get("success"):
            error_msg = result.get("errors", {}).get("message", "")
            error_code = result.get("errors", {}).get("code", 0)
            logger.error(f"API вернул ошибку: {error_msg} (код {error_code})")
            return None

        return result
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP ошибка: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        return None


def get_orders():
    """Получение списка заказов"""
    url = "https://api-seller.rozetka.com.ua/orders/search"
    params = {
        # "status": "1",  # статус заказа
        # "date_from": "2023-01-01",  # дата начала
        # "date_to": "2023-12-31",  # дата окончания
        "page": 1,  # страница
        "per_page": 20,  # количество заказов на странице
    }

    result = make_api_request("GET", url, params)
    if result and result.get("success"):
        # Сохраняем полученные заказы в файл
        save_json_data(result, orders_json_file)
        return result["content"]["orders"]

    logger.error("Не удалось получить список заказов")
    return []


def get_status_payment(order_id):
    """Получение статуса платежа по ID заказа"""
    url = f"https://api-seller.rozetka.com.ua/orders/status-payment/{order_id}"

    result = make_api_request("GET", url)
    logger.info(result)

    if result and result.get("success"):
        # Проверяем, что content не None перед доступом к его атрибутам
        if result.get("content") is not None:
            status_payment_id = result["content"].get("status_payment_id")
            if status_payment_id == 7:
                # Сохраняем статус платежа в файл для отладки
                status_file = data_directory / f"status_payment_{order_id}.json"
                save_json_data(result, status_file)
                return result["content"]

    logger.error(f"Не удалось получить статус платежа для заказа {order_id}")
    return None


def process_orders():
    """Обработка заказов и выборка нужной информации"""
    # Запускаем проверку валидности токена
    validyty_token()

    # Получаем заказы
    orders_data = get_orders()
    if not orders_data:
        logger.error("Нет данных о заказах для обработки")
        return []

    # Загружаем список товаров
    products_data = load_product_data(roblox_products_json_file)
    if not products_data:
        logger.error("Не удалось загрузить данные о товарах")
        return []

    # Создаем список только имен товаров для удобства проверки
    product_names = [product["name"] for product in products_data]

    result = []
    logger.info(f"Обработка {len(orders_data)} заказов")

    for order in orders_data:
        try:
            # Извлекаем информацию о товаре (первый товар в заказе)
            if not order.get("items_photos") or len(order["items_photos"]) == 0:
                logger.warning(
                    f"Заказ {order.get('id')} не содержит информации о товарах"
                )
                continue

            item_name = order["items_photos"][0]["item_name"]
            # Отправка сообщений в ТГ
            # loop = asyncio.new_event_loop()
            # asyncio.set_event_loop(loop)
            # loop.run_until_complete(
            #     send_message(
            #         "+380635623444",
            #         "Привет, тестирую код, не обращай пожалуйста внимание!",
            #     )
            # )

            # Проверяем, что товар есть в нашем списке
            if item_name in product_names:
                order_id = order["id"]
                logger.info(f"Обработка заказа #{order_id} - {item_name}")

                # Получаем статус платежа
                payment_status = get_status_payment(order_id)
                logger.info(payment_status)
                user_phone = None
                payment_status_title = "Не оплачено"  # Значение по умолчанию

                if payment_status is not None:
                    logger.info(payment_status)
                    payment_status_title = payment_status.get("title", "Не оплачено")

                    # Если статус "Сума заблокована", сохраняем телефон
                    if payment_status_title == "Сума заблокована":
                        user_phone = order["user_phone"]
                        logger.info(
                            f"Сумма заблокирована для заказа #{order_id}, телефон: {user_phone}"
                        )
                else:
                    logger.info("Не оплачено")
                # Формируем данные заказа
                all_data = {
                    "order_id": order_id,
                    "product": item_name,
                    "user_phone": user_phone,
                    "status": order["status"],
                    "status_payment": payment_status_title,
                    "created": order["created"],
                    "amount": order["amount"],
                    "user_info": {
                        "first_name": order["user_title"].get("first_name", ""),
                        "last_name": order["user_title"].get("last_name", ""),
                        "full_name": order["user_title"].get("full_name", ""),
                    },
                }
                result.append(all_data)
            else:
                logger.info(f"Товар {item_name} не наш")
        except Exception as e:
            logger.error(f"Ошибка при обработке заказа {order.get('id')}: {e}")

    # Сохраняем результат обработки
    result_file = data_directory / "parsed_orders.json"
    save_json_data(result, result_file)
    logger.info(f"Обработано {len(result)} заказов")

    return result

    # get_auth_token()
    # token = load_product_data(access_token_json_file)
    # # Получение заказов

    # orders = get_orders(token)
    # if not orders:
    #     logger.error("Заказы не найдены или произошла ошибка")
    #     return
    # orders = load_product_data(orders_json_file)
    # # Сохранение заказов в базу данных
    # save_orders_to_db(orders)
    # logger.info(f"Обработано {len(orders)} заказов")


def get_available_payments(order_id):
    """
    Получение доступных методов оплаты для заказа

    Args:
        order_id (int): ID заказа

    Returns:
        list: Список доступных методов оплаты или None в случае ошибки
    """
    url = "https://api-seller.rozetka.com.ua/orders/available-payments"
    params = {"order_id": order_id}
    headers = {"Content-Language": "uk"}  # Можно изменить на "ru" или "en"

    result = make_api_request("GET", url, params=params, data=headers)

    if result and result.get("success"):
        payments = result.get("content", {}).get("payments", [])
        if payments:
            logger.info(f"Доступные методы оплаты для заказа #{order_id}: {payments}")
            return payments
        else:
            logger.info(f"Для заказа #{order_id} нет доступных методов оплаты")
            return []

    logger.error(f"Не удалось получить доступные методы оплаты для заказа {order_id}")
    return None


if __name__ == "__main__":
    # main()
    while True:
        process_orders()
        logger.info("Пауза")
        time.sleep(300)
    # get_available_payments("845802219")
