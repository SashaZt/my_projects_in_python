#api/services/crm_service.py
import aiohttp
import json
from core.logger import logger
from core.config import settings

async def update_order_tracking_number(order_id, tracking_number, status_info, shipping_cost=None):
    """
    Асинхронно обновляет номер накладной заказа в SalesDrive CRM
    
    Args:
        order_id (str): ID заказа в CRM
        tracking_number (str): Номер накладной для обновления
        status_info (str): Информация о статусе доставки
        shipping_cost (str): Стоимость доставки (опционально)
        
    Returns:
        dict: Ответ от API
    """
    # URL для обновления заказа
    url = "https://uni.salesdrive.me/api/order/update/"
    
    # Заголовки запроса
    headers = {
        "Content-Type": "application/json",
        "Authorization": settings.CRM_API_KEY
    }
    
    # Данные заказа для обновления
    payload = {
        "form": settings.CRM_FORM_ID,
        "id": order_id,
        "externalId": "",
        "data": {
            "nomerNakladnoj": tracking_number,
            "statusDostavki": status_info
        }
    }
    # Добавляем стоимость доставки, если она указана
    if shipping_cost:
        try:
            # Преобразуем строку в число и убираем кавычки при наличии
            if isinstance(shipping_cost, str):
                shipping_cost = shipping_cost.replace('"', '').replace("'", "")
            
            # Преобразуем в float для CRM
            shipping_cost_float = float(shipping_cost)
            payload["data"]["summaDostavki"] = shipping_cost_float
            
            logger.info(f"Добавлена стоимость доставки: {shipping_cost_float}")
        except (ValueError, TypeError) as e:
            logger.warning(f"Не удалось преобразовать стоимость доставки '{shipping_cost}': {e}")
    # Отправка запроса
    try:
        logger.info(f"Отправка данных в CRM для заказа {order_id}: tracking_number={tracking_number}, status={status_info}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                headers=headers, 
                json=payload,
                timeout=settings.CRM_TIMEOUT or 10
            ) as response:
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    response_data = {"raw_response": response_text}
                
                if response.status == 200:
                    logger.info(f"Данные успешно отправлены в CRM: {response_data}")
                    return {
                        "success": True,
                        "response": response_data
                    }
                else:
                    error_message = f"Ошибка при обновлении заказа в CRM: {response.status} - {response_text}"
                    logger.error(error_message)
                    return {
                        "success": False,
                        "error": error_message,
                        "response": response_data
                    }
    except aiohttp.ClientError as e:
        error_message = f"Ошибка соединения с CRM API: {str(e)}"
        logger.error(error_message)
        return {
            "success": False,
            "error": error_message
        }
    except Exception as e:
        error_message = f"Непредвиденная ошибка при отправке в CRM: {str(e)}"
        logger.error(error_message)
        return {
            "success": False,
            "error": error_message
        }