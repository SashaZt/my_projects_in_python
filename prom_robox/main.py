import json
import os
import time

import pyautogui
import pyperclip
import requests
from logger import logger

LOG_FILE = "log.txt"


def is_order_processed(order_id):
    order_id_str = str(order_id)

    if not os.path.exists(LOG_FILE):
        logger.info(f"Файл лога не существует. Заказ {order_id_str} считается новым.")
        return False

    with open(LOG_FILE, "r") as log:
        processed_orders = log.readlines()
        # logger.debug(
        #     f"Проверка заказа {order_id_str}. В логе {len(processed_orders)} записей."
        # )

        for line in processed_orders:
            cleaned_line = line.strip()
            if cleaned_line == order_id_str:
                # logger.info(f"Найден обработанный заказ {order_id_str} в логе.")
                return True

    logger.info(f"Заказ {order_id_str} не найден в логе.")
    return False


def log_message(order_id):
    with open(LOG_FILE, "a") as log:
        log.write(f"{order_id}\n")


# Функція для відправки повідомлення через Viber
def send_viber_message(phone, message, order_id):
    # Створюємо посилання на Viber
    link = f"viber://chat?number={phone}"

    # Відкриваємо чат
    os.startfile(link)
    time.sleep(5)  # Чекаємо, поки відкриється Viber

    # Клікаємо в текстове поле (координати треба налаштувати під себе)
    pyautogui.click(1058, 1372)  # Заміни координати на правильні для свого екрану
    time.sleep(0.5)

    # Копіюємо повідомлення в буфер
    pyperclip.copy(message)

    # Вставляємо текст
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)

    # Відправляємо повідомлення
    pyautogui.press("enter")
    logger.info(f"Повідомлення надіслано клієнту {phone}!")

    # Логуємо повідомлення
    log_message(order_id)
    pyautogui.click(2444, 11)  # Закрытие окна
    time.sleep(0.5)


def get_orders():
    url = "https://my.prom.ua/api/v1/orders/list"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer cb8b346a636ebcbd2a90283d5d2d8dfa0c1b14ab",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        orders_data = response.json()

        with open("orders.json", "w", encoding="utf-8") as f:
            json.dump(orders_data, f, ensure_ascii=False, indent=4)
        return orders_data

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

    return {"orders": []}  # Возвращаем пустой список заказов в случае ошибки


def scrap_orders():
    # Чтение JSON файла
    orders_data = get_orders()
    result = []

    # Проходим по всем заказам
    for order in orders_data["orders"]:

        # Проверяем условия: status="pending", phone и client_first_name
        if order["status"] == "pending":

            # Проходим по продуктам в заказе
            for product in order["products"]:
                # Извлекаем нужные данные продукта
                product_data = {
                    "order_id": order["id"],
                    "client_first_name": order["client_first_name"],
                    "phone": order["phone"],
                    "product_id": product["id"],
                    "name": product["name_multilang"]["uk"],
                    "sku": product["sku"],
                    "price": product["price"],
                    "quantity": product["quantity"],
                }
                result.append(product_data)
    # Логируем результат
    if not result:
        logger.info("Нет новых заказов для обработки.")
    # else:
    #     logger.info(json.dumps(result, ensure_ascii=False, indent=4))

    return result


# Основний цикл для перевірки нових замовлень
def main():
    while True:
        try:
            orders_data = scrap_orders()  # Получаем новые заказы
            if not orders_data:  # Проверяем, что список не пустой
                logger.info("Нет новых заказов для обработки.")
            else:
                for order in orders_data:
                    order_id = order.get("order_id")
                    # Проверяем, отправляли ли сообщение этому клиенту
                    if is_order_processed(order_id):
                        logger.error(f"Заказ {order_id} уже обработан.Пропускаем.")
                        continue

                    phone = order.get("phone")
                    name_product = order.get("name")

                    # Формируем сообщение
                    message = f"""Вітаємо✨
Це інтернет-магазин “XGames_Store” 🎮
Ви оформили замовлення на Промі
{name_product}
Вірно?"""

                    # Отправляем сообщение через Viber
                    send_viber_message(phone, message, order_id)

        except Exception as e:
            logger.error(f"Помилка: {e}")

        logger.info("Чекаємо 10 хвилин перед наступною перевіркою...")
        time.sleep(600)  # Ждем 10 минут


if __name__ == "__main__":
    main()
