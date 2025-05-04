import logging
from config.logger import logger
from datetime import datetime
import json
import os
from pathlib import Path

# Создание директории для логов, если она отсутствует
log_dir = Path("logs/payments")
log_dir.mkdir(parents=True, exist_ok=True)

# Настройка логгера специально для платежей
payment_logger = logging.getLogger("payment_logger")
payment_logger.setLevel(logging.INFO)

# Обработчик для записи в файл
file_handler = logging.FileHandler(log_dir / "payment_logs.log")
file_handler.setLevel(logging.INFO)

# Форматирование логов
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Добавление обработчика к логгеру
payment_logger.addHandler(file_handler)


def log_payment_event(
    event_type: str, user_id: int, order_id: int = None, payment_data: dict = None
):
    """
    Логирует события платежной системы

    Args:
        event_type: Тип события (payment_started, pre_checkout, payment_success, payment_error)
        user_id: ID пользователя
        order_id: ID заказа (если есть)
        payment_data: Дополнительные данные о платеже
    """
    timestamp = datetime.now().isoformat()

    log_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "user_id": user_id,
        "order_id": order_id,
        "payment_data": payment_data or {},
    }

    # Логирование в стандартный лог
    logger.info(f"Payment event: {event_type} | User: {user_id} | Order: {order_id}")

    # Логирование в специальный файл для платежей
    payment_logger.info(json.dumps(log_entry))

    # Сохранение детальной информации о платеже в отдельный файл
    if payment_data:
        detailed_log_path = (
            log_dir / f"payment_{order_id}_{timestamp.replace(':', '-')}.json"
        )
        with open(detailed_log_path, "w") as f:
            json.dump(log_entry, f, indent=2)
