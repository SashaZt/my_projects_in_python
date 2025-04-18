# api/endpoints/bts_webhook.py
from fastapi import APIRouter, Request, Depends, Header
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.logger import logger
from models.orders import orders
from sqlalchemy import update, select
from services.crm_service import update_order_tracking_number

router = APIRouter()

# @router.post("/")
# async def receive_bts_callback(
#     request: Request, 
#     x_bts_signature: Optional[str] = Header(None),
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     Получает обратный вызов от BTS системы с обновлением статуса заказа
    
#     - **request**: Тело запроса с данными от BTS
#     - **x_bts_signature**: Подпись для валидации запроса (опционально)
#     """
#     try:
#         # Получаем тело запроса
#         data = await request.json()
        
#         # Логируем полученный запрос
#         logger.info(f"Получен вебхук от BTS: {request.url.path}")
#         logger.debug(f"Данные запроса: {data}")
        
#         # Получаем идентификатор заказа из данных BTS
#         bts_order_id = data.get("orderId")
#         ttn = data.get("barcode") or data.get("ttn")
#         shipping_cost = data.get("cost")  # Извлекаем стоимость доставки
        
#         # Получаем информацию о статусе
#         status_info = None
#         if "status" in data and isinstance(data["status"], dict):
#             status_info = data["status"].get("info")
        
#         if not bts_order_id:
#             logger.error("Получен вебхук от BTS без ID заказа")
#             return {
#                 "success": False,
#                 "message": "ID заказа не найден в данных вебхука"
#             }
            
#         # Находим заказ в нашей БД по ID заказа в BTS
#         query = select(orders).where(
#             orders.c.bts_response.contains({"orderId": bts_order_id})
#         )
#         result = await db.execute(query)
#         order_row = result.fetchone()
        
#         if not order_row:
#             logger.warning(f"Заказ с BTS ID {bts_order_id} не найден в базе данных")
#             return {
#                 "success": False,
#                 "message": f"Заказ с BTS ID {bts_order_id} не найден в базе данных"
#             }
        
#         # Обновляем запись в базе данных
#         update_query = update(orders).where(
#             orders.c.bts_response.contains({"orderId": bts_order_id})
#         ).values(
#             submission_status_bts="updated",
#             bts_status=status_info,
#             ttn=ttn,
#             shipping_amount=shipping_cost,  # Сохраняем стоимость доставки
#             bts_response=data  # Обновляем сохраненные данные
#         )
        
#         await db.execute(update_query)
#         await db.commit()
        
#         # Если есть ID заказа в CRM, обновляем статус в CRM
#         if order_row.id_order_crm and ttn and status_info:
#             try:
#                 # Отправляем данные в CRM
#                 crm_result = await update_order_tracking_number(
#                     order_row.id_order_crm,
#                     ttn,
#                     status_info,
#                     shipping_cost  # Добавляем стоимость доставки
#                 )
                
#                 # Обновляем статус в БД
#                 if crm_result.get("success"):
#                     await db.execute(
#                         update(orders)
#                         .where(orders.c.id == order_row.id)
#                         .values(
#                             crm_response=crm_result,
#                             submission_status_crm="success"
#                         )
#                     )
#                     await db.commit()
                    
#                     logger.info(f"Данные успешно обновлены в CRM для заказа {order_row.id_order_crm}")
#                 else:
#                     logger.error(f"Ошибка при обновлении данных в CRM: {crm_result}")
#             except Exception as crm_error:
#                 logger.error(f"Ошибка при отправке данных в CRM: {crm_error}")
        
#         # Возвращаем успешный ответ
#         return {
#             "success": True,
#             "message": f"Статус заказа {bts_order_id} успешно обновлен",
#             "order_id": str(bts_order_id),
#             "ttn": ttn,
#             "status": status_info
#         }
#     except Exception as e:
#         logger.exception(f"Ошибка обработки вебхука от BTS: {e}")
#         return {
#             "success": False,
#             "message": f"Ошибка обработки вебхука: {str(e)}"
#         }
# Предлагаемые изменения для endpoints/bts_webhook.py
# Обновление функции receive_bts_callback для поддержки новых полей

@router.post("/")
async def receive_bts_callback(
    request: Request, 
    x_bts_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает обратный вызов от BTS системы с обновлением статуса заказа
    
    - **request**: Тело запроса с данными от BTS
    - **x_bts_signature**: Подпись для валидации запроса (опционально)
    """
    try:
        # Получаем тело запроса
        data = await request.json()
        
        # Логируем полученный запрос
        logger.info(f"Получен вебхук от BTS: {request.url.path}")
        logger.debug(f"Данные запроса: {data}")
        
        # Получаем идентификатор заказа из данных BTS
        bts_order_id = data.get("orderId")
        ttn = data.get("barcode") or data.get("ttn")
        shipping_cost = data.get("cost")  # Извлекаем стоимость доставки
        
        # Получаем информацию о статусе
        status_info = None
        delivery_status = None
        if "status" in data and isinstance(data["status"], dict):
            status_info = data["status"].get("info")
            # Извлекаем часть до скобок для delivery_status
            if status_info and " (" in status_info:
                delivery_status = status_info.split(" (")[0]
            else:
                delivery_status = status_info
        
        if not bts_order_id:
            logger.error("Получен вебхук от BTS без ID заказа")
            return {
                "success": False,
                "message": "ID заказа не найден в данных вебхука"
            }
            
        # Находим заказ в нашей БД по ID заказа в BTS
        query = select(orders).where(
            # Проверяем и в bts_response, и в отдельном поле bts_order_id
            (orders.c.bts_response.contains({"orderId": bts_order_id})) |
            (orders.c.bts_order_id == str(bts_order_id))
        )
        result = await db.execute(query)
        order_row = result.fetchone()
        
        if not order_row:
            logger.warning(f"Заказ с BTS ID {bts_order_id} не найден в базе данных")
            return {
                "success": False,
                "message": f"Заказ с BTS ID {bts_order_id} не найден в базе данных"
            }
        
        # Обновляем запись в базе данных
        update_query = update(orders).where(
            (orders.c.bts_response.contains({"orderId": bts_order_id})) |
            (orders.c.bts_order_id == str(bts_order_id))
        ).values(
            submission_status_bts="updated",
            delivery_status=delivery_status,  # Сохраняем чистый статус без временных меток
            updated_delivery_status=func.now(),  # Текущее время
            bts_order_id=str(bts_order_id),  # На случай, если еще не сохранено
            ttn=ttn,
            shipping_amount=shipping_cost,  # Сохраняем стоимость доставки
            bts_response=data  # Обновляем сохраненные данные
        )
        
        await db.execute(update_query)
        await db.commit()
        
        # Если есть ID заказа в CRM, обновляем статус в CRM
        if order_row.id_order_crm and ttn and status_info:
            try:
                # Отправляем данные в CRM
                crm_result = await update_order_tracking_number(
                    order_row.id_order_crm,
                    ttn,
                    status_info,
                    shipping_cost  # Добавляем стоимость доставки
                )
                
                # Обновляем статус в БД
                if crm_result.get("success"):
                    await db.execute(
                        update(orders)
                        .where(orders.c.id == order_row.id)
                        .values(
                            crm_response=crm_result,
                            submission_status_crm="success"
                        )
                    )
                    await db.commit()
                    
                    logger.info(f"Данные успешно обновлены в CRM для заказа {order_row.id_order_crm}")
                else:
                    logger.error(f"Ошибка при обновлении данных в CRM: {crm_result}")
            except Exception as crm_error:
                logger.error(f"Ошибка при отправке данных в CRM: {crm_error}")
        
        # Возвращаем успешный ответ
        return {
            "success": True,
            "message": f"Статус заказа {bts_order_id} успешно обновлен",
            "order_id": str(bts_order_id),
            "ttn": ttn,
            "status": status_info,
            "delivery_status": delivery_status
        }
    except Exception as e:
        logger.exception(f"Ошибка обработки вебхука от BTS: {e}")
        return {
            "success": False,
            "message": f"Ошибка обработки вебхука: {str(e)}"
        }