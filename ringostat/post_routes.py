from fastapi.responses import JSONResponse
from database import DatabaseInitializer
from configuration.logger_setup import logger
from fastapi import FastAPI, Request, Query, Depends, HTTPException, APIRouter,  UploadFile, File, Body

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

router = APIRouter()



# Путь для сохранения файлов
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)  # Создаем директорию, если её нет


async def get_db():
    db_initializer = DatabaseInitializer()
    await db_initializer.create_database()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    return db_initializer

@router.post("/ringostat")
async def ringostat_post(request: Request):
    db = await get_db()
    try:
        data = await request.json()
        logger.debug(f"Получены JSON данные: {data}")

        # Подготовка данных для записи в базу данных
        phone_number = data["additional_call_data"]["userfield"]
        contacts = await db.get_all_contact_data()

        # По умолчанию статус клиента - "Новий"
        client_status = "Новий"
        client_id = None

        # Проверяем номера телефонов в базе данных
        for contact in contacts:
            client_id_bd = contact.get("contact_id")
            phone_number_bd = contact.get("phone_number")

            if phone_number_bd == phone_number:
                client_id = client_id_bd
                client_status = "Существует"
                logger.info(f"Найден клиент с ID {client_id} и номером {phone_number}")
                break

        all_data = {
            "id_call": data["uniqueid"],
            "date_and_time": data["calldate"],
            "client_id": client_id,  # Значение client_id после проверки в базе данных
            "phone_number": phone_number,
            "company_number": data["additional_call_data"]["dst"],
            "call_type": data["additional_call_data"]["call_type"],
            "client_status": client_status,  # Обновленный статус клиента
            "interaction_status": "Договір",
            "employee": "Хтось",
            "commentary": "commentary",
            "action": data["additional_call_data"].get("action", "Нет действия"),
        }

        # Попытка записи данных в базу данных
        success = await db.insert_call_data(all_data)
        if success:
            logger.info(f"Данные успешно добавлены в БД: {all_data}")
        else:
            logger.error(f"Ошибка при добавлении данных в БД: {all_data}")
            return JSONResponse(
                status_code=500,
                content={"status": "failure", "message": "Failed to save data"},
            )

    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON данных")
        return JSONResponse(
            status_code=400,
            content={"status": "failure", "message": "Invalid JSON data"},
        )
    except Exception as e:
        logger.error(f"Не удалось сохранить данные: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "failure", "message": f"Failed to save data: {e}"},
        )

    return JSONResponse(status_code=200, content={"status": "success", "data": data})

@router.post("/contact")
async def handle_contact(request: Request):
    db = await get_db()
    try:
        data = await request.json()
        logger.debug(f"Получены JSON данные: {data}")

        contact_id = data.get("contactId")
        mode = data.get("mode")

        # Статические поля, которые всегда должны быть в таблице
        static_fields = {
            "username": "VARCHAR(255)",
            "contact_type": "VARCHAR(255)",
            "contact_status": "VARCHAR(255)",
            "manager": "VARCHAR(255)",
            "userphone": "VARCHAR(20)",
            "useremail": "VARCHAR(255)",
            "usersite": "VARCHAR(255)",
            "comment": "TEXT"
        }

        # Проверка на наличие новых полей в данных
        for key in data.keys():
            if key not in static_fields:
                # Если поле не является статическим, проверяем его наличие в БД и добавляем при необходимости
                await add_column_if_not_exists("contacts", key, "VARCHAR(255)", db)

        if mode == "new" or not contact_id:
            # Создание нового контакта
            new_contact_data = {
                "username": data["username"],
                "contact_type": data["contactType"],
                "contact_status": data["contactStatus"],
                "manager": data["manager"],
                "userphone": data["userphone"],
                "useremail": data["useremail"],
                "usersite": data["usersite"],
                "comment": data.get("comment", "")
            }

            # Добавляем динамические данные
            for key in data.keys():
                if key not in static_fields:
                    new_contact_data[key] = data[key]

            contact_id = await db.insert_contact(new_contact_data)
            logger.info(f"Создан новый контакт с ID {contact_id}")

        elif mode == "edit" and contact_id:
            # Обновление существующего контакта
            update_contact_data = {
                "id": contact_id,
                "username": data["username"],
                "contact_type": data["contactType"],
                "contact_status": data["contactStatus"],
                "manager": data["manager"],
                "userphone": data["userphone"],
                "useremail": data["useremail"],
                "usersite": data["usersite"],
                "comment": data.get("comment", "")
            }

            # Добавляем динамические данные
            for key in data.keys():
                if key not in static_fields:
                    update_contact_data[key] = data[key]

            success = await db.update_contact(update_contact_data)
            if success:
                logger.info(f"Контакт с ID {contact_id} обновлен")
            else:
                raise Exception(f"Не удалось обновить контакт с ID {contact_id}")

        # Обработка дополнительных данных
        if contact_id:
            # Добавляем/обновляем дополнительные контакты
            additional_contacts = data.get("additionalContacts", [])
            for additional_contact in additional_contacts:
                additional_contact["contact_id"] = contact_id
                await db.insert_or_update_additional_contact(additional_contact)

            # Добавляем/обновляем данные мессенджеров
            messengers_data = data.get("messengersData", [])
            for messenger in messengers_data:
                messenger["contact_id"] = contact_id
                await db.insert_or_update_messenger_data(messenger)

            # Добавляем/обновляем платежные данные
            payment_details = data.get("paymentDetails", [])
            for payment in payment_details:
                payment["contact_id"] = contact_id
                await db.insert_or_update_payment_details(payment)

        return JSONResponse(status_code=200, content={"status": "success", "contactId": contact_id})

    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON данных")
        return JSONResponse(
            status_code=400,
            content={"status": "failure", "message": "Invalid JSON data"},
        )
    except Exception as e:
        logger.error(f"Ошибка обработки данных: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "failure", "message": f"Failed to process data: {e}"},
        )
"""Добавление нового столбца в таблицу, если его еще нет"""
async def add_column_if_not_exists(table_name: str, column_name: str, data_type: str, db):

    async with db.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            # Проверка наличия столбца
            await cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'")
            result = await cursor.fetchone()
            if not result:
                # Добавляем новый столбец
                await cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}")
                # Сохраняем метаданные
                await cursor.execute("INSERT INTO table_metadata (table_name, column_name, data_type) VALUES (%s, %s, %s)", (table_name, column_name, data_type))
                logger.info(f"Добавлен новый столбец {column_name} в таблицу {table_name}")

# Модель данных для задачи
class TaskModel(BaseModel):
    title: str
    status: str
    note: str
    initiator: str
    performers: List[str]
    reviewers: List[str]
    startTime: datetime
    endTime: datetime
    controlTime: datetime
    contacts: List[int] = []
    statements: List[int] = []
    documents: List[str] = []

# Маршрут для сохранения задачи
# @router.post("/task")
# async def save_task(
#     task: TaskModel,  # Убрали Body(...)
#     files: Optional[List[UploadFile]] = File(None),
#     db=Depends(get_db)
# ):
#     try:
#         task_id = await db.save_task_data(task.dict(exclude={"documents"}))
#         await db.save_contacts(task_id, task.contacts)
#         await db.save_statements(task_id, task.statements)

#         if files:
#             for file in files:
#                 file_path = UPLOAD_DIR / file.filename
#                 with open(file_path, "wb") as f:
#                     f.write(await file.read())
#                 await db.save_document({
#                     "task_id": task_id,
#                     "file_name": file.filename,
#                     "file_path": str(file_path)
#                 })

#         return JSONResponse(status_code=200, content={"status": "success", "taskId": task_id})

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error saving task: {e}")

@router.post("/task")
async def save_task(
    request: Request,
    files: Optional[List[UploadFile]] = File(None),
    db=Depends(get_db)
):
    try:
        # Декодируем JSON тело
        task_data = await request.json()

        # Преобразуем данные задачи в модель
        task = TaskModel(**task_data)

        task_id = await db.save_task_data(task.dict(exclude={"documents"}))

        # Проверка и создание контактов, если они не существуют
        for contact_id in task.contacts:
            contact_exists = await db.contact_exists(contact_id)
            if not contact_exists:
                # Создаем новый контакт, если его нет
                await db.create_contact(contact_id)

        # Проверка и создание заявок, если они не существуют
        for statement_id in task.statements:
            statement_exists = await db.statement_exists(statement_id)
            if not statement_exists:
                # Создаем новую заявку, если её нет
                await db.create_statement(statement_id, f"Заявка {statement_id}")

        await db.save_contacts(task_id, task.contacts)
        await db.save_statements(task_id, task.statements)

        # Сохранение файлов
        if files:
            for file in files:
                file_path = UPLOAD_DIR / file.filename
                with open(file_path, "wb") as f:
                    f.write(await file.read())
                await db.save_document({
                    "task_id": task_id,
                    "file_name": file.filename,
                    "file_path": str(file_path)
                })

        return JSONResponse(status_code=200, content={"status": "success", "taskId": task_id})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving task: {e}")
