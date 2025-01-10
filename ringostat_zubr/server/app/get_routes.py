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

SECRET_AES_KEY = os.getenv(
    "SECRET_AES_KEY"
).encode()  # Байтовый ключ для шифрования/расшифровки
ORIGINAL_ACCESS_KEY = os.getenv("ORIGINAL_ACCESS_KEY")  # Текстовый ключ для проверки


def decrypt_access_key(encrypted_key: str) -> str:
    try:
        logger.info("Decrypting access key")
        encrypted_data = base64.b64decode(encrypted_key)
        iv = encrypted_data[:16]  # IV занимает первые 16 байтов
        ciphertext = encrypted_data[16:]

        cipher = Cipher(
            algorithms.AES(SECRET_AES_KEY), modes.CBC(iv), backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Убираем паддинг
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_key = (unpadder.update(padded_data) + unpadder.finalize()).decode()
        logger.info("Access key decrypted successfully")
        return decrypted_key
    except Exception as e:
        logger.error(f"Failed to decrypt access key: {e}")
        raise


# Первый вариант
# @router.get("/get_all_data")
# async def get_all_data(access_key: str = Query(...), db=Depends(get_db)):
#     try:
#         decrypted_key = decrypt_access_key(access_key)
#         if decrypted_key != ORIGINAL_ACCESS_KEY:
#             raise HTTPException(
#                 status_code=403, detail="Access denied: Invalid access key"
#             )

#         async with db.pool.acquire() as connection:
#             async with connection.cursor() as cursor:
#                 await cursor.execute("SELECT * FROM calls_zubr")
#                 records = await cursor.fetchall()

#         for record in records:
#             for key, value in record.items():
#                 if isinstance(value, datetime):
#                     record[key] = value.strftime("%Y-%m-%d %H:%M:%S")

#         return JSONResponse(
#             status_code=200, content={"status": "success", "data": records}
#         )
#     except Exception as e:
#         return JSONResponse(
#             status_code=500, content={"status": "failure", "message": str(e)}
#         )


# @router.get("/get_all_data")
# async def get_all_data(
#     access_key: str = Query(...),
#     call_recording: Optional[str] = None,
#     utm_campaign: Optional[str] = None,
#     utm_source: Optional[str] = None,
#     utm_term: Optional[str] = None,
#     utm_content: Optional[str] = None,
#     utm_medium: Optional[str] = None,
#     call_duration: Optional[str] = None,
#     call_date: Optional[str] = None,
#     employee: Optional[str] = None,
#     employee_ext_number: Optional[str] = None,
#     caller_number: Optional[str] = None,
#     unique_call: Optional[str] = None,
#     unique_target_call: Optional[str] = None,
#     number_pool_name: Optional[str] = None,
#     substitution_type: Optional[str] = None,
#     call_id: Optional[str] = None,
#     db=Depends(get_db),
# ):
#     try:
#         decrypted_key = decrypt_access_key(access_key)
#         if decrypted_key != ORIGINAL_ACCESS_KEY:
#             raise HTTPException(
#                 status_code=403, detail="Access denied: Invalid access key"
#             )

#         # Формирование SQL-запроса с динамическими условиями
#         query = "SELECT * FROM calls_zubr WHERE 1=1"
#         filters = []
#         params = []

#         # Добавляем условия для каждого переданного параметра, кроме `id`
#         if call_recording:
#             filters.append("call_recording = %s")
#             params.append(call_recording)
#         if utm_campaign:
#             filters.append("utm_campaign = %s")
#             params.append(utm_campaign)
#         if utm_source:
#             filters.append("utm_source = %s")
#             params.append(utm_source)
#         if utm_term:
#             filters.append("utm_term = %s")
#             params.append(utm_term)
#         if utm_content:
#             filters.append("utm_content = %s")
#             params.append(utm_content)
#         if utm_medium:
#             filters.append("utm_medium = %s")
#             params.append(utm_medium)
#         if call_duration:
#             filters.append("call_duration = %s")
#             params.append(call_duration)
#         if call_date:
#             filters.append("call_date = %s")
#             params.append(call_date)
#         if employee:
#             filters.append("employee = %s")
#             params.append(employee)
#         if employee_ext_number:
#             filters.append("employee_ext_number = %s")
#             params.append(employee_ext_number)
#         if caller_number:
#             filters.append("caller_number = %s")
#             params.append(caller_number)
#         if unique_call:
#             filters.append("unique_call = %s")
#             params.append(unique_call)
#         if unique_target_call:
#             filters.append("unique_target_call = %s")
#             params.append(unique_target_call)
#         if number_pool_name:
#             filters.append("number_pool_name = %s")
#             params.append(number_pool_name)
#         if substitution_type:
#             filters.append("substitution_type = %s")
#             params.append(substitution_type)
#         if call_id:
#             filters.append("call_id = %s")
#             params.append(call_id)

#         # Если есть фильтры, добавляем их к запросу
#         if filters:
#             query += " AND " + " AND ".join(filters)

#         async with db.pool.acquire() as connection:
#             async with connection.cursor() as cursor:
#                 await cursor.execute(query, params)
#                 records = await cursor.fetchall()

#         # Преобразование datetime в строку
#         for record in records:
#             for key, value in record.items():
#                 if isinstance(value, datetime):
#                     record[key] = value.strftime("%Y-%m-%d %H:%M:%S")


#         return JSONResponse(
#             status_code=200, content={"status": "success", "data": records}
#         )
#     except Exception as e:
#         return JSONResponse(
#             status_code=500, content={"status": "failure", "message": str(e)}
#         )
# @router.get("/get_all_data")
# async def get_all_data(
#     access_key: str = Query(...),
#     field: Optional[str] = None,
#     condition: Optional[str] = None,
#     value: Optional[str] = None,
#     db=Depends(get_db),
# ):
#     try:
#         logger.info("Received request to /get_all_data")

#         # Расшифровка ключа доступа
#         decrypted_key = decrypt_access_key(access_key)
#         if decrypted_key != ORIGINAL_ACCESS_KEY:
#             logger.warning("Access denied: Invalid access key")
#             raise HTTPException(
#                 status_code=403, detail="Access denied: Invalid access key"
#             )

#         # Формирование SQL-запроса с динамическими условиями
#         logger.info(
#             f"Applying filter: field={field}, condition={condition}, value={value}"
#         )
#         query = "SELECT * FROM calls_zubr WHERE 1=1"
#         params = []

#         # Добавляем фильтр только если все параметры фильтрации заданы
#         if field and condition and value:
#             if condition == "равно":
#                 query += f" AND {field} = %s"
#                 params.append(value)
#             elif condition == "не равно":
#                 query += f" AND {field} != %s"
#                 params.append(value)
#             elif condition == "начинается с":
#                 query += f" AND {field} LIKE %s"
#                 params.append(f"{value}%")
#             elif condition == "заканчивается на":
#                 query += f" AND {field} LIKE %s"
#                 params.append(f"%{value}")
#             elif condition == "содержит":
#                 query += f" AND {field} LIKE %s"
#                 params.append(f"%{value}%")
#             elif condition == "не содержит":
#                 query += f" AND {field} NOT LIKE %s"
#                 params.append(f"%{value}%")

#         logger.info(f"Executing SQL query: {query} with params {params}")
#         async with db.pool.acquire() as connection:
#             async with connection.cursor() as cursor:
#                 await cursor.execute(query, params)
#                 records = await cursor.fetchall()
#                 logger.info(
#                     f"Query executed successfully, fetched {len(records)} records"
#                 )

#         # Преобразование datetime в строку
#         for record in records:
#             for key, value in record.items():
#                 if isinstance(value, datetime):
#                     record[key] = value.strftime("%Y-%m-%d %H:%M:%S")

#         logger.info("Returning response with data")
#         return JSONResponse(
#             status_code=200, content={"status": "success", "data": records}
#         )

#     except Exception as e:
#         logger.error(f"An error occurred while processing the request: {e}")
#         return JSONResponse(
#             status_code=500, content={"status": "failure", "message": str(e)}
#         )


@router.get("/get_all_data")
async def get_all_data(access_key: str = Query(...), db=Depends(get_db)):
    try:
        # decrypted_key = decrypt_access_key(access_key)
        # if decrypted_key != ORIGINAL_ACCESS_KEY:
        #     logger.warning("Access denied: Invalid access key")
        #     raise HTTPException(
        #         status_code=403, detail="Access denied: Invalid access key"
        #     )

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
