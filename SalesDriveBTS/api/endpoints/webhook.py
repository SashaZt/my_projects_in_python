#api/endpoints/webhook.py
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from typing import Optional, Dict, Any
import json
import uuid
from datetime import datetime

from core.logger import logger
from core.database import get_db
from models.webhook import CRMWebhookResponse
from services.webhook_service import save_crm_webhook, process_webhook_data

router = APIRouter()

@router.post("/", response_model=CRMWebhookResponse)
async def receive_webhook(
    request: Request,
    x_crm_signature: Optional[str] = Header(None),
    db = Depends(get_db)
):
    """
    Получение вебхука от CRM системы.
    
    - **request**: Тело запроса с данными от CRM
    - **x_crm_signature**: Подпись для валидации запроса (опционально)
    """
    try:
        # Получаем тело запроса
        body_bytes = await request.body()
        
        # Преобразуем байты в словарь
        body_dict = json.loads(body_bytes)
        
        # Логируем полученный запрос
        logger.info(f"Получен webhook от CRM: {request.url.path}")
        logger.debug(f"Заголовки запроса: {request.headers}")
        
        # Сохраняем запрос
        request_id = save_crm_webhook(body_dict)
        logger.info(f"Webhook сохранен с ID: {request_id}")
        
        # Обрабатываем данные
        result = await process_webhook_data(body_dict, db)
        
        # Получаем ID заказа из тела запроса или используем значение по умолчанию
        order_id = body_dict.get("data", {}).get("id", "unknown")
        
        # Проверяем формат результата
        response_data = {
            "success": True,
            "order_id": str(order_id),
            "message": "Webhook успешно получен и обработан",
            "request_id": request_id
        }
        
        # Добавляем дополнительные данные из результата обработки
        if result and isinstance(result, dict):
            # ВАЖНО: Конвертируем bts_order_id в строку
            if "bts_order_id" in result and result["bts_order_id"] is not None:
                response_data["bts_order_id"] = str(result["bts_order_id"])
            else:
                # Если bts_order_id отсутствует, не включаем его в ответ
                pass
                
            if "tracking_number" in result and result["tracking_number"]:
                response_data["tracking_number"] = result["tracking_number"]
                
            if "delivery_cost" in result and result["delivery_cost"]:
                response_data["delivery_cost"] = result["delivery_cost"]
                
            if "estimated_delivery_date" in result and result["estimated_delivery_date"]:
                response_data["estimated_delivery_date"] = result["estimated_delivery_date"]
                
            if "details" in result and result["details"]:
                response_data["details"] = result["details"]
        
        # Логируем данные перед созданием модели для отладки
        logger.debug(f"Данные для CRMWebhookResponse: {response_data}")
        
        # Создаем модель ответа
        response = CRMWebhookResponse(**response_data)
        
        logger.info(f"Webhook обработан для заказа {order_id}")
        return response
        
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON в теле запроса")
        raise HTTPException(status_code=400, detail="Некорректный JSON")
    except Exception as e:
        logger.exception(f"Ошибка обработки webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.get("/status/{order_id}")
async def get_webhook_status(
    order_id: str,
    db = Depends(get_db)
):
    """
    Получение статуса обработки webhook для конкретного заказа.
    
    - **order_id**: ID заказа
    """
    try:
        # Здесь будет логика получения статуса заказа
        logger.info(f"Запрошен статус для заказа {order_id}")
        
        # Пока возвращаем заглушку
        return {
            "success": True,
            "order_id": order_id,
            "status": "pending",
            "message": "Статус заказа успешно получен"
        }
    except Exception as e:
        logger.exception(f"Ошибка получения статуса webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))