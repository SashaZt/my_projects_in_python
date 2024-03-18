import base64
import csv
import logging
from datetime import date

import requests
from fastapi import FastAPI, UploadFile, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.requests import Request

from database import engine, SessionLocal
from models import Base, ColdCall
from models import SessionLocal
from schemas import ColdCallModel, ColdCallCreate

"""uvicorn main:app --reload  Запускать приложение"""
# Настройка логгера
logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все методы
    allow_headers=["*"],  # Разрешает все заголовки
)

username = "someuser"
password = "30ae9039c371a0070dc4c63d3ad8ed37"
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
auth_header = f"Basic {encoded_credentials}"

# Создание таблиц в базе данных (если они еще не созданы)
Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")



"""Переход на главную страницу"""
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/get_data/")
def get_data(db: Session = Depends(get_db)):
    data = db.query(ColdCall).all()
    return data

"""Переход на страничку для загрузки номеров в mysql"""
@app.get("/upload/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

"""Загрузка номеров в mysql"""
@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile, db: Session = Depends(get_db)):
    try:
        if file.filename.endswith('.csv') or file.filename.endswith('.txt'):
            content = await file.read()
            content = content.decode()

            lines = content.split('\n')
            reader = csv.reader(lines)

            added_count = 0  # Счетчик добавленных записей
            invalid_numbers = []  # Список для номеров, которые не соответствуют требованиям

            for row in reader:
                nomer = row[0]
                if not (nomer.isdigit() and len(nomer) == 10):
                    invalid_numbers.append(nomer)  # Добавляем номер в список
                    continue

                existing_call = db.query(ColdCall).filter(ColdCall.nomer == nomer).first()
                if not existing_call:
                    new_call = ColdCall(nomer=nomer, date_of_creation=date.today())
                    db.add(new_call)
                    added_count += 1

            db.commit()
            await file.close()

            # Формируем ответ
            message = f"Успешно добавлено {added_count} записей!"
            if invalid_numbers:
                message += f" Неверные номера: {', '.join(invalid_numbers)}"

            return templates.TemplateResponse("success.html", {"request": request, "message": message})

    except HTTPException as http_error:
        return templates.TemplateResponse("error.html", {"request": request, "message": str(http_error.detail)})

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return templates.TemplateResponse("error.html", {"request": request, "message": "Ошибка при обработке файла."})


""""Остнавное приложение для звонков"""
@app.get("/make_call/{number}")
def make_call(number: str):
    url = "http://31.41.216.130:8088/ari/channels/originate"
    params = {
        "endpoint": f"SIP/10314552/{number}",
        "extension": "777",  # Здесь указываем номер оператора
        "context": "custom-call-routing",
        "priority": 1,
        "app": "make_call"
    }
    headers = {
        "Authorization": auth_header
    }
    response = requests.post(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "error": f"Ошибка при попытке совершить звонок. Статус: {response.status_code}, Тело ответа: {response.text}"}



@app.post("/create_cold_call/", response_model=ColdCallModel)
def create_cold_call(cold_call: ColdCallCreate, db: Session = Depends(get_db)):
    db_cold_call = ColdCall(**cold_call.dict())
    db.add(db_cold_call)
    db.commit()
    db.refresh(db_cold_call)
    return db_cold_call
