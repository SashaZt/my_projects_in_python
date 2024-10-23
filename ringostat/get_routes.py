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
                contact[key] = value.strftime("%d.%m.%Y %H:%M:%S")

        response_data = {
            "contactId": contact_id,
            **contact,
            "additionalContacts": additional_contacts,
            "messengersData": messengers_data,
            "paymentDetails": payment_details,
            "comments": comments,
        }

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        logger.error(f"Ошибка при получении данных контакта: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



@router.get("/contacts")
async def get_filtered_contacts(
    mini: bool = Query(False, description="Возвращать только id и organization"),
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
    db=Depends(get_db),
):
    try:
        # Если параметр mini=True, выбираем только id и organization
        if mini:
            columns = "id, organization"
        else:
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

                # Если mini=False, преобразуем даты в читаемый формат
                if not mini:
                    for contact in contacts:
                        if isinstance(contact.get("created_at"), datetime):
                            contact["created_at"] = contact["created_at"].strftime(
                                "%d.%m.%Y"
                            )

        # Получаем общее количество записей
        async with db.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT COUNT(*) FROM contacts WHERE 1=1")
                total_records = await cursor.fetchone()
                total_pages = (total_records["COUNT(*)"] // limit) + 1

        # Формирование итогового ответа
        return JSONResponse(
            status_code=200,
            content={"data": contacts, "totalPages": total_pages, "currentPage": page},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, DELETE",
                "Access-Control-Allow-Headers": "Authorization, Content-Type",
            },
        )

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
            performers = performers.split(
                ","
            )  # Преобразуем строку исполнителей в список

        reviewer = task.get("reviewer", None)  # Проверяющий
        initiator = task.get("initiator", None)  # Инициатор

        # Проверяем наличие временных полей, и если есть, форматируем их, иначе возвращаем None
        start_time = task.get("start_time")
        end_time = task.get("end_time")
        control_time = task.get("control_time")

        start_time_str = (
            start_time.strftime("%Y-%m-%dT%H:%M:%SZ") if start_time else None
        )
        end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%SZ") if end_time else None
        control_time_str = (
            control_time.strftime("%Y-%m-%dT%H:%M:%SZ") if control_time else None
        )

        response_data = {
            "id": task.get("id"),
            "title": task.get(
                "title", "Без названия"
            ),  # Устанавливаем значение по умолчанию, если нет названия
            "status": task.get("status", "Не указан"),  # Статус задачи
            "note": task.get("note", ""),  # Заметки
            "initiator": initiator,  # Инициатор
            "performers": performers,  # Список исполнителей
            "reviewer": reviewer,  # Проверяющий
            "startTime": start_time_str,  # Время начала
            "endTime": end_time_str,  # Время окончания
            "controlTime": control_time_str,  # Время контроля
            "documents": documents,  # Связанные документы
        }

        return JSONResponse(status_code=200, content=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching task: {e}")


# Добавление в `get_routes.py`


@router.get("/getconfig")
async def get_config(db=Depends(get_db)):
    """Получает конфигурационные данные для формы 'Задачи'."""
    try:
        # Получаем конфигурационные данные из базы данных
        config_data = await db.get_config()

        if not config_data:
            raise HTTPException(
                status_code=404, detail="Конфигурационные данные не найдены"
            )

        # Список полей, которые нужно преобразовать в список пользователей
        user_list_fields = ["Reviewers", "Initiators", "Performers", "Admin"]

        # Создаем новый словарь для хранения обработанных данных
        processed_data = {}

        for key, value in config_data.items():
            if key in user_list_fields:
                # Проверяем, что значение не пустое
                if value:
                    users_list = []
                    # Разбиваем строку по запятым
                    entries = [entry.strip() for entry in value.split(",")]
                    for entry in entries:
                        # Разбиваем каждую запись по двоеточию
                        email_name = entry.strip().split(":")
                        if len(email_name) == 2:
                            email = email_name[0].strip()
                            name = email_name[1].strip()
                        else:
                            # Если имя отсутствует, используем email в качестве имени
                            email = email_name[0].strip()
                            name = email
                        users_list.append({"name": name, "email": email})
                    processed_data[key] = users_list
                else:
                    processed_data[key] = []
            else:
                # Оставляем значение без изменений
                processed_data[key] = value

        return JSONResponse(
            status_code=200, content={"status": "success", "data": processed_data}
        )

    except Exception as e:
        logger.error(f"Ошибка при получении конфигурационных данных: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка при получении конфигурационных данных"
        )


@router.get("/getTaskConfigSettings")
async def get_task_config_settings(db=Depends(get_db)):
    try:
        # Получение конфигурационных данных из базы данных
        config_data = ConfigModel(
            Reviewers=[
                SimpleContactModel(name="Назар Скварок", email="office@labfox.space"),
                SimpleContactModel(name="Михаил Иванченко", email="miha125@gmail.com"),
            ],
            Admin=[
                SimpleContactModel(
                    name="office@labfox.space-", email="office@labfox.space-"
                )
            ],
            Initiators=[
                SimpleContactModel(name="Назар Скварок", email="office@labfox.space"),
                SimpleContactModel(name="Михаил Иванченко", email="miha125@gmail.com"),
            ],
            Performers=[
                SimpleContactModel(name="Назар Скварок", email="office@labfox.space"),
                SimpleContactModel(name="Михаил Иванченко", email="miha125@gmail.com"),
            ],
        )

        # Преобразование данных для JSON-сериализации
        config_data = jsonable_encoder(config_data)

        return JSONResponse(
            status_code=200, content=config_data
        )  # Возврат настроек в виде JSON-ответа

    except Exception as e:
        # Логирование ошибки и возврат HTTP-исключения
        logger.error(f"Ошибка при получении настроек задач: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
