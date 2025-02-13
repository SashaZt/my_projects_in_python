# app/api/olx_token_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.services.olx_service import OLXService
from loguru import logger

router = APIRouter(prefix="/olx", tags=["olx-token"])

@router.post("/token/refresh")
async def refresh_token(db: AsyncSession = Depends(get_db)):
    """Обновить токен вручную"""
    try:
        service = OLXService(db)
        result = await service.refresh_token()
        
        if result:
            return {
                "message": "Token refreshed successfully",
                "token_data": {
                    "expires_in": result["expires_in"],
                    "scope": result["scope"],
                    "token_type": result["token_type"]
                }
            }
        raise HTTPException(status_code=400, detail="Failed to refresh token")
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/token/status")
async def get_token_status(db: AsyncSession = Depends(get_db)):
    """Получить статус текущего токена"""
    try:
        service = OLXService(db)
        token = await service.get_current_token()
        
        if not token:
            return {"status": "no_token"}
            
        is_expired = await service.is_token_expired(token)
        
        return {
            "status": "expired" if is_expired else "active",
            "token_type": token.token_type,
            "scope": token.scope,
            "expires_in": token.expires_in,
            "updated_at": token.updated_at
        }
    except Exception as e:
        logger.error(f"Error getting token status: {e}")
        raise HTTPException(status_code=500, detail=str(e))