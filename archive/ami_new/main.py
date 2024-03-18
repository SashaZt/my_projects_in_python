import asyncio
import logging

from fastapi import FastAPI, UploadFile, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.requests import Request
from config import secret, username, host
import ami_handler
from database import SessionLocal
from database_operations import get_all_data, upload_data_from_file, create_new_cold_call
# from models import SessionLocal
from schemas import ColdCallModel, ColdCallCreate

app = FastAPI()

templates = Jinja2Templates(directory="templates")
# Настройка логгера
logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

"""uvicorn main:app --reload  Запускать приложение"""


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


"""Переход на страничку для загрузки номеров в mysql"""


@app.get("/upload/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


"""Загрузка номеров в mysql"""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/get_data/")
def get_data(db: Session = Depends(get_db)):
    return get_all_data(db)


@app.post("/create_cold_call/", response_model=ColdCallModel)
def create_cold_call(cold_call: ColdCallCreate, db: Session = Depends(get_db)):
    return create_new_cold_call(db, cold_call)


@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile, db: Session = Depends(get_db)):
    try:
        added_count, invalid_numbers = await upload_data_from_file(db, file)
        message = f"Успешно добавлено {added_count} записей!"
        if invalid_numbers:
            message += f" Неверные номера: {', '.join(invalid_numbers)}"
        return templates.TemplateResponse("success.html", {"request": request, "message": message})
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return templates.TemplateResponse("error.html", {"request": request, "message": "Ошибка при обработке файла."})


async def start_calls(db: Session = Depends(get_db)):
    client_list = await ami_handler.load_client_list(db)
    asyncio.create_task(ami_handler.call_clients(client_list))
    return {"message": "Процесс обзвона начат"}


@app.on_event("startup")
async def startup_event():
    logger.info("Starting AMI connection")
    try:
        ami_handler.initialize_manager(
            host=host,
            port=5038,
            username=username,
            secret=secret,
            ping_delay=5
        )
        # Подключение к AMI
        await ami_handler.manager.connect()
        logger.info("AMI connection established")
    except Exception as e:
        logger.error(f"Error connecting to AMI: {e}")


# main.py
@app.post("/start_calls/")
async def start_calls(db: Session = Depends(get_db)):
    await ami_handler.load_client_list(db)
    asyncio.create_task(ami_handler.call_clients(ami_handler.manager))
    return {"message": "Процесс обзвона начат"}
@app.post("/call_number/")
async def call_number(number: str, db: Session = Depends(get_db)):
    # Логика для инициации звонка на номер number
    return {"message": f"Звонок на номер {number} инициирован"}