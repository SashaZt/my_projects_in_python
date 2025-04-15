#/api/services/bts_service.py
async def send_order_to_bts(order_data, db_order_id, db):
    """
    Отправляет данные заказа в BTS систему согласно документации API
    
    Args:
        order_data: Данные заказа для отправки
        db_order_id: ID заказа в БД
        db: Сессия базы данных
        
    Returns:
        dict: Результат отправки
    """
    from core.config import settings
    import aiohttp
    from models.orders import orders
    from sqlalchemy import update
    from datetime import datetime, timedelta
    import json
    from core.logger import logger
    from sqlalchemy import select
    
    # URL для отправки данных в BTS
    bts_url = f"{settings.BTS_API_URL}?r=v1/order/add"
    
    # Форматируем текущую дату и дату доставки (завтра)
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Подготавливаем данные для отправки согласно документации API
    bts_data = {
        
        "senderDelivery": order_data["sender_delivery"],
        "senderCityId": order_data["sender_city_id"],
        "senderAddress": order_data["sender_address"],
        "senderReal": order_data["sender_real"],
        "senderPhone": order_data["sender_phone"],
        
        "weight": float(order_data["weight"]),
        "packageId": order_data["package_id"],
        "postTypeId": order_data["post_type_id"],
        "piece": order_data["piece"],
        
        "receiverDelivery": order_data["receiver_delivery"],
        "receiver": order_data["receiver"],
        "receiverCityId": order_data["receiver_city_id"],
        "receiverAddress": order_data["receiver_address"],
        "receiverPhone": order_data["receiver_phone"],
        
        "senderDate": today,
        "receiverDate": tomorrow,
        "volume": 0,
        "takePhoto": 0
    }
    
    # Если есть филиал получателя и доставка самовывозом
    if order_data["receiver_delivery"] == 0 and order_data.get("receiver_branch_id"):
        bts_data["receiverBranchId"] = order_data["receiver_branch_id"]
    
    # Если есть наложенный платеж
    if order_data.get("bring_back_money") == 1 and order_data.get("back_money"):
        bts_data["bringBackMoney"] = 1
        bts_data["back_money"] = float(order_data["back_money"])
    
    # Если есть товары в заказе, добавляем их как postTypes
    from models.order_items import order_items
    query = select(order_items).where(order_items.c.order_id == db_order_id)
    result = await db.execute(query)
    items = result.fetchall()
    
    if items:
        bts_data["postTypes"] = []
        for item in items:
            bts_data["postTypes"].append({
                "name": item.name,
                "code": f"ITEM{item.id}",  # Генерируем код товара
                "count": item.quantity
            })
    
    try:
        # Получаем API ключ из настроек
        headers = {
            "Authorization": f"Bearer {settings.BTS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Выполняем асинхронный запрос к BTS API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                bts_url, 
                json=bts_data, 
                headers=headers,
                timeout=settings.BTS_TIMEOUT
            ) as response:
                response_text = await response.text()
                
                try:
                    response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    response_data = {"raw_response": response_text}
                
                # Обрабатываем ответ
                # if response.status == 200 and response_data.get("success", False):
                #     logger.info(f"Заказ успешно отправлен в BTS: {response_data}")
                    
                #     # Получаем TTN из ответа (зависит от структуры ответа BTS)
                #     ttn = response_data.get("data", {}).get("ttn") or response_data.get("ttn")
                    
                #     # Обновляем запись в БД с результатами отправки
                #     await db.execute(
                #         update(orders)
                #         .where(orders.c.id == db_order_id)
                #         .values(
                #             bts_response=response_data,
                #             submission_status_bts="success",
                #             ttn=ttn,
                #             # Добавьте другие поля, которые могут прийти в ответе
                #         )
                #     )
                #     await db.commit()
                    
                #     return {
                #         "success": True,
                #         "bts_order_id": response_data.get("data", {}).get("id"),
                #         "tracking_number": ttn,
                #         "response": response_data
                #     }
                if response.status == 200 and response_data.get("orderId") is not None:
                    logger.info(f"Заказ успешно отправлен в BTS: {response_data}")
                    
                    # Получаем TTN из ответа (барков или другое поле)
                    ttn = response_data.get("barcode") or response_data.get("ttn")
                    
                    # Обновляем запись в БД с результатами отправки
                    await db.execute(
                        update(orders)
                        .where(orders.c.id == db_order_id)
                        .values(
                            bts_response=response_data,
                            submission_status_bts="success",
                            ttn=ttn,
                            # Добавьте другие поля, которые могут прийти в ответе
                        )
                    )
                    await db.commit()
                    
                    return {
                        "success": True,
                        "bts_order_id": response_data.get("orderId"),
                        "tracking_number": ttn,
                        "response": response_data
                    }
                else:
                    error_message = response_data.get("message", "Ошибка при отправке заказа в BTS")
                    logger.error(f"Ошибка при отправке заказа в BTS: {response_data}")
                    
                    # Обновляем запись в БД с информацией об ошибке
                    await db.execute(
                        update(orders)
                        .where(orders.c.id == db_order_id)
                        .values(
                            bts_response=response_data,
                            submission_status_bts="error"
                        )
                    )
                    await db.commit()
                    
                    return {
                        "success": False,
                        "error": error_message,
                        "details": response_data
                    }
                
    except aiohttp.ClientError as e:
        error_message = f"Ошибка соединения с BTS API: {str(e)}"
        logger.error(error_message)
        
        # Обновляем запись в БД с информацией об ошибке
        await db.execute(
            update(orders)
            .where(orders.c.id == db_order_id)
            .values(
                bts_response={"error": error_message},
                submission_status_bts="connection_error"
            )
        )
        await db.commit()
        
        return {
            "success": False,
            "error": error_message
        }
        
    except Exception as e:
        error_message = f"Непредвиденная ошибка при отправке в BTS: {str(e)}"
        logger.error(error_message)
        
        # Обновляем запись в БД с информацией об ошибке
        await db.execute(
            update(orders)
            .where(orders.c.id == db_order_id)
            .values(
                bts_response={"error": error_message},
                submission_status_bts="unknown_error"
            )
        )
        await db.commit()
        
        return {
            "success": False,
            "error": error_message
        }