from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
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
import dependencies  # Импортируем модуль для доступа к db_initializer
from database import DatabaseInitializer


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


@router.get("/contacts")
async def get_all_contacts(
    name: Optional[str] = None,
    surname: Optional[str] = None,
    formal_title: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
):
    db = await get_db()
    try:
        logger.info("Начало получения данных с фильтрацией по параметрам.")

        # Собираем все переданные параметры в словарь
        filters = {
            "name": name,
            "surname": surname,
            "formal_title": formal_title,
            "phone_number": phone_number,
            "email": email,
        }
        # Убираем параметры, значение которых None
        filters = {k: v for k, v in filters.items() if v is not None}

        # Вызов функции с фильтрами
        result = await db.get_all_contact_data(filters=filters)

        if not result:
            logger.warning("Данные из таблиц contacts_ не найдены.")
            raise HTTPException(status_code=404, detail="No contact data found")

        logger.info(f"Данные успешно получены из всех таблиц contacts_: {result}")
        return {"status": "success", "data": result}

    except Exception as e:
        logger.error(f"Ошибка при получении данных из всех таблиц contacts_: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve contact data: {e}"
        )