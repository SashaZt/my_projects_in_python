import os
import time
from pathlib import Path

import requests
from core.logger import logger


def update_single_order_with_settlements():
    """
    Обновляет один заказ в SalesDrive несколько раз, используя населенные пункты из файла

    :param file_path: путь к файлу с населенными пунктами
    :param order_id: ID заказа для обновления
    """
    # Константы для API SalesDrive
    API_URL = "https://uni.salesdrive.me/api/order/update/"
    FORM_ID = "DPbNgFSa9RbYpwz3Pl8g77YkCQe0ihjr9QQ4PITJeS2_w5YW9SedrK"

    # Заголовки запроса
    headers = {"Content-Type": "application/json"}

    # Чтение населенных пунктов из файла
    try:
        # ID заказа для обновления
        order_id = "81"

        # Создаем директорию для сохранения файла, если она не существует
        output_dir = Path(os.environ.get("DATA_DIR", "./data"))
        output_dir.mkdir(parents=True, exist_ok=True)

        # Путь к файлу
        output_file = output_dir / "all_branches.txt"
        with open(output_file, "r", encoding="utf-8") as file:
            settlements = [line.strip() for line in file if line.strip()]
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        return

    logger.info(f"Найдено {len(settlements)} населенных пунктов в файле")

    # Обновление заказа для каждого населенного пункта
    for i, settlement in enumerate(settlements):
        # Полная структура данных заказа для обновления
        payload = {
            "form": FORM_ID,
            "id": order_id,
            "data": {
                "naselennyjPunkt": settlement,  # Устанавливаем значение из файла
            },
        }

        try:
            # Отправка запроса
            logger.info(
                f"Отправка запроса {i+1}/{len(settlements)} для населенного пункта: {settlement}"
            )
            response = requests.post(API_URL, json=payload, headers=headers, timeout=10)

            # Проверка ответа
            if response.status_code == 200:
                logger.info(
                    f"Заказ {order_id} успешно обновлен. Населенный пункт: {settlement}"
                )
            else:
                logger.error(
                    f"Ошибка при обновлении заказа {order_id}. Код: {response.status_code}, Ответ: {response.text}"
                )

        except Exception as e:
            logger.error(f"Ошибка при отправке запроса для заказа {order_id}: {e}")

        # Пауза 10 секунд между запросами
        if i < len(settlements) - 1:  # Не делать паузу после последнего запроса
            time.sleep(5)
    logger.info("Обновление населенных пунктов завершено.")
