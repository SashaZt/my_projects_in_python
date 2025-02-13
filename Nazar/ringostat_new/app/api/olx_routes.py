# # app/api/olx_routes.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import sys
from pydantic import BaseModel
import secrets
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
import httpx
from pydantic import BaseModel
import secrets
from typing import Optional
from loguru import logger
from app.services.olx_service import OLXService
from typing import Optional
from app.core.config import OLX_CONFIG
from loguru import logger
from pathlib import Path
from app.core.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Настройка логирования
current_directory = Path.cwd()
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "olx_oauth.log"

logger.remove()
# Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# Логирование в консоль
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)
router = APIRouter()
states = set()


class TokenResponse(BaseModel):
    access_token: str
    expires_in: int
    token_type: str
    scope: str
    refresh_token: str


@router.get("/auth/connect")
async def auth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Обработчик callback от OLX"""
    logger.debug(f"Auth callback received with code: {code} and state: {state}")
    try:
        if not state or state not in states:
            logger.warning(f"Invalid state received: {state}")
            return {"error": "Invalid state"}

        states.remove(state)

        if not code:
            logger.warning("No code provided in callback")
            return {"error": "No code provided"}

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Version": "2.0",
        }

        data = {
            "grant_type": "authorization_code",
            "client_id": OLX_CONFIG["client_id"],
            "client_secret": OLX_CONFIG["client_secret"],
            "code": code,
            "scope": "v2 read write",
            "redirect_uri": OLX_CONFIG["redirect_uri"],
        }

        async with httpx.AsyncClient(verify=False) as client:
            response = await client.post(
                "https://www.olx.ua/api/open/oauth/token", json=data, headers=headers
            )

            if response.status_code == 200:
                token_data = response.json()

                # Сохраняем токены в базу данных
                olx_service = OLXService(db)
                await olx_service.save_tokens(token_data)

                logger.info("Successfully received and saved OLX tokens")
                return {
                    "message": "Successfully authenticated",
                    "token_data": TokenResponse(**token_data),
                }
            else:
                error_msg = f"Failed to get token. Status: {response.status_code}, Response: {response.text}"
                logger.error(error_msg)
                return {"error": "Failed to get token", "details": response.text}

    except Exception as e:
        logger.error(f"Error during token exchange: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/olx/login")
async def login_olx():
    """Инициирует процесс OAuth авторизации OLX"""
    try:
        state = secrets.token_urlsafe(32)
        states.add(state)

        auth_url = (
            f"{OLX_CONFIG['authorize_url']}"
            f"?client_id={OLX_CONFIG['client_id']}"
            f"&response_type=code"
            f"&state={state}"
            f"&scope=read write v2"
            f"&redirect_uri={OLX_CONFIG['redirect_uri']}"
        )

        logger.info(f"Redirecting to OLX authorization URL with state: {state}")
        logger.debug(f"Authorization URL: {auth_url}")
        return RedirectResponse(url=auth_url)
    except Exception as e:
        logger.error(f"Error during OLX login initialization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Добавим эндпоинт для проверки текущего токена
@router.get("/olx/token")
async def get_current_token(db: AsyncSession = Depends(get_db)):
    """Получить текущий токен"""
    try:
        olx_service = OLXService(db)
        token = await olx_service.get_current_token()
        if token:
            return {
                "access_token": token.access_token,
                "expires_in": token.expires_in,
                "scope": token.scope,
            }
        return {"message": "No token found"}
    except Exception as e:
        logger.error(f"Error getting current token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/olx/token/check")
async def check_token(db: AsyncSession = Depends(get_db)):
    """Проверить текущий токен"""
    try:
        olx_service = OLXService(db)
        token = await olx_service.get_current_token()
        if token:
            return {
                "status": "active",
                "token_type": token.token_type,
                "scope": token.scope,
                "expires_in": token.expires_in
            }
        return {"status": "no_token"}
    except Exception as e:
        logger.error(f"Error checking token: {e}")
        raise HTTPException(status_code=500, detail=str(e))