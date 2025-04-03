# api/endpoints/user.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.user import User as UserSchema, UserCreate, UserDetail, UserUpdate
from core.database import get_db
from core.logger import logger
from services.user_service import UserService

router = APIRouter()


@router.post("/", response_model=UserSchema)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создание нового пользователя TikTok"""
    user_service = UserService(db)
    try:
        existing_user = await user_service.get_by_tiktok_id(user.tik_tok_id)
        if existing_user:
            raise HTTPException(status_code=400, detail="Пользователь с таким tik_tok_id уже существует")
        
        return await user_service.create(user)
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tiktok_id}", response_model=UserDetail)
async def get_user(tiktok_id: str, db: AsyncSession = Depends(get_db)):
    """Получение детальной информации о пользователе TikTok по его ID"""
    user_service = UserService(db)
    user = await user_service.get_by_tiktok_id(tiktok_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Явно загружаем связанные объекты
    user_dict = {
        "id": user.id,
        "tik_tok_id": user.tik_tok_id,
        "account_key": user.account_key,
        "nickname": user.nickname,
        "unique_id": user.unique_id,
        "avatar_medium": user.avatar_medium,
        "following_visibility": user.following_visibility,
        "is_under_age_18": user.is_under_age_18,
        "open_favorite": user.open_favorite,
        "private_account": user.private_account,
        "signature": user.signature,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "stats_history": [],
        "nickname_history": [],
        "unique_id_history": [],
        "live_streams": [],
        "daily_analytics": []
    }
    
    return UserDetail(**user_dict)


@router.get("/", response_model=List[UserSchema])
async def get_users(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получение списка пользователей с пагинацией"""
    user_service = UserService(db)
    return await user_service.get_all(skip=skip, limit=limit)


@router.put("/{tiktok_id}", response_model=UserSchema)
async def update_user(
    tiktok_id: str, 
    user_update: UserUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Обновление информации о пользователе"""
    user_service = UserService(db)
    user = await user_service.get_by_tiktok_id(tiktok_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return await user_service.update(user.id, user_update)


@router.delete("/{tiktok_id}")
async def delete_user(tiktok_id: str, db: AsyncSession = Depends(get_db)):
    """Удаление пользователя"""
    user_service = UserService(db)
    user = await user_service.get_by_tiktok_id(tiktok_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    await user_service.delete(user.id)
    return {"status": "success", "message": "Пользователь успешно удален"}