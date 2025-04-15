# api/endpoints/bts_webhook.py
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.logger import logger
from models.orders import orders
from sqlalchemy import update

router = APIRouter()

@router.post("/")
async def receive_bts_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Получает обратный вызов от BTS системы с обновлением статуса заказа
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
        status = data.get("status", {}).get("info")
        
        if bts_order_id:
            # Находим заказ в нашей БД по ID заказа в BTS
            query = update(orders).where(
                orders.c.bts_response.contains({"orderId": bts_order_id})
            ).values(
                submission_status_bts="updated",
                bts_status=status,
                # Другие поля, которые нужно обновить
            )
            
            result = await db.execute(query)
            await db.commit()
            
            # Возвращаем успешный ответ
            return {
                "success": True,
                "message": f"Статус заказа {bts_order_id} успешно обновлен"
            }
        else:
            logger.error("Получен вебхук от BTS без ID заказа")
            return {
                "success": False,
                "message": "ID заказа не найден в данных вебхука"
            }
            
    except Exception as e:
        logger.exception(f"Ошибка обработки вебхука от BTS: {e}")
        return {
            "success": False,
            "message": f"Ошибка обработки вебхука: {str(e)}"
        }