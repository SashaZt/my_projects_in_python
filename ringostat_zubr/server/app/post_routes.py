import json
import re
from typing import List

from configuration.logger_setup import logger  # Настройка логирования

# Импорт класса для работы с базой данных
from database import DatabaseInitializer, wait_for_db
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

router = APIRouter()


async def get_db():
    db_initializer = DatabaseInitializer()
    # Создание базы данных, если она не существует
    await wait_for_db()  # Убедитесь, что MySQL готов
    await db_initializer.create_database()
    await db_initializer.create_pool()  # Создание пула соединений к базе данных
    # Инициализация базы данных и создание необходимых таблиц
    await db_initializer.init_db()
    return db_initializer


# Модель для входных данных
class DeleteRecord(BaseModel):
    call_date: str
    caller_number: str
    employee_ext_number: str
    employee: str


# Pydantic модель для валидации входящих данных
class CallData(BaseModel):
    date: str
    phone: str
    line: str
    manager_name: str
    call_text_ukr: str
    overview: str
    notes: str
    mp3_link: str
    file_name: str
    transcript_id: str


def clean_text(text):
    """Удаляет неподходящие символы из текста."""
    return re.sub(r"[^\w\s.,!?@()-]", "", text)


@router.post("/ringostat_zubr")
async def ringostat_post(request: Request, db=Depends(get_db)):
    try:
        data = await request.json()
        logger.debug(f"Получены JSON данные: {data}")

        all_data = {
            "call_recording": data.get("call_recording"),
            "utm_campaign": data.get("utm_campaign"),
            "utm_source": data.get("utm_source"),
            "utm_term": data.get("utm_term"),
            "utm_content": data.get("utm_content"),
            "call_duration": data.get("call_duration"),
            "call_date": data.get("call_date"),
            "employee": data.get("employee"),
            "employee_ext_number": data.get("employee_ext_number"),
            "caller_number": data.get("caller_number"),
            "unique_call": data.get("unique_call"),
            "unique_target_call": data.get("unique_target_call"),
            "number_pool_name": data.get("number_pool_name"),
            "utm_medium": data.get("utm_medium"),
            "substitution_type": data.get("substitution_type"),
            "call_id": data.get("call_id"),
            "talk_time": data.get("talk_time"),
        }

        success = await db.insert_call_data_zubr(all_data)
        if success:
            logger.info(f"Данные успешно добавлены в БД: {all_data}")
            return JSONResponse(
                status_code=200, content={"status": "success", "data": data}
            )
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


# @router.post("/add_call_data")
# async def add_call_data(call_data: CallData, db: DatabaseInitializer = Depends(get_db)):
#     """Маршрут для добавления данных в таблицу calls_data."""
#     try:
#         # Очистка текстовых полей
#         cleaned_data = {
#             "date": call_data.date,
#             "phone": call_data.phone,
#             "line": call_data.line,
#             "manager_name": clean_text(call_data.manager_name),
#             "call_text_ukr": clean_text(call_data.call_text_ukr),
#             "overview": clean_text(call_data.overview),
#             "notes": clean_text(call_data.notes),
#             "mp3_link": call_data.mp3_link,
#             "file_name": call_data.file_name,
#             "transcript_id": call_data.transcript_id,
#         }

#         # Вставка данных в базу
#         success = await db.insert_call_data(cleaned_data)
#         if not success:
#             logger.error(f"Ошибка записи данных в БД: {cleaned_data}")
#             raise HTTPException(status_code=500, detail="Ошибка записи данных в БД")

#         logger.info(f"Данные успешно добавлены: {cleaned_data}")
#         return {"message": "Данные успешно добавлены"}

#     except HTTPException as http_err:
#         logger.error(f"HTTP ошибка: {http_err.detail}")
#         raise
#     except Exception as e:
#         logger.error(f"Неизвестная ошибка в маршруте /add_call_data: {e}")
#         raise HTTPException(status_code=500, detail="Ошибка обработки запроса")

@router.post("/add_call_data")
async def add_call_data(call_data: CallData, db: DatabaseInitializer = Depends(get_db)):
    """Маршрут для добавления данных в таблицу calls_data."""
    try:
        # Сначала проверяем существование transcript_id в базе
        exists = await db.check_transcript_exists(call_data.transcript_id)
        if exists:
            logger.info(f"Запись с transcript_id {call_data.transcript_id} уже существует в БД. Пропускаем.")
            return {"message": "Запись уже существует в БД"}

        # Если записи нет, продолжаем обработку
        cleaned_data = {
            "date": call_data.date,
            "phone": call_data.phone,
            "line": call_data.line,
            "manager_name": clean_text(call_data.manager_name),
            "call_text_ukr": clean_text(call_data.call_text_ukr),
            "overview": clean_text(call_data.overview),
            "notes": clean_text(call_data.notes),
            "mp3_link": call_data.mp3_link,
            "file_name": call_data.file_name,
            "transcript_id": call_data.transcript_id,
        }

        # Вставка данных в базу
        success = await db.insert_call_data(cleaned_data)
        if not success:
            logger.error(f"Ошибка записи данных в БД: {cleaned_data}")
            raise HTTPException(status_code=500, detail="Ошибка записи данных в БД")

        logger.info(f"Данные успешно добавлены: {cleaned_data}")
        return {"message": "Данные успешно добавлены"}

    except HTTPException as http_err:
        logger.error(f"HTTP ошибка: {http_err.detail}")
        raise
    except Exception as e:
        logger.error(f"Неизвестная ошибка в маршруте /add_call_data: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обработки запроса")