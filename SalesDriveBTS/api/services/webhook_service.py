#api/services/webhook_service.py
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from services.webhook_db_service import save_webhook_to_db
from services.bts_service import send_order_to_bts

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
            
        else:
            bts_result = {"success": False, "error": "Не удалось получить ID заказа или данные для отправки"}
            logger.error(bts_result["error"])
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}")
        db_order_id = None
        bts_result = {"success": False, "error": str(e)}
   
    logger.debug(f"Извлеченные данные заказа: {json.dumps(bts_result, ensure_ascii=False)}")
    # Возвращаем заглушку для дальнейшей обработки
    # return {
    #     "bts_order_id": None,
    #     "delivery_cost": None,
    #     "estimated_delivery_date": None,
    #     "tracking_number": None,
    #     "details": {
    #         "status": "pending_processing",
    #         "db_order_id": db_order_id,
    #         "extracted_data": extracted_data
    #     }
    # }
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

# def format_phone(phone):
#     """
#     Форматирует номер телефона в формат 998-765-354.
    
#     Args:
#         phone: Номер телефона в виде строки или списка
        
#     Returns:
#         str: Отформатированный номер телефона
#     """
#     if isinstance(phone, list) and phone:
#         phone = phone[0]  # Берем первый номер из списка
#     elif not phone:
#         return ""
        
#     # Убираем все нецифровые символы
#     phone = ''.join(filter(str.isdigit, str(phone)))
    
#     # Форматируем номер, если длина подходящая
#     if len(phone) >= 9:
#         return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
#     return phone

# def extract_order_data(json_data):
#     """
#     Извлекает структурированные данные из webhook-запроса.
    
#     Args:
#         json_data: Данные webhook в формате JSON или словаря
        
#     Returns:
#         dict: Структурированные данные заказа
#     """
#     # Парсим JSON, если это строка
#     data = json.loads(json_data) if isinstance(json_data, str) else json_data
    
#     # Извлекаем данные
#     try:
#         result = {
#             "Фамилия": data["data"]["contacts"][0]["lName"] if data.get("data", {}).get("contacts") else None,
#             "Имя": data["data"]["contacts"][0]["fName"] if data.get("data", {}).get("contacts") else None,
#             "Телефон": format_phone(data["data"]["contacts"][0]["phone"]) if data.get("data", {}).get("contacts") and data["data"]["contacts"][0].get("phone") else None,
#             "Товары": [
#                 {
#                     "Название": product["name"] or None,
#                     "К-во": product["amount"],
#                     "Цена": f"{product['price']:,.2f}".replace(",", " ") if product["price"] is not None else None
#                 }
#                 for product in data["data"]["products"]
#             ] if data.get("data", {}).get("products") else [],
#             "Способ оплаты": next(
#                 (option["text"] for option in data["meta"]["fields"]["payment_method"]["options"]
#                 if option["value"] == data["data"]["payment_method"]), None
#             ) if data.get("meta", {}).get("fields", {}).get("payment_method") and data.get("data", {}).get("payment_method") else None,
#             "Населенный пункт": next(
#                 (option["text"] for option in data["meta"]["fields"]["naselennyjPunkt"]["options"]
#                 if option["value"] == data["data"]["naselennyjPunkt"]), None
#             ) if data.get("meta", {}).get("fields", {}).get("naselennyjPunkt") and data.get("data", {}).get("naselennyjPunkt") else None,
#             "Сумма": f"{data['data']['paymentAmount']:,.0f}".replace(",", " ") if data.get("data", {}).get("paymentAmount") is not None else None,
#             "Курьер": bool(data["data"]["kurer"]) if data.get("data", {}).get("kurer") is not None else None,
#             "Комментарий для доставки": data["data"]["kommentarijDlaDostavki"] if data.get("data", {}).get("kommentarijDlaDostavki") else None,
#             "Адрес доставки": data["data"]["shipping_address"] if data.get("data", {}).get("shipping_address") else None
#         }
        
#         return result
#     except Exception as e:
#         logger.error(f"Ошибка при извлечении данных заказа: {e}")
#         return {"error": str(e)}

# async def process_webhook_data(data: Dict[str, Any], db=None) -> Dict[str, Any]:
#     """
#     Обрабатывает данные webhook, готовит и отправляет запрос в BTS.
    
#     Args:
#         data: Словарь с данными от CRM
#         db: Сессия базы данных (опционально)
        
#     Returns:
#         Dict[str, Any]: Результат обработки
#     """
#     # Извлекаем ID заказа
#     order_id = ""
#     if "data" in data and "id" in data["data"]:
#         order_id = str(data["data"]["id"])
#     else:
#         order_id = str(data.get("id", "unknown"))
    
#     logger.info(f"Обработка данных webhook для заказа {order_id}")
    
#     # Извлекаем структурированные данные заказа
#     extracted_data = extract_order_data(data)
#     logger.debug(f"Извлеченные данные заказа: {json.dumps(extracted_data, ensure_ascii=False)}")
    
#     # Если подключение к БД включено и библиотеки успешно импортированы, сохраняем в БД
#     try:
#         db_order_id = await save_webhook_to_db(data, extracted_data, db)
#         logger.info(f"Данные webhook сохранены в БД с ID: {db_order_id}")
#     except Exception as e:
#         logger.error(f"Ошибка при сохранении webhook в БД: {e}")
    
#     # Возвращаем заглушку для дальнейшей обработки
#     return {
#         "bts_order_id": None,
#         "delivery_cost": None,
#         "estimated_delivery_date": None,
#         "tracking_number": None,
#         "details": {
#             "status": "pending_processing",
#             "db_order_id": db_order_id,
#             "extracted_data": extracted_data
#         }
#     }
