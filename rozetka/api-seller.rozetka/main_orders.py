# main_orders.py
import asyncio
import re
import time
from pathlib import Path

import requests
from logger import logger
from main_alert import init_alert_client_sync, send_alert_sync
from main_db import (
    get_next_available_key_for_orders,
    import_keys_from_files,
    save_parsed_orders_to_db,
)
from main_mail import get_send_email
from main_tg import send_message
from main_token import get_token, load_product_data, save_json_data, validyty_token

init_alert_client_sync()
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

# Загружаем конфигурацию для Telegram
config_directory = Path.cwd() / "config"
config_json_file = config_directory / "config.json"
config = load_product_data(config_json_file)
api_id = config["tg"]["api_id"]
api_hash = config["tg"]["api_hash"]
phone_number = config["tg"]["phone_number"]


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


def get_order_details(order_id):
    """
    Получает детальную информацию о заказе, включая информацию о доставке.

    Args:
        order_id (int): ID заказа

    Returns:
        dict: Детальная информация о заказе или None в случае ошибки
    """
    url = f"https://api-seller.rozetka.com.ua/orders/{order_id}"
    params = {"expand": "delivery"}  # Параметр для получения информации о доставке

    result = make_api_request("GET", url, params)

    if result and result.get("success"):
        # Сохраняем детали заказа в файл для отладки
        details_file = data_directory / f"order_details_{order_id}.json"
        save_json_data(result, details_file)

        logger.info(f"Получена детальная информация о заказе #{order_id}")
        return result["content"]

    logger.error(f"Не удалось получить детальную информацию о заказе #{order_id}")
    return None


def complete_order(order_id):
    """
    Закрывает заказ, последовательно устанавливая:
    1. Статус 26
    2. После паузы 5 секунд - статус 6 (Замовлення виконано)

    Args:
        order_id (int): ID заказа

    Returns:
        bool: True если заказ успешно закрыт, False в случае ошибки
    """
    try:
        # Получаем текущую информацию о заказе
        url_status = f"https://api-seller.rozetka.com.ua/orders/{order_id}"

        # Сначала устанавливаем статус 26
        logger.info(f"Устанавливаем статус 26 для заказа #{order_id}")
        data_step1 = {
            "status": 26,
        }

        # Выполняем первый запрос
        result_step1 = make_api_request("PUT", url_status, data=data_step1)

        if not result_step1 or not result_step1.get("success"):
            error_msg = (
                result_step1.get("errors", {}).get("message", "Неизвестная ошибка")
                if result_step1
                else "Нет ответа от API"
            )
            error_code = (
                result_step1.get("errors", {}).get("code", 0) if result_step1 else 0
            )
            logger.error(
                f"Не удалось установить статус 26 для заказа #{order_id}. Ошибка: {error_msg} (код {error_code})"
            )
            return False

        logger.info(
            f"Статус 26 успешно установлен для заказа #{order_id}. Пауза 5 секунд..."
        )
        time.sleep(5)
        data_step2 = {
            "status": 2,
        }

        # Выполняем первый запрос
        result_step2 = make_api_request("PUT", url_status, data=data_step2)

        if not result_step2 or not result_step2.get("success"):
            error_msg = (
                result_step2.get("errors", {}).get("message", "Неизвестная ошибка")
                if result_step2
                else "Нет ответа от API"
            )
            error_code = (
                result_step2.get("errors", {}).get("code", 0) if result_step2 else 0
            )
            logger.error(
                f"Не удалось установить статус 2 для заказа #{order_id}. Ошибка: {error_msg} (код {error_code})"
            )
            return False

        logger.info(
            f"Статус 2 успешно установлен для заказа #{order_id}. Пауза 5 секунд..."
        )

        # Пауза 5 секунд между запросами
        time.sleep(5)

        # Устанавливаем финальный статус 6
        logger.info(f"Устанавливаем статус 6 для заказа #{order_id}")
        data_step3 = {
            "status": 6,
        }

        # Выполняем второй запрос
        result_step3 = make_api_request("PUT", url_status, data=data_step3)

        if not result_step3 or not result_step3.get("success"):
            error_msg = (
                result_step3.get("errors", {}).get("message", "Неизвестная ошибка")
                if result_step3
                else "Нет ответа от API"
            )
            error_code = (
                result_step3.get("errors", {}).get("code", 0) if result_step3 else 0
            )
            logger.error(
                f"Не удалось установить статус 6 для заказа #{order_id}. Ошибка: {error_msg} (код {error_code})"
            )
            return False

        logger.info(f"Заказ #{order_id} успешно завершен (статус 6)")
        return True

    except Exception as e:
        logger.error(
            f"Неожиданная ошибка при изменении статуса заказа #{order_id}: {e}"
        )
        return False


def process_orders():
    """Обработка заказов и выборка нужной информации"""
    # Запускаем проверку валидности токена
    validyty_token()

    # Получаем заказы
    orders_data = get_orders()
    # orders_data = load_product_data(orders_json_file)["content"]["orders"]
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
    # logger.info(orders_data)
    for order in orders_data:
        # обработке заказа {order.get('id')}: {e}")

        try:

            item_name = order["items_photos"][0]["item_name"]
            logger.info(f"Товар: {item_name}")

            # Проверяем, что товар есть в нашем списке
            if item_name in product_names:
                order_id = order["id"]
                logger.info(f"Обработка заказа #{order_id} - {item_name}")

                # Получаем статус платежа
                payment_status_raw = get_status_payment(order_id)
                email = get_order_details(order_id)["delivery"]["email"]
                payment_status = payment_status_raw.get("status_payment_id", None)
                if payment_status == 7:
                    payment_status_title = payment_status_raw["title"]
                    user_phone = order["user_phone"]

                    # Формируем данные заказа
                    all_data = {
                        "order_id": order_id,
                        "product": item_name,
                        "user_phone": user_phone,
                        "email": email,
                        "status_payment": payment_status_title,
                        "created": order["created"],
                        "amount": order["amount"],
                        "full_name": order["user_title"].get("full_name", ""),
                    }
                    result.append(all_data)

        except Exception as e:
            logger.error(f"Ошибка при обработке заказа {order.get('id')}: {e}")

    # Сохраняем результат обработки
    result_file = data_directory / "parsed_orders.json"
    save_json_data(result, result_file)
    save_parsed_orders_to_db(result)
    logger.info(f"Обработано {len(result)} заказов")


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


def get_roblox_message_tg(product, code, mes, text_code) -> str:
    message = f"""Вітаємо 💚

Це інтернет-магазин “GAMERSQ” 🎮

Ви оформили замовлення в нашому магазині на Розетці на цей товар:

{product}

Це цифровий код, його потрібно активувати на офіційному сайті гри Roblox. 
Для активації через офіційний сайт вам потрібно пам'ятати **нікнейм та пароль** від вашого Roblox акаунту❗️

{text_code} {code}

Відео інструкція як активувати код.

https://youtu.be/6r9qPBOOzHk

1. Перейдіть на офіційний сайт гри http://roblox.com/redeem
2. Увійдіть до акаунту на якому бажаєте активувати код.
3. Уведіть код.
4. Підтвердіть активацію.
5. Обміняйте баланс на пакет Робуксів в магазині❗️

Щоб обміняти баланс на Робукси 💰
Активуйте код та натисніть на кнопку **"Get Robux"**
Або виберіть в магазині пакет який вам потрібен, та вкажіть спосіб оплати "Roblox Credit" після цього підтвердіть покупку❗️

{mes}

Код обов'язково потрібно активувати через сайт http://roblox.com/redeem  ❗️❗️❗️

Як активуєте код,напишіть нам будь ласка!

Якщо потрібна допомога з активацією то звертайтесь.

Дякуємо за придбання товару ✨
"""
    return message


def get_roblox_message_email(product, code, mes, text_code) -> str:
    message = f"""Вітаємо 💚

Це інтернет-магазин “GAMERSQ” 🎮

Ви оформили замовлення в нашому магазині на Розетці на цей товар:

{product}

Це цифровий код,його потрібно активувати на офіційному сайті Roblox. 
Для активації через офіційний сайт вам потрібно знати нікнейм та пароль від вашого Роблокс акаунту❗️

{text_code} {code}


Відео інструкція як активувати код.

https://youtu.be/6r9qPBOOzHk

1.Перейдіть на офіційний сайт гри http://roblox.com/redeem
2.Увійдіть до акаунту на якому бажаєте активувати код.
3.Уведіть код.
4.Підтвердіть активацію.
5.Обміняйте баланс на пакет Робуксів в магазині❗️

Щоб обміняти баланс на Робукси 💰
Активуйте код та натисніть на кнопку "Get Robux"
Або виберіть в магазині пакет який вам потрібен,та вкажіть спосіб оплати "Roblox Credit" після цього підтвердіть покупку❗️

{mes}

Код обов'язково потрібно активувати через сайт http://roblox.com/redeem  ❗️❗️❗️

Якщо виникнуть питання то можете написати нам в месенджери допоможемо з активацією.

Viber +380631922193
Telegram: t.me/gamersq_q
Whatsapp: wa.me/+380683845703

Дякуємо за придбання товару✨
"""
    return message


if __name__ == "__main__":
    while True:

        import_keys_from_files()
        process_orders()

        result_order = get_next_available_key_for_orders()
        for i, order in enumerate(result_order):

            if "error" in order:
                # Если есть ошибка (например, недостаточно ключей)
                message_alert = order["error"]
                send_alert_sync(message_alert)
                logger.info(f"Отправлено уведомление: {message_alert}")
                continue
            # Добавляем задержку между обработкой заказов
            if i > 0:
                logger.info("Пауза 30 секунд между заказами...")
                time.sleep(30)
            key_ids = order["key_ids"]
            order_id = order["order_id"]
            user_phone = order["user_phone"]
            # user_phone = "+380635623555"
            email = order["email"]
            # email = "a.zinchyk83@gmail.com"
            product = order["product"]
            keys_product = order["keys"]
            logger.info(f"Ключі: {keys_product}")
            logger.info(f"Ключі: {product}")  # Список ключей
            code = ", ".join(keys_product)
            text_code_product = "Ваш код:"

            if len(keys_product) > 1:
                text_code_product = "Ваші коди:"
                # Захватываем только цифры перед $
                match = re.search(r"(\d+)\$", product)

                # Общая сумма
                amount_usd = match.group(1)  # Извлекаем только число

                #  Номинал карты
                number_cards = int(int(amount_usd) / len(keys_product))

                # Количество карт
                denomination_cards = int(int(amount_usd) / number_cards)
                if denomination_cards == 2:
                    denomination_cards = "дві"
                elif denomination_cards == 3:
                    denomination_cards = "три"

                mes = f"Це {denomination_cards} картки кожна по ${number_cards} після активації карток на балансі буде ${amount_usd} ви їх потім обміняєте на робукси."

                message_tg = get_roblox_message_tg(
                    product,
                    code,
                    mes,
                    text_code_product,
                )
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    send_message(user_phone, message_tg, key_ids, order_id, code)
                )
                # Добавляем задержку перед отправкой email
                time.sleep(5)

                message_email = get_roblox_message_email(
                    product, code, mes, text_code_product
                )
                get_send_email(email, message_email)
                logger.info(f"Заказ {order_id} обработан")
                # Закрываем заказ после отправки всех уведомлений
                if complete_order(order_id):
                    logger.info(f"Заказ {order_id} обработан и завершен")
                else:
                    logger.error(
                        f"Заказ {order_id} обработан, но не удалось установить статус 'Выполнено'"
                    )

            else:
                match = re.search(r"(\d+)\$", product)
                amount_usd = match.group(1)

                mes = f"Це картка на ${amount_usd} після активації карток на балансі буде ${amount_usd} ви їх потім обміняєте на робукси."

                message_tg = get_roblox_message_tg(
                    product, code, mes, text_code_product
                )
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    send_message(user_phone, message_tg, key_ids, order_id, code)
                )
                # Добавляем задержку перед отправкой email
                time.sleep(5)

                message_email = get_roblox_message_email(
                    product, code, mes, text_code_product
                )

                get_send_email(email, message_email)
                logger.info(f"Заказ {order_id} обработан")
                # Закрываем заказ после отправки всех уведомлений
                if complete_order(order_id):
                    logger.info(f"Заказ {order_id} обработан и завершен")
                else:
                    logger.error(
                        f"Заказ {order_id} обработан, но не удалось установить статус 'Выполнено'"
                    )

        logger.info("Пауза 10 мин")
        time.sleep(600)
