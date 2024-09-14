from configuration.logger_setup import logger
from fastapi import FastAPI, Request, Query, Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pathlib import Path
import json
from datetime import datetime
from database import DatabaseInitializer  # Импорт класса для работы с базой данных
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import aiomysql
from pydantic import BaseModel, Field
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
        
        # Преобразование datetime в строку
        for key, value in contact.items():
            if isinstance(value, datetime):
                contact[key] = value.strftime('%d.%m.%Y %H:%M:%S')

        response_data = {
            "contactId": contact_id,
            **contact,
            "additionalContacts": additional_contacts,
            "messengersData": messengers_data,
            "paymentDetails": payment_details,
            "comments": comments
        }
        
        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        logger.error(f"Ошибка при получении данных контакта: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# Маршрут для HEAD-запроса
@router.head("/contacts")
async def head_contacts():
    return {"message": "Contacts list"}
    
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
        # Динамическое формирование списка полей для запроса
        contact_columns = await db.get_dynamic_columns("contacts")
        columns = ", ".join(contact_columns)

        # Формирование базового SQL-запроса
        query = f"SELECT {columns} FROM contacts WHERE 1=1"
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
                    if isinstance(contact.get('created_at'), datetime):
                        contact['created_at'] = contact['created_at'].strftime('%d.%m.%Y')

        # Получаем общее количество записей
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
        },headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
            "Access-Control-Allow-Headers": "Authorization, Content-Type"
        })

    except Exception as e:
        logger.error(f"Ошибка при получении списка контактов: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/task/{task_id}")
async def get_task_by_id(task_id: int, db=Depends(get_db)):
    try:
        # Получаем данные задания по ID
        task = await db.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Получаем документы, связанные с задачей
        documents = await db.get_documents_by_task_id(task_id)

        # Проверка наличия всех полей и установка значений по умолчанию
        performers = task.get("performers", "")  # Исполнители
        if isinstance(performers, str):
            performers = performers.split(",")  # Преобразуем строку исполнителей в список

        reviewer = task.get("reviewer", None)  # Проверяющий
        initiator = task.get("initiator", None)  # Инициатор

        # Проверяем наличие временных полей, и если есть, форматируем их, иначе возвращаем None
        start_time = task.get("start_time")
        end_time = task.get("end_time")
        control_time = task.get("control_time")

        start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ') if start_time else None
        end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ') if end_time else None
        control_time_str = control_time.strftime('%Y-%m-%dT%H:%M:%SZ') if control_time else None

        response_data = {
            "id": task.get("id"),
            "title": task.get("title", "Без названия"),  # Устанавливаем значение по умолчанию, если нет названия
            "status": task.get("status", "Не указан"),  # Статус задачи
            "note": task.get("note", ""),  # Заметки
            "initiator": initiator,  # Инициатор
            "performers": performers,  # Список исполнителей
            "reviewer": reviewer,  # Проверяющий
            "startTime": start_time_str,  # Время начала
            "endTime": end_time_str,  # Время окончания
            "controlTime": control_time_str,  # Время контроля
            "documents": documents  # Связанные документы
        }

        return JSONResponse(status_code=200, content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task: {e}")
