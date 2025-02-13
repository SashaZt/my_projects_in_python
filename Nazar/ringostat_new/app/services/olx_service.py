# app/services/olx_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.olx_token import OLXToken
from loguru import logger
import httpx
from typing import Optional, Dict, Any
from app.core.config import OLX_CONFIG
from datetime import datetime, timedelta

class OLXService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_tokens(self, token_data: Dict[str, Any]) -> OLXToken:
        """Сохранить или обновить токены в базе данных"""
        try:
            query = select(OLXToken)
            result = await self.db.execute(query)
            existing_token = result.scalar_one_or_none()

            if existing_token:
                existing_token.access_token = token_data["access_token"]
                existing_token.refresh_token = token_data["refresh_token"]
                existing_token.expires_in = token_data["expires_in"]
                existing_token.token_type = token_data["token_type"]
                existing_token.scope = token_data["scope"]
                token = existing_token
            else:
                token = OLXToken(**token_data)
                self.db.add(token)

            await self.db.commit()
            await self.db.refresh(token)
            logger.info("Токены OLX успешно сохранены")
            return token

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Ошибка при сохранении токенов: {e}")
            raise

    async def get_current_token(self) -> Optional[OLXToken]:
        """Получить текущий токен из базы данных"""
        try:
            query = select(OLXToken)
            result = await self.db.execute(query)
            token = result.scalar_one_or_none()
            return token
        except Exception as e:
            logger.error(f"Ошибка при получении токена: {e}")
            return None

    async def is_token_expired(self, token: OLXToken) -> bool:
        """Проверить, истек ли срок действия токена"""
        if not token.updated_at:
            return True
            
        expiration_time = token.updated_at + timedelta(seconds=token.expires_in)
        return datetime.utcnow() > expiration_time

    async def refresh_token(self) -> Optional[Dict[str, Any]]:
        """Обновить токен доступа используя refresh_token"""
        try:
            current_token = await self.get_current_token()
            if not current_token:
                logger.error("No token found to refresh")
                return None

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Version": "2.0"
            }

            data = {
                "grant_type": "refresh_token",
                "client_id": OLX_CONFIG["client_id"],
                "client_secret": OLX_CONFIG["client_secret"],
                "refresh_token": current_token.refresh_token
            }

            logger.debug(f"Attempting to refresh token with data: {data}")

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    "https://www.olx.ua/api/open/oauth/token",
                    json=data,
                    headers=headers
                )

                logger.debug(f"Refresh token response status: {response.status_code}")
                logger.debug(f"Refresh token response: {response.text}")

                if response.status_code == 200:
                    token_data = response.json()
                    await self.save_tokens(token_data)
                    logger.info("Token successfully refreshed")
                    return token_data
                else:
                    logger.error(f"Error refreshing token: {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error during token refresh: {e}")
            return None

    async def get_valid_token(self) -> Optional[str]:
        """Получить действующий токен, при необходимости обновить"""
        current_token = await self.get_current_token()
        if not current_token:
            logger.error("No token found")
            return None

        if await self.is_token_expired(current_token):
            logger.info("Token expired, attempting to refresh")
            refresh_result = await self.refresh_token()
            if not refresh_result:
                logger.error("Failed to refresh token")
                return None
            return refresh_result["access_token"]

        return current_token.access_token