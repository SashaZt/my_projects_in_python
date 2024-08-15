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



# Установка директорий для логов и данных
current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
log_directory = temp_path / "log"
data_directory = temp_path / "data"
ringostat_directory = data_directory / "ringostat"

log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
ringostat_directory.mkdir(parents=True, exist_ok=True)

# Создаем глобальный объект db_initializer
db_initializer = None

# Управление жизненным циклом приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_initializer  # Используем глобальный db_initializer
    db_initializer = DatabaseInitializer()
    await db_initializer.create_database()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    yield
    await db_initializer.close_pool()

app = FastAPI(lifespan=lifespan)

# Используем Depends для передачи db_initializer в эндпоинт
@app.get('/calls')
async def get_calls(
    request: Request,
    db: DatabaseInitializer = Depends(lambda: db_initializer)
):
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

                return JSONResponse(status_code=200, content={"status": "success", "data": calls_serializable})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "failure", "message": str(e)})


# Эндпоинт POST для обработки данных вебхука
@app.post('/ringostat')
async def ringostat_post(request: Request):
    try:
        data = await request.json()
        logger.debug(f"Получены JSON данные: {data}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file_path = ringostat_directory / f"data_{timestamp}.json"

        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        logger.debug(f"Данные сохранены в файл: {json_file_path}")
    except json.JSONDecodeError:
        logger.error("Ошибка декодирования JSON данных")
        return JSONResponse(status_code=400, content={"status": "failure", "message": "Invalid JSON data"})
    except Exception as e:
        logger.error(f"Не удалось сохранить данные: {e}")
        return JSONResponse(status_code=500, content={"status": "failure", "message": "Failed to save data"})

    return JSONResponse(status_code=200, content={"status": "success", "data": data})

# Эндпоинт GET для проверки состояния вебхука
@app.get('/ringostat')
async def ringostat_get():
    logger.debug("GET запрос на /ringostat - вебхук работает корректно")
    return JSONResponse(status_code=200, content={"status": "success", "message": "Webhook endpoint is up and running"})


class ContactData(BaseModel):
    data: Dict[str, Any] = Field(..., description="Данные для записи в таблицы contacts_")

async def ensure_column_exists(table_name: str, column_name: str, column_type: str, db: DatabaseInitializer):
    """Проверить, существует ли колонка в таблице, и если нет, добавить её."""
    async with db.pool.acquire() as connection:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            logger.info(f"Проверка существования колонки '{column_name}' в таблице '{table_name}'.")
            await cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE %s", (column_name,))
            column_exists = await cursor.fetchone()

            if not column_exists:
                logger.info(f"Колонка '{column_name}' отсутствует в таблице '{table_name}'. Добавляем колонку.")
                await cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                await connection.commit()
                logger.info(f"Колонка '{column_name}' добавлена в таблицу '{table_name}'.")

async def insert_dynamic_data(table_name: str, data: Dict[str, Any], db: DatabaseInitializer):
    """Вставка данных в таблицу, динамически добавляя колонки."""
    async with db.pool.acquire() as connection:
        async with connection.cursor(aiomysql.DictCursor) as cursor:
            logger.info(f"Начало вставки данных в таблицу '{table_name}': {data}")
            
            # Получаем существующие колонки таблицы
            await cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            columns = await cursor.fetchall()
            existing_columns = {col['Field']: col['Type'] for col in columns}

            insert_columns = []
            insert_values = []
            placeholders = []

            for key, value in data.items():
                if key not in existing_columns:
                    logger.info(f"Колонка '{key}' отсутствует в таблице '{table_name}'.")
                    await ensure_column_exists(table_name, key, "VARCHAR(255)", db)
                insert_columns.append(key)
                insert_values.append(value)
                placeholders.append("%s")

            query = f"INSERT INTO {table_name} ({', '.join(insert_columns)}) VALUES ({', '.join(placeholders)})"
            logger.info(f"Выполнение SQL-запроса: {query}")
            await cursor.execute(query, insert_values)
            await connection.commit()
            logger.info(f"Данные успешно вставлены в таблицу '{table_name}'.")

@app.post('/contacts')
async def create_contact(data: ContactData, db: DatabaseInitializer = Depends(lambda: db_initializer)):
    try:
        logger.info(f"Приняты данные для вставки в таблицы contacts_: {data}")
        
        # Вставляем данные в таблицу contacts
        contact_id = None
        if "contacts" in data.data:
            contact_data = data.data.pop("contacts")
            logger.info(f"Вставка данных в таблицу 'contacts': {contact_data}")
            await insert_dynamic_data("contacts", contact_data, db)
            
            async with db.pool.acquire() as connection:
                async with connection.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute("SELECT LAST_INSERT_ID() as last_id")
                    contact_id = (await cursor.fetchone())['last_id']
                    logger.info(f"Получен ID вставленного контакта: {contact_id}")

        if not contact_id:
            logger.error("Не удалось вставить данные в таблицу contacts.")
            raise HTTPException(status_code=500, detail="Failed to insert contact")

        # Вставляем данные в остальные таблицы, связанные с contacts_
        for table_suffix, table_data in data.data.items():
            table_name = f"contacts_{table_suffix}"
            logger.info(f"Обработка таблицы '{table_name}' с данными: {table_data}")
            for record in table_data:
                record["contact_id"] = contact_id
                await insert_dynamic_data(table_name, record, db)

        logger.info("Данные успешно вставлены во все таблицы contacts_.")
        return {"status": "success", "message": "Contact created successfully"}
    except Exception as e:
        logger.error(f"Ошибка при вставке данных в таблицы contacts_: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create contact: {e}")


@app.get('/contacts')
async def get_all_contacts(
    name: Optional[str] = None,
    surname: Optional[str] = None,
    formal_title: Optional[str] = None,
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    db: DatabaseInitializer = Depends(lambda: db_initializer)
):
    try:
        logger.info("Начало получения данных с фильтрацией по параметрам.")

        # Собираем все переданные параметры в словарь
        filters = {
            "name": name,
            "surname": surname,
            "formal_title": formal_title,
            "phone_number": phone_number,
            "email": email
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
        raise HTTPException(status_code=500, detail=f"Failed to retrieve contact data: {e}")


if __name__ == '__main__':
    logger.debug("Запуск FastAPI сервера")
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)
