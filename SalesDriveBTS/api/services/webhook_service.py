#api/services/webhook_service.py
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.webhook_db_service import save_webhook_to_db
from services.bts_service import send_order_to_bts
from services.crm_service import update_order_tracking_number
from sqlalchemy import update
from models.orders import orders
from sqlalchemy import update, func


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

async def process_webhook_data(data: Dict[str, Any], db=None) -> Dict[str, Any]:
    """
    Обрабатывает данные webhook, готовит и отправляет запрос в BTS.
    
    Args:
        data: Словарь с данными от CRM
        db: Сессия базы данных (опционально)
        
    Returns:
        Dict[str, Any]: Результат обработки
    """
    # Извлекаем ID заказа
    order_id = ""
    if "data" in data and "id" in data["data"]:
        order_id = str(data["data"]["id"])
    else:
        order_id = str(data.get("id", "unknown"))
    
    logger.info(f"Обработка данных webhook для заказа {order_id}")
    
    # Если подключение к БД включено, сохраняем в БД
    try:
        # Сохраняем данные в БД и получаем результат
        result = await save_webhook_to_db(data, db)
        
        # Распаковываем результат
        db_order_id = result.get("order_id")
        order_data = result.get("order_data")
        
        if db_order_id and order_data:
            # Отправляем данные в BTS
            bts_result = await send_order_to_bts(order_data, db_order_id, db)
            logger.info(f"Результат отправки в BTS: {bts_result}")
            
            # Если отправка в BTS успешна, обновляем данные в CRM
            if bts_result.get("success") and "response" in bts_result:
                try:
                    # Получаем данные из ответа BTS
                    bts_response = bts_result.get("response", {})
                    
                    tracking_number = bts_response.get("barcode")
                    shipping_cost = bts_response.get("cost")  # Извлекаем стоимость доставки
                    # Проверяем наличие статуса в ответе
                    status_info = None
                    if "status" in bts_response and isinstance(bts_response["status"], dict):
                        status_info = bts_response["status"].get("info")
                    
                    if tracking_number and status_info:
                        # Отправляем данные в CRM для обновления заказа
                        crm_result = await update_order_tracking_number(
                            order_id, 
                            tracking_number, 
                            status_info,
                            shipping_cost  # Передаем стоимость доставки
                        )
                        
                        logger.info(f"Результат обновления в CRM: {crm_result}")
                        
                        # Обновляем информацию о запросе в базе данных
                        if db and db_order_id:
                            await db.execute(
                                update(orders)
                                .where(orders.c.id == db_order_id)
                                .values(
                                    crm_response=crm_result,
                                    submission_status_crm="success" if crm_result.get("success") else "error",
                                    shipping_amount=shipping_cost  # Сохраняем стоимость доставки в БД
                                )
                            )
                            await db.commit()
                    else:
                        logger.warning(f"Не удалось найти номер накладной или статус в ответе BTS: {bts_response}")
                
                except Exception as e:
                    logger.error(f"Ошибка при отправке данных в CRM: {e}")
                    if db and db_order_id:
                        await db.execute(
                            update(orders)
                            .where(orders.c.id == db_order_id)
                            .values(
                                crm_response={"error": str(e)},
                                submission_status_crm="error"
                            )
                        )
                        await db.commit()
                        
            return bts_result
        else:
            bts_result = {"success": False, "error": "Не удалось получить ID заказа или данные для отправки"}
            logger.error(bts_result["error"])
            return bts_result
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return {"success": False, "error": str(e)}

# Предлагаемые изменения для services/webhook_service.py
# Требуется обновить функцию process_webhook_data для сохранения bts_order_id

async def process_webhook_data(data: Dict[str, Any], db=None) -> Dict[str, Any]:
    """
    Обрабатывает данные webhook, готовит и отправляет запрос в BTS.
    
    Args:
        data: Словарь с данными от CRM
        db: Сессия базы данных (опционально)
        
    Returns:
        Dict[str, Any]: Результат обработки
    """
    # Извлекаем ID заказа
    order_id = ""
    if "data" in data and "id" in data["data"]:
        order_id = str(data["data"]["id"])
    else:
        order_id = str(data.get("id", "unknown"))
    
    logger.info(f"Обработка данных webhook для заказа {order_id}")
    
    # Если подключение к БД включено, сохраняем в БД
    try:
        # Сохраняем данные в БД и получаем результат
        result = await save_webhook_to_db(data, db)
        
        # Распаковываем результат
        db_order_id = result.get("order_id")
        order_data = result.get("order_data")
        
        if db_order_id and order_data:
            # Отправляем данные в BTS
            bts_result = await send_order_to_bts(order_data, db_order_id, db)
            logger.info(f"Результат отправки в BTS: {bts_result}")
            
            # Если отправка в BTS успешна, обновляем данные в CRM и сохраняем bts_order_id
            if bts_result.get("success") and "response" in bts_result:
                try:
                    # Получаем данные из ответа BTS
                    bts_response = bts_result.get("response", {})
                    
                    # Сохраняем bts_order_id
                    bts_order_id = bts_response.get("orderId")
                    tracking_number = bts_response.get("barcode")
                    shipping_cost = bts_response.get("cost")  # Извлекаем стоимость доставки
                    
                    # Получаем начальный статус доставки из ответа BTS
                    delivery_status = None
                    if "status" in bts_response and isinstance(bts_response["status"], dict):
                        status_info = bts_response["status"].get("info")
                        # Извлекаем часть до скобок, если есть
                        if status_info and " (" in status_info:
                            delivery_status = status_info.split(" (")[0]
                        else:
                            delivery_status = status_info
                    
                    # Обновляем запись в БД с bts_order_id и начальным статусом
                    if bts_order_id:
                        await db.execute(
                            update(orders)
                            .where(orders.c.id == db_order_id)
                            .values(
                                bts_order_id=str(bts_order_id),
                                delivery_status=delivery_status,
                                updated_delivery_status=func.now()
                            )
                        )
                        await db.commit()
                    
                    # Проверяем наличие статуса в ответе
                    status_info = None
                    if "status" in bts_response and isinstance(bts_response["status"], dict):
                        status_info = bts_response["status"].get("info")
                    
                    if tracking_number and status_info:
                        # Отправляем данные в CRM для обновления заказа
                        crm_result = await update_order_tracking_number(
                            order_id, 
                            tracking_number, 
                            status_info,
                            shipping_cost  # Передаем стоимость доставки
                        )
                        
                        logger.info(f"Результат обновления в CRM: {crm_result}")
                        
                        # Обновляем информацию о запросе в базе данных
                        if db and db_order_id:
                            await db.execute(
                                update(orders)
                                .where(orders.c.id == db_order_id)
                                .values(
                                    crm_response=crm_result,
                                    submission_status_crm="success" if crm_result.get("success") else "error",
                                    shipping_amount=shipping_cost  # Сохраняем стоимость доставки в БД
                                )
                            )
                            await db.commit()
                    else:
                        logger.warning(f"Не удалось найти номер накладной или статус в ответе BTS: {bts_response}")
                
                except Exception as e:
                    logger.error(f"Ошибка при отправке данных в CRM: {e}")
                    if db and db_order_id:
                        await db.execute(
                            update(orders)
                            .where(orders.c.id == db_order_id)
                            .values(
                                crm_response={"error": str(e)},
                                submission_status_crm="error"
                            )
                        )
                        await db.commit()
                        
            return bts_result
        else:
            bts_result = {"success": False, "error": "Не удалось получить ID заказа или данные для отправки"}
            logger.error(bts_result["error"])
            return bts_result
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        return {"success": False, "error": str(e)}

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