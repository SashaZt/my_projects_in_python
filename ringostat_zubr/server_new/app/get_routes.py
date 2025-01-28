import base64
import os
from datetime import datetime
from typing import Optional

from configuration.logger_setup import logger  # Импортируем loguru логгер
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from dependencies import get_db
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

# Создание экземпляра маршрутизатора
router = APIRouter()

# Загрузка ключей из .env
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)

@router.get("/get_all_data")
async def get_all_data(db=Depends(get_db)):
    try:
        # Простой запрос без фильтрации
        query = "SELECT * FROM calls_zubr"

        logger.info("Executing SQL query to fetch all records")
        async with db.pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(query)
                records = await cursor.fetchall()
                logger.info(f"Fetched {len(records)} records from database")

        # Преобразование datetime в строку
        for record in records:
            for key, value in record.items():
                if isinstance(value, datetime):
                    record[key] = value.strftime("%Y-%m-%d %H:%M:%S")

        logger.info("Returning all records to client")
        return JSONResponse(
            status_code=200, content={"status": "success", "data": records}
        )

    except Exception as e:
        logger.error(f"An error occurred while processing the request: {e}")
        return JSONResponse(
            status_code=500, content={"status": "failure", "message": str(e)}
        )
