from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from configuration.logger_setup import logger
from fastapi import FastAPI, Request, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from loguru import logger
from pathlib import Path
import json
from datetime import datetime
from database import DatabaseInitializer  # Импорт класса для работы с базой данных
from contextlib import asynccontextmanager
from configuration.logger_setup import logger  # Настройка логирования
from typing import List, Optional, Dict, Any
import aiomysql
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from fastapi import Query
import dependencies  # Импортируем модуль для доступа к db_initializer


router = APIRouter()


async def get_db():
    db_initializer = DatabaseInitializer()
    await db_initializer.create_database()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    return db_initializer

@router.get("/calls")
async def get_calls(request: Request):
    db = await get_db()
    query = "SELECT * FROM calls WHERE 1=1"
    parameters = []

    # Получаем список всех возможных параметров (колонок) из запроса
    requested_params = dict(request.query_params)

    try:
        async with db.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:

                # Получаем список всех колонок в таблице calls
                await cursor.execute("SHOW COLUMNS FROM calls")
                columns = await cursor.fetchall()
                column_names = [column["Field"] for column in columns]

                # Формируем SQL-запрос на основе переданных параметров, если они совпадают с колонками
                for param, value in requested_params.items():
                    if param in column_names:
                        query += f" AND {param} = %s"
                        parameters.append(value)

                # Выполняем запрос
                await cursor.execute(query, parameters)
                calls = await cursor.fetchall()

                # Преобразование данных в формат, который может быть сериализован в JSON
                calls_serializable = jsonable_encoder(calls)

                return JSONResponse(
                    status_code=200,
                    content={"status": "success", "data": calls_serializable},
                )
    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса: {e}")
        return JSONResponse(
            status_code=500, content={"status": "failure", "message": str(e)}
        )

# РАБОЧИЙ КОД БЫЛ
# @router.get("/contacts")
# async def get_all_contacts(
#     name: Optional[str] = None,
#     surname: Optional[str] = None,
#     formal_title: Optional[str] = None,
#     phone_number: Optional[str] = None,
#     email: Optional[str] = None,
# ):
#     db = await get_db()
#     try:
#         logger.info("Начало получения данных с фильтрацией по параметрам.")

#         # Собираем все переданные параметры в словарь
#         filters = {
#             "name": name,
#             "surname": surname,
#             "formal_title": formal_title,
#             "phone_number": phone_number,
#             "email": email,
#         }
#         # Убираем параметры, значение которых None
#         filters = {k: v for k, v in filters.items() if v is not None}

#         # Вызов функции с фильтрами
#         result = await db.get_all_contact_data(filters=filters)

#         if not result:
#             logger.warning("Данные из таблиц contacts_ не найдены.")
#             raise HTTPException(status_code=404, detail="No contact data found")

#         logger.info(f"Данные успешно получены из всех таблиц contacts_: {result}")
#         return {"status": "success", "data": result}

#     except Exception as e:
#         logger.error(f"Ошибка при получении данных из всех таблиц contacts_: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Failed to retrieve contact data: {e}"
#         )
@router.get("/contact/{contact_id}")
async def get_contact(contact_id: int, db=Depends(get_db)):
    try:
        contact = await db.get_contact_by_id(contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        additional_contacts = await db.get_additional_contacts(contact_id)
        messengers_data = await db.get_messengers_data(contact_id)
        payment_details = await db.get_payment_details(contact_id)
        comments = await db.get_comments(contact_id)
        
        # Формируем ответ в формате заказчика
        response_data = {
            "contactId": contact_id,
            "username": contact["username"],
            "contactType": contact["contact_type"],
            "contactStatus": contact["contact_status"],
            "manager": contact["manager"],
            "userphone": contact["userphone"],
            "useremail": contact["useremail"],
            "usersite": contact["usersite"],
            "comment": contact["comment"],
            "additionalContacts": additional_contacts,
            "messengersData": messengers_data,
            "paymentDetails": payment_details,
            "comments": comments
        }
        
        return response_data

    except Exception as e:
        logger.error(f"Ошибка при получении данных контакта: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/contacts")
async def get_filtered_contacts(
    searchString: Optional[str] = None,
    statusFilter: Optional[str] = None,
    contactFilter: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    activeRecords: Optional[str] = None,
    limit: int = 10,
    page: int = 1,
    sortBy: Optional[str] = None,
    sortOrder: Optional[str] = "asc",
    db=Depends(get_db)
):
    try:
        # Формирование базового SQL-запроса
        query = "SELECT id, created_at AS date, contact_type AS organization, contact_status AS status, manager AS contact, userphone AS phone FROM contacts WHERE 1=1"
        parameters = []

        # Добавление условий фильтрации
        if searchString:
            query += " AND (username LIKE %s OR userphone LIKE %s OR useremail LIKE %s)"
            search_pattern = f"%{searchString}%"
            parameters.extend([search_pattern, search_pattern, search_pattern])

        if statusFilter:
            query += " AND contact_status = %s"
            parameters.append(statusFilter)

        if contactFilter:
            query += " AND contact_type = %s"
            parameters.append(contactFilter)

        if start and end:
            query += " AND created_at BETWEEN %s AND %s"
            parameters.extend([start, end])

        if activeRecords:
            query += " AND active = %s"
            parameters.append(activeRecords)

        # Добавление условий сортировки
        if sortBy:
            query += f" ORDER BY {sortBy} {sortOrder}"

        # Добавление условий пагинации
        offset = (page - 1) * limit
        query += " LIMIT %s OFFSET %s"
        parameters.extend([limit, offset])

        async with db.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, parameters)
                contacts = await cursor.fetchall()

                # Преобразование datetime в строку
                for contact in contacts:
                    if isinstance(contact.get('date'), datetime):
                        contact['date'] = contact['date'].strftime('%d.%m.%Y')

        # Расчет общего количества страниц (предполагается, что общее количество записей уже известно)
        async with db.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT COUNT(*) FROM contacts WHERE 1=1")
                total_records = await cursor.fetchone()
                total_pages = (total_records['COUNT(*)'] // limit) + 1

        # Формирование итогового ответа
        return JSONResponse(status_code=200, content={
            "data": contacts,
            "totalPages": total_pages,
            "currentPage": page
        })

    except Exception as e:
        logger.error(f"Ошибка при получении списка контактов: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

