import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, text
from sqlalchemy.future import select

from core.logger import logger
from models.db_models import (
    Order, OrderItem, Contact, Branch, City, 
    SubmissionStatus, PaymentMethod
)

async def save_webhook_to_db_simple(
    data: Dict[str, Any], 
    extracted_data: Dict[str, Any], 
    db: AsyncSession
) -> Optional[int]:
    """
    Упрощенная версия функции сохранения данных webhook в базу данных.
    Использует только базовые поля, которые точно существуют в таблице.
    
    Args:
        data: Исходные данные webhook
        extracted_data: Извлеченные структурированные данные
        db: Сессия базы данных
        
    Returns:
        Optional[int]: ID созданного заказа в базе данных или None в случае ошибки
    """
    try:
        # 1. Создаем или получаем контакт
        contact_id = await get_or_create_contact(extracted_data, db)
        
        # 2. Находим или создаем метод оплаты
        payment_method_id = await get_or_create_payment_method(extracted_data, db)
        
        # 3. Находим или создаем населенный пункт
        city_branch_id = await get_or_create_city_branch(extracted_data, db)
        
        # 4. Получаем статус "pending"
        status_pending = await get_submission_status("pending", db)
        
        # Получаем order_id из данных
        order_id_from_crm = None
        if "data" in data and "id" in data["data"]:
            order_id_from_crm = str(data["data"]["id"])
        
        # Проверяем, существует ли уже заказ с таким номером
        if order_id_from_crm:
            query = text("""
            SELECT id FROM orders WHERE order_number = :order_number
            """)
            result = await db.execute(query, {"order_number": order_id_from_crm})
            existing_order = result.scalar()
            
            if existing_order:
                # Обновляем существующий заказ
                query = text("""
                UPDATE orders SET 
                    contact_id = :contact_id,
                    branch_id = :branch_id,
                    payment_method_id = :payment_method_id,
                    total_amount = :total_amount,
                    raw_data = :raw_data,
                    updated_at = :updated_at
                WHERE id = :id
                """)
                
                # Подготовка данных для обновления
                update_data = {
                    "id": existing_order,
                    "contact_id": contact_id,
                    "branch_id": city_branch_id,
                    "payment_method_id": payment_method_id,
                    "total_amount": float(extracted_data.get("Сумма", "0").replace(" ", "")) if extracted_data.get("Сумма") else 0,
                    "raw_data": json.dumps(data),
                    "updated_at": datetime.now()
                }
                
                await db.execute(query, update_data)
                
                # Удаляем и создаем заново товары
                delete_query = text("DELETE FROM order_items WHERE order_id = :order_id")
                await db.execute(delete_query, {"order_id": existing_order})
                
                # Создаем товары
                if extracted_data.get("Товары"):
                    await create_order_items_simple(existing_order, extracted_data["Товары"], db)
                
                await db.commit()
                logger.info(f"Обновлен заказ с ID {existing_order}")
                return existing_order
        
        # Создаем новый заказ
        query = text("""
        INSERT INTO orders (
            contact_id, branch_id, payment_method_id, order_number, 
            total_amount, raw_data, created_at, updated_at
        ) VALUES (
            :contact_id, :branch_id, :payment_method_id, :order_number,
            :total_amount, :raw_data, :created_at, :updated_at
        ) RETURNING id
        """)
        
        # Подготовка данных для вставки
        insert_data = {
            "contact_id": contact_id,
            "branch_id": city_branch_id,
            "payment_method_id": payment_method_id,
            "order_number": order_id_from_crm,
            "total_amount": float(extracted_data.get("Сумма", "0").replace(" ", "")) if extracted_data.get("Сумма") else 0,
            "raw_data": json.dumps(data),
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        result = await db.execute(query, insert_data)
        order_id = result.scalar()
        
        # Создаем товары
        if extracted_data.get("Товары"):
            await create_order_items_simple(order_id, extracted_data["Товары"], db)
        
        await db.commit()
        logger.info(f"Создан новый заказ с ID {order_id}")
        return order_id
        
    except Exception as e:
        await db.rollback()
        logger.exception(f"Ошибка при сохранении заказа: {e}")
        return None

async def create_order_items_simple(order_id: int, items: List[Dict[str, Any]], db: AsyncSession) -> None:
    """
    Создает товары для заказа в базе данных (упрощенная версия).
    
    Args:
        order_id: ID заказа
        items: Список товаров
        db: Сессия базы данных
    """
    for item in items:
        # Преобразуем цену из строки с пробелами в число
        price_str = item.get("Цена", "0").replace(" ", "")
        try:
            price = float(price_str)
        except ValueError:
            price = 0.0
            
        query = text("""
        INSERT INTO order_items (
            order_id, name, quantity, price, created_at, updated_at
        ) VALUES (
            :order_id, :name, :quantity, :price, :created_at, :updated_at
        )
        """)
        
        item_data = {
            "order_id": order_id,
            "name": item.get("Название", ""),
            "quantity": item.get("К-во", 1),
            "price": price,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        await db.execute(query, item_data)
    
    logger.info(f"Созданы товары для заказа с ID {order_id}")

async def get_or_create_contact(extracted_data: Dict[str, Any], db: AsyncSession) -> int:
    """
    Находит или создает запись о контакте в базе данных.
    
    Args:
        extracted_data: Извлеченные структурированные данные
        db: Сессия базы данных
        
    Returns:
        int: ID контакта
    """
    phone = extracted_data.get("Телефон", "").replace("-", "")
    
    # Проверяем, существует ли контакт
    query = text("SELECT id FROM contacts WHERE phone = :phone")
    result = await db.execute(query, {"phone": phone})
    contact = result.scalar()
    
    if contact:
        return contact
    
    # Создаем новый контакт
    query = text("""
    INSERT INTO contacts (
        last_name, first_name, phone, address, created_at, updated_at
    ) VALUES (
        :last_name, :first_name, :phone, :address, :created_at, :updated_at
    ) RETURNING id
    """)
    
    contact_data = {
        "last_name": extracted_data.get("Фамилия", ""),
        "first_name": extracted_data.get("Имя", ""),
        "phone": phone,
        "address": extracted_data.get("Адрес доставки", ""),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    result = await db.execute(query, contact_data)
    contact_id = result.scalar()
    
    logger.info(f"Создан новый контакт с ID {contact_id}")
    return contact_id

async def get_or_create_payment_method(extracted_data: Dict[str, Any], db: AsyncSession) -> int:
    """
    Находит или создает метод оплаты в базе данных.
    
    Args:
        extracted_data: Извлеченные структурированные данные
        db: Сессия базы данных
        
    Returns:
        int: ID метода оплаты
    """
    payment_method_name = extracted_data.get("Способ оплаты", "")
    
    # Определяем код метода оплаты
    payment_code = "cod" if payment_method_name == "Наложенный платеж" else "standard"
    
    # Проверяем, существует ли метод оплаты
    query = text("SELECT id FROM payment_methods WHERE code = :code")
    result = await db.execute(query, {"code": payment_code})
    payment_method = result.scalar()
    
    if payment_method:
        return payment_method
    
    # Создаем новый метод оплаты
    query = text("""
    INSERT INTO payment_methods (
        code, name, created_at, updated_at
    ) VALUES (
        :code, :name, :created_at, :updated_at
    ) RETURNING id
    """)
    
    payment_data = {
        "code": payment_code,
        "name": payment_method_name,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    result = await db.execute(query, payment_data)
    payment_method_id = result.scalar()
    
    logger.info(f"Создан новый метод оплаты с ID {payment_method_id}")
    return payment_method_id

async def get_or_create_city_branch(extracted_data: Dict[str, Any], db: AsyncSession) -> Optional[int]:
    """
    Находит или создает запись о городе/филиале в базе данных.
    
    Args:
        extracted_data: Извлеченные структурированные данные
        db: Сессия базы данных
        
    Returns:
        Optional[int]: ID филиала или None
    """
    city_name = extracted_data.get("Населенный пункт", "")
    
    # Если нет названия города, возвращаем None
    if not city_name:
        return None
    
    # Проверяем, существует ли филиал с таким external_id
    query = text("SELECT id FROM branches WHERE external_id = :external_id")
    result = await db.execute(query, {"external_id": city_name})
    branch = result.scalar()
    
    if branch:
        return branch
    
    # Парсим ID города и название, если в формате id_XXX_Name
    branch_id = None
    branch_name = city_name
    
    if city_name.startswith("id_"):
        parts = city_name.split("_", 2)
        if len(parts) >= 3:
            branch_id = parts[1]
            branch_name = parts[2].split("_BTS")[0] if "_BTS" in parts[2] else parts[2]
    
    # Создаем новый филиал
    query = text("""
    INSERT INTO branches (
        name, external_id, extracted_branch_id, extracted_branch_name, created_at, updated_at
    ) VALUES (
        :name, :external_id, :extracted_branch_id, :extracted_branch_name, :created_at, :updated_at
    ) RETURNING id
    """)
    
    branch_data = {
        "name": branch_name,
        "external_id": city_name,
        "extracted_branch_id": branch_id,
        "extracted_branch_name": branch_name,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    result = await db.execute(query, branch_data)
    branch_id = result.scalar()
    
    logger.info(f"Создан новый филиал с ID {branch_id}")
    return branch_id

async def get_submission_status(code: str, db: AsyncSession) -> int:
    """
    Получает ID статуса отправки по коду.
    
    Args:
        code: Код статуса
        db: Сессия базы данных
        
    Returns:
        int: ID статуса
    """
    # Проверяем, существует ли статус с таким кодом
    query = text("SELECT id FROM submission_statuses WHERE code = :code")
    result = await db.execute(query, {"code": code})
    status = result.scalar()
    
    if status:
        return status
    
    # Если статус не найден, создаем новый
    status_names = {
        "pending": "Ожидает отправки",
        "sent": "Отправлено",
        "error": "Ошибка",
        "received": "Получено",
        "processing": "В обработке",
        "cancelled": "Отменено"
    }
    
    query = text("""
    INSERT INTO submission_statuses (
        code, name, created_at, updated_at
    ) VALUES (
        :code, :name, :created_at, :updated_at
    ) RETURNING id
    """)
    
    status_data = {
        "code": code,
        "name": status_names.get(code, code.capitalize()),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    result = await db.execute(query, status_data)
    status_id = result.scalar()
    
    logger.info(f"Создан новый статус с ID {status_id}")
    return status_id