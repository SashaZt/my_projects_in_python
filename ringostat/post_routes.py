from fastapi.responses import JSONResponse
from database import DatabaseInitializer  # Импорт класса для работы с базой данных
from typing import List, Optional, Dict, Any
import aiomysql
from fastapi import (
    FastAPI,
    Request,
    Query,
    Depends,
    HTTPException,
    APIRouter,
    UploadFile,
    File,
    Body,
)
from fastapi.encoders import jsonable_encoder
from pathlib import Path
import json
from datetime import datetime
from contextlib import asynccontextmanager
from configuration.logger_setup import logger  # Настройка логирования
from pydantic import BaseModel, Field, EmailStr
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse

router = APIRouter()

# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request, exc):
#     logger.error(f"Ошибка валидации: {exc}")
#     return PlainTextResponse(str(exc), status_code=422)


# Путь для сохранения файлов
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)  # Создаем директорию, если её нет


async def get_db():
    db_initializer = DatabaseInitializer()
    await db_initializer.create_database()
    await db_initializer.create_pool()
    await db_initializer.init_db()
    return db_initializer


# Модели данных
class AdditionalContact(BaseModel):
    name: str
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None


class MessengerData(BaseModel):
    messenger: str
    link: str


class PaymentDetail(BaseModel):
    IBAN: str
    BankName: Optional[str] = None
    SWIFT: Optional[str] = None
    AccountType: Optional[str] = None
    Currency: Optional[str] = None


class ContactModel(BaseModel):
    contactId: Optional[int] = None
    mode: str
    username: str
    contactType: str
    contactStatus: str
    manager: str
    userphone: str
    useremail: EmailStr
    usersite: Optional[str] = None
    comment: Optional[str] = None
    additionalContacts: Optional[List[AdditionalContact]] = None
    messengersData: Optional[List[MessengerData]] = None
    paymentDetails: Optional[List[PaymentDetail]] = None


# Маршрут для создания контакта
@router.post("/contact")
async def create_or_update_contact(contact: ContactModel, db=Depends(get_db)):
    try:
        contact_data = contact.dict()
        contact_id = contact_data.get("contactId")
        mode = contact_data.get("mode")

        # Статические поля
        static_fields = {
            "username": "VARCHAR(255)",
            "contact_type": "VARCHAR(255)",
            "contact_status": "VARCHAR(255)",
            "manager": "VARCHAR(255)",
            "userphone": "VARCHAR(20)",
            "useremail": "VARCHAR(255)",
            "usersite": "VARCHAR(255)",
            "comment": "TEXT",
        }

        # Проверка и добавление новых полей в таблицу
        for key in contact_data.keys():
            if key not in static_fields and key not in [
                "contactId",
                "mode",
                "additionalContacts",
                "messengersData",
                "paymentDetails",
            ]:
                await add_column_if_not_exists("contacts", key, "VARCHAR(255)", db)

        if mode == "new" or not contact_id:
            # Создание нового контакта
            new_contact_data = {
                "username": contact_data["username"],
                "contact_type": contact_data["contactType"],
                "contact_status": contact_data["contactStatus"],
                "manager": contact_data["manager"],
                "userphone": contact_data["userphone"],
                "useremail": contact_data["useremail"],
                "usersite": contact_data.get("usersite", ""),
                "comment": contact_data.get("comment", ""),
            }

            # Добавляем динамические данные
            for key in contact_data.keys():
                if key not in static_fields and key not in [
                    "contactId",
                    "mode",
                    "additionalContacts",
                    "messengersData",
                    "paymentDetails",
                ]:
                    new_contact_data[key] = contact_data[key]

            contact_id = await db.insert_contact(new_contact_data)
            logger.info(f"Создан новый контакт с ID {contact_id}")

        elif mode == "edit" and contact_id:
            # Обновление существующего контакта
            update_contact_data = {
                "id": contact_id,
                "username": contact_data["username"],
                "contact_type": contact_data["contactType"],
                "contact_status": contact_data["contactStatus"],
                "manager": contact_data["manager"],
                "userphone": contact_data["userphone"],
                "useremail": contact_data["useremail"],
                "usersite": contact_data.get("usersite", ""),
                "comment": contact_data.get("comment", ""),
            }

            # Добавляем динамические данные
            for key in contact_data.keys():
                if key not in static_fields and key not in [
                    "contactId",
                    "mode",
                    "additionalContacts",
                    "messengersData",
                    "paymentDetails",
                ]:
                    update_contact_data[key] = contact_data[key]

            success = await db.update_contact(update_contact_data)
            if success:
                logger.info(f"Контакт с ID {contact_id} обновлен")
            else:
                raise Exception(f"Не удалось обновить контакт с ID {contact_id}")

        # Обработка дополнительных данных
        if contact_id:
            # Обработка дополнительных контактов
            if contact.additionalContacts:
                for additional_contact in contact.additionalContacts:
                    additional_contact_data = additional_contact.dict()
                    additional_contact_data["contact_id"] = contact_id
                    await db.insert_or_update_additional_contact(
                        additional_contact_data
                    )

            # Обработка данных мессенджеров
            if contact.messengersData:
                for messenger in contact.messengersData:
                    messenger_data = messenger.dict()
                    messenger_data["contact_id"] = contact_id
                    await db.insert_or_update_messenger_data(messenger_data)

            # Обработка платежных данных
            if contact.paymentDetails:
                for payment in contact.paymentDetails:
                    payment_data = payment.dict()
                    payment_data["contact_id"] = contact_id
                    await db.insert_or_update_payment_details(payment_data)

        return JSONResponse(
            status_code=200, content={"status": "success", "contactId": contact_id}
        )

    except Exception as e:
        logger.error(f"Ошибка обработки данных: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "failure", "message": f"Failed to process data: {e}"},
        )


# Маршрут для получения контактов
@router.post("/contacts")
async def post_filtered_contacts(
    request: Request,
    mini: bool = Query(False, description="Возвращать только id и username"),
    db=Depends(get_db),
):
    try:
        # Чтение тела запроса в любом случае
        try:
            data = await request.json()
        except Exception as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON data")

        # Извлечение фильтров из данных
        searchString = data.get("searchString", "").strip()
        statusFilter = data.get("statusFilter", "").strip()
        contactFilter = data.get("contactFilter", "").strip()
        dateRange = data.get("dateRange", {})
        start = dateRange.get("start", None)
        end = dateRange.get("end", None)
        activeRecords = data.get("activeRecords", "").strip()
        limit = data.get("limit", 10)
        page = data.get("page", 1)
        sortBy = data.get("sortBy", "").strip()
        sortOrder = data.get("sortOrder", "asc").strip()

        # Определение возвращаемых столбцов
        if mini:
            columns = "id, username"
        else:
            contact_columns = await db.get_dynamic_columns("contacts")
            columns = ", ".join(contact_columns)

        # Формирование базового SQL-запроса
        query = f"SELECT {columns} FROM contacts WHERE 1=1"
        parameters = []

        # Применение фильтров
        if searchString:
            query += " AND (LOWER(username) LIKE LOWER(%s) OR LOWER(userphone) LIKE LOWER(%s) OR LOWER(useremail) LIKE LOWER(%s))"
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

        # Выполнение запроса для получения данных
        async with db.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                logger.debug(f"Executing query: {query} with parameters: {parameters}")
                await cursor.execute(query, parameters)
                contacts = await cursor.fetchall()

        # Выполнение отдельного запроса для подсчета общего количества записей
        count_query = "SELECT COUNT(*) as total FROM contacts WHERE 1=1"
        count_params = []

        if searchString:
            count_query += " AND (LOWER(username) LIKE LOWER(%s) OR LOWER(userphone) LIKE LOWER(%s) OR LOWER(useremail) LIKE LOWER(%s))"
            count_params.extend([search_pattern, search_pattern, search_pattern])

        if statusFilter:
            count_query += " AND contact_status = %s"
            count_params.append(statusFilter)

        if contactFilter:
            count_query += " AND contact_type = %s"
            count_params.append(contactFilter)

        if start and end:
            count_query += " AND created_at BETWEEN %s AND %s"
            count_params.extend([start, end])

        if activeRecords:
            count_query += " AND active = %s"
            count_params.append(activeRecords)

        # Выполнение запроса для подсчета
        async with db.pool.acquire() as connection:
            async with connection.cursor(aiomysql.DictCursor) as cursor:
                logger.debug(
                    f"Executing count query: {count_query} with parameters: {count_params}"
                )
                await cursor.execute(count_query, count_params)
                total_records = await cursor.fetchone()

        # Преобразование данных для JSON-сериализации
        contacts = jsonable_encoder(contacts)
        total_records = jsonable_encoder(total_records)

        # Формирование итогового ответа
        total_pages = (total_records["total"] // limit) + 1
        response_content = {
            "data": contacts,
            "totalPages": total_pages,
            "currentPage": page,
        }

        # if mini:
        #     # Если mini=True, возвращаем только данные без пагинации
        #     response_content = {"data": contacts}

        return JSONResponse(status_code=200, content=response_content)

    except Exception as e:
        logger.error(f"Ошибка при получении списка контактов: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


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


@router.post("/task")
async def save_task(
    request: Request, files: Optional[List[UploadFile]] = File(None), db=Depends(get_db)
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
                await db.save_document(
                    {
                        "task_id": task_id,
                        "file_name": file.filename,
                        "file_path": str(file_path),
                    }
                )

        return JSONResponse(
            status_code=200, content={"status": "success", "taskId": task_id}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving task: {e}")


"""Добавление нового столбца в таблицу, если его еще нет"""


async def add_column_if_not_exists(
    table_name: str, column_name: str, data_type: str, db
):

    async with db.pool.acquire() as connection:
        async with connection.cursor() as cursor:
            # Проверка наличия столбца
            await cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'")
            result = await cursor.fetchone()
            if not result:
                # Добавляем новый столбец
                await cursor.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}"
                )
                # Сохраняем метаданные
                await cursor.execute(
                    "INSERT INTO table_metadata (table_name, column_name, data_type) VALUES (%s, %s, %s)",
                    (table_name, column_name, data_type),
                )
                logger.info(
                    f"Добавлен новый столбец {column_name} в таблицу {table_name}"
                )


# Pydantic модель для простых контактов (содержит только name и email)
class SimpleContactModel(BaseModel):
    name: str
    email: EmailStr


# Pydantic модель для конфигурации, использующая SimpleContactModel
class ConfigModel(BaseModel):
    Reviewers: List[SimpleContactModel]
    Admin: List[SimpleContactModel]
    Initiators: List[SimpleContactModel]
    Performers: List[SimpleContactModel]


# Новый маршрут для сохранения конфигурации с ручной обработкой JSON
@router.post("/setconfig")
async def set_config(request: Request, db=Depends(get_db)):
    """Сохраняет конфигурационные данные для формы 'Задачи'."""
    try:
        # Ручное получение данных из запроса
        body = await request.body()
        config_data = ConfigModel.parse_raw(body)

        # Логирование данных для отладки
        logger.info(f"Полученные данные конфигурации: {config_data}")

        # Преобразуем конфигурационные данные в словарь, чтобы сохранить их в базе данных
        config_dict = {
            "Reviewers": ", ".join(
                [f"{contact.email}:{contact.name}" for contact in config_data.Reviewers]
            ),
            "Admin": ", ".join([f"{contact.email}" for contact in config_data.Admin]),
            "Initiators": ", ".join(
                [
                    f"{contact.email}:{contact.name}"
                    for contact in config_data.Initiators
                ]
            ),
            "Performers": ", ".join(
                [
                    f"{contact.email}:{contact.name}"
                    for contact in config_data.Performers
                ]
            ),
        }

        # Сохраняем конфигурационные данные в базе данных
        success = await db.save_config_to_db(config_dict)

        if not success:
            raise HTTPException(
                status_code=500, detail="Ошибка при сохранении конфигурационных данных"
            )

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Конфигурационные данные успешно сохранены",
            },
        )

    except Exception as e:
        logger.error(f"Ошибка при сохранении конфигурационных данных: {e}")
        raise HTTPException(
            status_code=500, detail="Ошибка при сохранении конфигурационных данных"
        )
