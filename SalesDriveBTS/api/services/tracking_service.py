# api/services/tracking_service.py
import aiohttp
import asyncio
import time
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core.logger import logger
from core.config import settings
from models.orders import orders
from services.crm_service import update_order_tracking_number

TERMINAL_STATUSES = ["Отказ", "Доставлен", "Возврат"]

async def get_order_tracking_status(bts_order_id):
    """
    Получает текущий статус заказа из BTS API
    
    Args:
        bts_order_id: ID заказа в BTS
        
    Returns:
        dict: Данные о статусе доставки
    """
    try:
        url = f"{settings.BTS_API_URL}?r=v1/order/history&id={bts_order_id}"
        headers = {
            "Authorization": f"Bearer {settings.BTS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                headers=headers,
                timeout=settings.BTS_TIMEOUT
            ) as response:
                if response.status == 200:
                    history_data = await response.json()
                    
                    # Если есть история доставки
                    if history_data and isinstance(history_data, list) and len(history_data) > 0:
                        # Берем последнюю запись из истории (самую новую)
                        latest_status = history_data[0]
                        
                        return {
                            "success": True,
                            "status": latest_status.get("location"),
                            "message": latest_status.get("message"),
                            "timestamp": latest_status.get("timestamp"),
                            "status_id": latest_status.get("status_id"),
                            "tracking_link": latest_status.get("trackingLink"),
                            "is_terminal": any(term_status in latest_status.get("location", "") 
                                              for term_status in TERMINAL_STATUSES)
                        }
                    else:
                        return {
                            "success": False,
                            "error": "История доставки пуста"
                        }
                else:
                    error_message = f"Ошибка при получении статуса: {response.status}"
                    return {
                        "success": False,
                        "error": error_message
                    }
    except Exception as e:
        error_message = f"Ошибка при запросе статуса доставки: {str(e)}"
        logger.error(error_message)
        return {
            "success": False,
            "error": error_message
        }

async def update_order_status(db: AsyncSession, order_id: int, bts_order_id: str):
    """
    Обновляет статус заказа в БД и CRM
    
    Args:
        db: Сессия базы данных
        order_id: ID заказа в БД
        bts_order_id: ID заказа в BTS
        
    Returns:
        dict: Результат обновления
    """
    try:
        # Получаем текущий статус из BTS
        status_data = await get_order_tracking_status(bts_order_id)
        
        if not status_data.get("success"):
            logger.error(f"Не удалось получить статус для заказа BTS ID {bts_order_id}: {status_data.get('error')}")
            return status_data
        
        # Получаем существующий заказ из БД
        query = select(orders).where(orders.c.id == order_id)
        result = await db.execute(query)
        order_row = result.fetchone()
        
        if not order_row:
            logger.error(f"Заказ с ID {order_id} не найден в базе данных")
            return {
                "success": False,
                "error": f"Заказ с ID {order_id} не найден в базе данных"
            }
        
        # Проверяем, изменился ли статус
        current_status = status_data.get("status")
        if current_status == order_row.delivery_status:
            logger.info(f"Статус заказа {bts_order_id} не изменился: {current_status}")
            return {
                "success": True,
                "message": "Статус не изменился",
                "status": current_status,
                "no_changes": True
            }
        
        # Обновляем запись в БД
        update_query = update(orders).where(
            orders.c.id == order_id
        ).values(
            delivery_status=current_status,
            updated_delivery_status=datetime.now(),
            bts_order_id=bts_order_id  # на случай, если не было сохранено ранее
        )
        
        await db.execute(update_query)
        await db.commit()
        
        # Отправляем обновление в CRM
        if order_row.id_order_crm and order_row.ttn:
            try:
                # Подготавливаем сообщение для CRM с датой обновления
                status_message = status_data.get("message", "")
                if status_message:
                    # Добавляем время из timestamp, если есть
                    if status_data.get("timestamp"):
                        timestamp = status_data.get("timestamp")
                        status_time = datetime.fromtimestamp(timestamp)
                        formatted_time = status_time.strftime("%d.%m.%Y %H:%M")
                    else:
                        formatted_time = datetime.now().strftime("%d.%m.%Y %H:%M")
                        
                    status_info = f"{current_status} ({formatted_time})"
                else:
                    status_info = current_status
                
                # Отправляем данные в CRM
                crm_result = await update_order_tracking_number(
                    order_row.id_order_crm,
                    order_row.ttn,
                    status_info,
                    order_row.shipping_amount
                )
                
                # Обновляем статус отправки в CRM
                if crm_result.get("success"):
                    await db.execute(
                        update(orders)
                        .where(orders.c.id == order_id)
                        .values(
                            crm_response=crm_result,
                            submission_status_crm="success"
                        )
                    )
                    await db.commit()
                    
                    logger.info(f"Статус успешно обновлен в CRM для заказа {order_row.id_order_crm}")
                else:
                    logger.error(f"Ошибка при обновлении статуса в CRM: {crm_result}")
                    
                return {
                    "success": True,
                    "message": f"Статус заказа {bts_order_id} успешно обновлен",
                    "status": current_status,
                    "crm_update": crm_result.get("success", False),
                    "is_terminal": status_data.get("is_terminal", False)
                }
            except Exception as crm_error:
                logger.error(f"Ошибка при отправке статуса в CRM: {crm_error}")
                return {
                    "success": True,
                    "message": f"Статус заказа обновлен в БД, но возникла ошибка при отправке в CRM",
                    "status": current_status,
                    "crm_error": str(crm_error),
                    "is_terminal": status_data.get("is_terminal", False)
                }
        else:
            logger.warning(f"Отсутствует ID заказа в CRM или номер ТТН для заказа {order_id}")
            return {
                "success": True,
                "message": "Статус обновлен только в БД (отсутствуют данные для CRM)",
                "status": current_status,
                "is_terminal": status_data.get("is_terminal", False)
            }
            
    except Exception as e:
        logger.exception(f"Ошибка при обновлении статуса заказа: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def process_pending_orders(db: AsyncSession):
    """
    Обрабатывает все заказы, которые находятся в процессе доставки
    и обновляет их статусы
    
    Args:
        db: Сессия базы данных
    """
    try:
        # Выбираем заказы, которые:
        # 1. Имеют bts_order_id
        # 2. Не имеют терминального статуса
        query = select(orders).where(
            orders.c.bts_response.isnot(None),
            orders.c.delivery_status.notin_(TERMINAL_STATUSES),
            (orders.c.delivery_status.is_(None)) | 
            (orders.c.delivery_status != "Отказ") & 
            (orders.c.delivery_status != "Доставлен") & 
            (orders.c.delivery_status != "Возврат")
        )
        
        result = await db.execute(query)
        pending_orders = result.fetchall()
        
        logger.info(f"Найдено {len(pending_orders)} заказов для обновления статуса")
        
        for order in pending_orders:
            # Извлекаем bts_order_id из bts_response если не задан напрямую
            bts_order_id = order.bts_order_id
            if not bts_order_id and order.bts_response:
                bts_order_id = order.bts_response.get("orderId")
            
            if bts_order_id:
                # Обновляем статус заказа
                update_result = await update_order_status(db, order.id, bts_order_id)
                
                if update_result.get("success"):
                    # Проверяем, является ли новый статус терминальным
                    if update_result.get("is_terminal", False):
                        logger.info(f"Заказ {bts_order_id} достиг терминального статуса: {update_result.get('status')}")
                    elif not update_result.get("no_changes", False):
                        logger.info(f"Обновлен статус заказа {bts_order_id}: {update_result.get('status')}")
                else:
                    logger.error(f"Ошибка обновления статуса заказа {bts_order_id}: {update_result.get('error')}")
                
                # Пауза между запросами, чтобы не перегружать API
                await asyncio.sleep(1)
    except Exception as e:
        logger.exception(f"Ошибка при обработке ожидающих заказов: {e}")

async def tracking_worker():
    """
    Рабочий процесс для отслеживания статусов заказов
    """
    from core.database import async_session
    
    logger.info("Запуск службы отслеживания статусов заказов")
    
    while True:
        try:
            async with async_session() as db:
                await process_pending_orders(db)
                
            # Пауза 5 минут между проверками
            logger.info("Ожидание 10 минут до следующей проверки статусов заказов")
            await asyncio.sleep(600)  # 10 минут
            
        except Exception as e:
            logger.exception(f"Ошибка в службе отслеживания: {e}")
            # Даже при ошибке делаем паузу перед повторной попыткой
            await asyncio.sleep(60)  # 1 минута при ошибке

def start_tracking_service():
    """
    Запускает службу отслеживания статусов заказов
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(tracking_worker())
    except KeyboardInterrupt:
        logger.info("Служба отслеживания остановлена")
    finally:
        loop.close()