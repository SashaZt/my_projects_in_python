import json

from configuration.logger_setup import logger  # Настройка логирования
# Импорт класса для работы с базой данных
from database import DatabaseInitializer
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

router = APIRouter()


async def get_db():
    db_initializer = DatabaseInitializer()
    # Создание базы данных, если она не существует
    await db_initializer.create_database()
    await db_initializer.create_pool()  # Создание пула соединений к базе данных
    # Инициализация базы данных и создание необходимых таблиц
    await db_initializer.init_db()
    return db_initializer


@router.post("/ringostat_zubr")
async def ringostat_post(request: Request, db=Depends(get_db)):
    try:
        data = await request.json()
        logger.debug(f"Получены JSON данные: {data}")

        all_data = {
            'call_recording': data.get("call_recording"),
            'utm_campaign':  data.get("utm_campaign"),
            'utm_source':  data.get("utm_source"),
            'utm_term':  data.get("utm_term"),
            'utm_content':  data.get("utm_content"),
            'call_duration':  data.get("call_duration"),
            'call_date':  data.get("call_date"),
            'employee':  data.get("employee"),
            'employee_ext_number':  data.get("employee_ext_number"),
            'caller_number':  data.get("caller_number"),
            'unique_call':  data.get("unique_call"),
            'unique_target_call': data.get("unique_target_call"),
            'number_pool_name':  data.get("number_pool_name"),
            'utm_medium':  data.get("utm_medium"),
            'substitution_type':  data.get("substitution_type"),
            'call_id':  data.get("call_id"),
        }

        success = await db.insert_call_data_zubr(all_data)
        if success:
            logger.info(f"Данные успешно добавлены в БД: {all_data}")
            return JSONResponse(status_code=200, content={"status": "success", "data": data})
        else:
            logger.error(f"Ошибка при добавлении данных в БД: {all_data}")
            return JSONResponse(status_code=500, content={"status": "failure", "message": "Failed to save data"})

    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON данных")
        return JSONResponse(status_code=400, content={"status": "failure", "message": "Invalid JSON data"})
    except Exception as e:
        logger.error(f"Не удалось сохранить данные: {e}")
        return JSONResponse(status_code=500, content={"status": "failure", "message": f"Failed to save data: {e}"})
