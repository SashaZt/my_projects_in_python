#api/services/webhook_db_service.py
from core.logger import logger
import json
from datetime import datetime
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession
import re

# Правильные импорты для обеих таблиц
from models.orders import orders, order_items  # Импортируем обе таблицы из orders.py

def format_phone(phone):
    """
    Форматирует номер телефона в формат 998-765-354.
    
    Args:
        phone: Номер телефона в виде строки или списка
        
    Returns:
        str: Отформатированный номер телефона
    """
    if isinstance(phone, list) and phone:
        phone = phone[0]  # Берем первый номер из списка
    elif not phone:
        return ""
        
    # Убираем все нецифровые символы
    phone = ''.join(filter(str.isdigit, str(phone)))
    
    # Форматируем номер, если длина подходящая
    if len(phone) >= 9:
        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
    return phone

async def save_webhook_to_db(json_data, db):
    """
    Сохраняет данные вебхука в базу данных
    
    Args:
        json_data: Исходные данные webhook
        db: Сессия базы данных
        
    Returns:
        int: ID созданного заказа
    """
    try:
        # Парсим JSON
        data = json.loads(json_data) if isinstance(json_data, str) else json_data
        logger.info(data)
        # Извлекаем данные из вебхука
        order_number = data["data"]["id"] or None
        first_name = data["data"]["contacts"][0]["fName"] or None
        last_name = data["data"]["contacts"][0]["lName"] or None
        receiver = f"{first_name} {last_name}"
        receiverPhone = format_phone(data["data"]["contacts"][0]["phone"]) if data["data"]["contacts"][0].get("phone") else None
        
        receiverDelivery = bool(data["data"]["kurer"]) if data["data"]["kurer"] is not None else None  # 1-Вызов курьера, 0-самовывоз в офис BTS.
        receiverAddress = None
        receiver_branch_id = None
        receiver_city_id = None  # Объявляем переменную заранее
        
        if receiverDelivery:
            receiverDelivery = 1
            receiverAddress = next(
                (option["text"] for option in data["meta"]["fields"]["naselennyjPunkt"]["options"]
                 if option["value"] == data["data"]["naselennyjPunkt"]), None
            )
        else:
            receiverDelivery = 0
            receiverAddress = next(
                (option["text"] for option in data["meta"]["fields"]["naselennyjPunkt"]["options"]
                 if option["value"] == data["data"]["naselennyjPunkt"]), None
            )
            # Используем функцию parse_location из этого же модуля
            branch_id_value = str(parse_location(receiverAddress))
            logger.info(f"branch_id_value: {branch_id_value}")
            logger.info(type(branch_id_value))
            # Получаем данные о филиале по ID из БД
            branch_data = await get_branch_by_id(branch_id_value, db)
            
            if branch_data:
                # Если филиал найден, используем его данные
                receiverAddress = branch_data["address"]
                # Преобразуем branche_id в целое число 
                receiver_branch_id = branch_data["id"]  
                receiver_city_id = branch_data["city_id"]  # ID города получателя

            else:
                # Если филиал не найден, используем текст из формы
                receiverAddress = next(
                    (option["text"] for option in data["meta"]["fields"]["naselennyjPunkt"]["options"]
                    if option["value"] == data["data"]["naselennyjPunkt"]), None
                )
            
        
        bringBackMoney = next(
                (option["text"] for option in data["meta"]["fields"]["payment_method"]["options"]
                 if option["value"] == data["data"]["payment_method"]), None
            )
        back_money = None
        if bringBackMoney == "Наложенный платеж":
            bringBackMoney = 1
            back_money = data["data"]["paymentAmount"] if data["data"].get("paymentAmount") is not None else None
        else:
            bringBackMoney = 0
            
        # Вычисляем суммарный вес
        total_weight = sum(product.get("mass", 0) or 0 for product in data["data"]["products"])
        weight = total_weight if total_weight > 0 else 0.5  # Если вес не указан, ставим минимальный
        
        # Создаем словарь для вставки в таблицу orders
        order_data = {
            "id_order_crm": str(order_number),
            "sender_city_id": 6,  # ID города отправителя (зафиксирован)
            "sender_address": "г.Ташкент, Яккасарайский район, массив Кушбеги , дом 17 41 кв.",  # Адрес отправителя
            "sender_real": "Гульпа Данил",  # ФИО отправителя
            "sender_phone": "+998 99 236-13-58",  # Телефон отправителя
            "sender_delivery": 0,  # Вызов курьера (1) или самовывоз (0), по умолчанию 0
            
            "weight": weight,  # Вес отправления в кг
            "package_id": 8,  # ID типа упаковки Пакет
            "post_type_id": 27,  # ID типа отправления Хозтовары
            "piece": 1,  # Количество мест
            
            "receiver": receiver,  # ФИО получателя
            "receiver_address": receiverAddress,  # Адрес получателя
            "receiver_city_id": receiver_city_id,  # ID города получателя
            "receiver_phone": receiverPhone,  # Телефон получателя
            "receiver_delivery": receiverDelivery,  # Доставка курьером (1) или самовывоз (0)
            "receiver_branch_id": receiver_branch_id,  # ID филиала получателя
            
            "bring_back_money": bringBackMoney,  # Наложенный платеж (1 - да, 0 - нет)
            "back_money": back_money,  # Сумма наложенного платежа
            
            "is_test": 0,  # Тестовый режим
            "ttn": None,  # Номер ТТН
            "shipping_amount": None,  # Стоимость доставки
            "submission_status_bts": None,  # Статус отправки в BTS
            "submission_status_crm": None,  # Статус отправки в CRM
            
            "raw_data": data,  # Исходные данные запроса
            "bts_response": None,  # Ответ от BTS
            "crm_response": None,  # Ответ от CRM
        }
        
        # Вставляем заказ в базу данных
        stmt = insert(orders).values(**order_data).returning(orders.c.id)
        result = await db.execute(stmt)
        order_id = result.scalars().first()
        
        # Добавляем товары заказа
        if "products" in data["data"] and data["data"]["products"]:
            order_items_data = []
            for product in data["data"]["products"]:
                item = {
                    "order_id": order_id,
                    "name": product.get("name", "Товар без названия"),
                    "quantity": product.get("amount", 1),
                    "price": product.get("price", 0),
                    "sku": product.get("sku", None)  # Добавляем сохранение поля sku
                }
                order_items_data.append(item)
            
            if order_items_data:
                # Логируем данные товаров перед вставкой для отладки
                logger.debug(f"Данные товаров для вставки: {order_items_data}")
                
                # Вставляем товары
                await db.execute(insert(order_items).values(order_items_data))
        
        await db.commit()
        return {
            "order_id": order_id,
            "order_data": order_data  # Данные заказа для отправки в BTS
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Ошибка при сохранении заказа в БД: {e}")
        raise

async def get_branch_by_id(branch_id, db):
    """
    Находит филиал по branche_id в базе данных
    
    Args:
        branch_id: branche_id филиала
        db: Сессия базы данных
        
    Returns:
        dict: Данные филиала с адресом
    """
    from sqlalchemy import select
    from models.branches import branches
    
    try:
        # Выполняем SQL-запрос для получения филиала по branche_id
        query = select(branches).where(branches.c.branche_id == str(branch_id))
        result = await db.execute(query)
        branch = result.fetchone()
        
        if branch:
            # Преобразуем результат в словарь и добавляем внутренний id
            return {
                "id": branch.id,  # Это primary key, который нужен для внешнего ключа
                "branche_id": branch.branche_id,
                "branche_name": branch.branche_name,
                "address": branch.address,
                "region_id": branch.region_id,
                "city_id": branch.city_id
            }
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении филиала по ID {branch_id}: {e}")
        return None

def parse_location(location_str):
    # Регулярное выражение:
    # id_(\d+) - захватывает id_ и число
    # _([^_]+) - захватывает текст после id_ до следующего _ или конца строки
    pattern = r'id_(\d+)_([^_]+)'
    match = re.match(pattern, location_str)
    
    if match:
        id_branche = match.group(1)
        return id_branche
    else:
        id_branche = None
        return id_branche