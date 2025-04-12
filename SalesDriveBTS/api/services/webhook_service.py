import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.logger import logger

def generate_unique_id() -> str:
    """Генерирует уникальный идентификатор для запроса"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"

def save_crm_webhook(data: Dict[str, Any]) -> str:
    """
    Сохраняет полученные данные webhook в JSON файл.
    
    Args:
        data: Словарь с данными от CRM
        
    Returns:
        str: Уникальный идентификатор запроса
    """
    # Создаем директорию, если она не существует
    os.makedirs(settings.STORAGE_CRM_REQUESTS_DIR, exist_ok=True)
    
    # Генерируем уникальный идентификатор для запроса
    request_id = generate_unique_id()
    
    # Формируем имя файла
    filename = f"crm_webhook_{request_id}.json"
    file_path = os.path.join(settings.STORAGE_CRM_REQUESTS_DIR, filename)
    
    # Сохраняем данные в файл
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Webhook сохранен в файл: {file_path}")
        return request_id
    except Exception as e:
        logger.error(f"Ошибка сохранения webhook: {e}")
        raise

async def process_webhook_data(data: Dict[str, Any], db: AsyncSession) -> Dict[str, Any]:
    """
    Обрабатывает данные webhook, готовит и отправляет запрос в BTS.
    
    Args:
        data: Словарь с данными от CRM
        db: Сессия базы данных
        
    Returns:
        Dict[str, Any]: Результат обработки
    """
    logger.info(f"Обработка данных webhook для заказа {data.get('order_id', 'unknown')}")
    
    # На этом этапе мы просто возвращаем заглушку
    # В будущем здесь будет логика обработки данных и отправки в BTS
    
    # TODO: Реализовать обработку данных и отправку в BTS
    
    return {
        "bts_order_id": None,
        "delivery_cost": None,
        "estimated_delivery_date": None,
        "tracking_number": None,
        "details": {
            "status": "pending_processing"
        }
    }

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Проверяет подпись webhook для защиты от подделки запросов.
    
    Args:
        payload: Тело запроса в виде байтов
        signature: Подпись из заголовка запроса
        
    Returns:
        bool: True если подпись верна, иначе False
    """
    # TODO: Реализовать проверку подписи
    # Это может быть HMAC с секретным ключом или другой метод
    
    # Пока просто возвращаем True
    return True