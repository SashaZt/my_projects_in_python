from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from database import DatabaseInitializer
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

router = APIRouter()

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
