import base64
import os
from datetime import datetime
from typing import Optional
from datetime import datetime, timedelta
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

@router.get("/comment_orders")
async def get_comment_orders(
   date_from: Optional[str] = Query(None),
   date_to: Optional[str] = Query(None), 
   db=Depends(get_db)
):
   try:
       # Если даты не указаны, берем последние 24 часа
       if not date_from or not date_to:
           date_to = datetime.now()
           date_from = date_to - timedelta(days=1)
           date_to = date_to.replace(hour=23, minute=59, second=59)
           date_from = date_from.replace(hour=0, minute=0, second=0)
       else:
           date_from = datetime.strptime(date_from, "%Y-%m-%d %H:%M:%S")
           date_to = datetime.strptime(date_to, "%Y-%m-%d %H:%M:%S")

       query = """
           SELECT id, date, phone, manager_name ,notes, date
           FROM calls_data 
           WHERE comment_order = FALSE 
           AND date BETWEEN %s AND %s
       """

       logger.info(f"Executing query for dates from {date_from} to {date_to}")
       
       async with db.pool.acquire() as connection:
           async with connection.cursor() as cursor:
               await cursor.execute(query, (date_from, date_to))
               records = await cursor.fetchall()
               logger.info(f"Fetched {len(records)} records from database")

               # Преобразование datetime в строку
               for record in records:
                   for key, value in record.items():
                       if isinstance(value, datetime):
                           record[key] = value.strftime("%Y-%m-%d %H:%M:%S")

       logger.info("Returning records to client")
       return JSONResponse(
           status_code=200, 
           content={"status": "success", "data": records}
       )

   except Exception as e:
       logger.error(f"An error occurred while processing the request: {e}")
       return JSONResponse(
           status_code=500,
           content={"status": "failure", "message": str(e)}
       )