from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.core.dependencies import get_db
from app.schemas.telegram import TelegramMessageSchema, UserSchema, MessageSchema
from app.models.telegram_message import TelegramMessage
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import secrets
from typing import Optional
import uvicorn
from loguru import logger
from pathlib import Path
import sys
current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"

router = APIRouter()

logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)

@router.get("/telegram/messages", response_model=list[TelegramMessageSchema])
async def get_all_telegram_messages(db: AsyncSession = Depends(get_db)):
    """
    Получить все сообщения Telegram с данными отправителя и получателя.

    :param db: Асинхронная сессия базы данных.
    :return: Список сообщений с полными данными.
    """
    try:
        query = select(TelegramMessage).options(
            joinedload(TelegramMessage.sender), joinedload(TelegramMessage.recipient)
        )
        result = await db.execute(query)
        messages = result.scalars().all()

        if not messages:
            logger.info("Сообщения отсутствуют в базе данных.")
            return []

        serialized_messages = [
            TelegramMessageSchema(
                sender=UserSchema(
                    name=message.sender.name,
                    username=message.sender.username,
                    telegram_id=message.sender.telegram_id,
                    phone=message.sender.phone,
                ),
                recipient=UserSchema(
                    name=message.recipient.name,
                    username=message.recipient.username,
                    telegram_id=message.recipient.telegram_id,
                    phone=message.recipient.phone,
                ),
                message=MessageSchema(
                    message_id=message.message_id,
                    text=message.message,  # изменено с text на message согласно модели
                    is_reply=message.is_reply,
                    reply_to=message.reply_to,
                    read=message.is_read,  # изменено с read на is_read согласно модели
                    direction=message.direction,
                ),
            )
            for message in messages
        ]

        logger.info(f"Получено {len(serialized_messages)} сообщений из базы данных.")
        return serialized_messages

    except Exception as e:
        logger.error(f"Ошибка при получении сообщений: {e}")
        raise HTTPException(
            status_code=500, detail=f"Ошибка при получении сообщений: {e}"
        )

# OLX_CONFIG = {
#     "client_id": "202061",  # Замените на ваш client_id
#     "client_secret": "I4MVWEcN5OPsrFcyP3x5wkWzZ8UY2yWjOmrQMoWucu8uVJpo",  # Замените на ваш client_secret
#     "redirect_uri": "https://185.233.116.213:5000/auth/connect",
#     "authorize_url": "https://www.olx.ua/oauth/authorize/",
#     "token_url": "https://www.olx.ua/api/open/oauth/token"
# }

# # Хранилище для state (в продакшене лучше использовать Redis или базу данных)
# states = set()

# class TokenResponse(BaseModel):
#     access_token: str
#     expires_in: int
#     token_type: str
#     scope: str
#     refresh_token: str

# @router.get("/")
# async def root():
#     return {"message": "OLX OAuth Integration"}

# @router.get("/login/olx")
# async def login_olx():
#     # Генерируем state для безопасности
#     state = secrets.token_urlsafe(32)
#     states.add(state)
    
#     # Формируем URL для авторизации
#     auth_url = (
#         f"{OLX_CONFIG['authorize_url']}"
#         f"?client_id={OLX_CONFIG['client_id']}"
#         f"&response_type=code"
#         f"&state={state}"
#         f"&scope=read write v2"
#         f"&redirect_uri={OLX_CONFIG['redirect_uri']}"
#     )
    
#     return RedirectResponse(url=auth_url)

# @router.get("/auth/connect")
# async def auth_callback(code: Optional[str] = None, state: Optional[str] = None):
#     # Проверяем state
#     if not state or state not in states:
#         return {"error": "Invalid state"}
    
#     # Удаляем использованный state
#     states.remove(state)
    
#     if not code:
#         return {"error": "No code provided"}
    
#     # Обмениваем код на токен
#     async with httpx.AsyncClient() as client:
#         try:
#             response = await client.post(
#                 OLX_CONFIG["token_url"],
#                 json={
#                     "grant_type": "authorization_code",
#                     "client_id": OLX_CONFIG["client_id"],
#                     "client_secret": OLX_CONFIG["client_secret"],
#                     "code": code,
#                     "scope": "v2 read write",
#                     "redirect_uri": OLX_CONFIG["redirect_uri"]
#                 }
#             )
            
#             if response.status_code == 200:
#                 token_data = TokenResponse(**response.json())
#                 return {
#                     "message": "Successfully authenticated",
#                     "token_data": token_data
#                 }
#             else:
#                 return {
#                     "error": "Failed to get token",
#                     "details": response.json()
#                 }
                
#         except Exception as e:
#             return {"error": f"Error during token exchange: {str(e)}"}
