# services/user_service.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from schemas.user import UserCreate, UserUpdate

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user_data: UserCreate) -> User:
        """Создание нового пользователя"""
        user = User(
            tik_tok_id=user_data.tik_tok_id,
            nickname=user_data.nickname,
            unique_id=user_data.unique_id,
            avatar_medium=user_data.avatar_medium,
            following_visibility=user_data.following_visibility,
            is_under_age_18=user_data.is_under_age_18,
            open_favorite=user_data.open_favorite,
            private_account=user_data.private_account,
            signature=user_data.signature
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()
    
    async def get_by_tiktok_id(self, tiktok_id: str) -> Optional[User]:
        """Получение пользователя по TikTok ID"""
        result = await self.db.execute(select(User).where(User.tik_tok_id == tiktok_id))
        return result.scalars().first()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение списка пользователей с пагинацией"""
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()
    
    async def update(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Обновление информации о пользователе"""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        # Обновляем только переданные поля
        user_data_dict = user_data.dict(exclude_unset=True)
        for key, value in user_data_dict.items():
            setattr(user, key, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: int) -> bool:
        """Удаление пользователя"""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        await self.db.delete(user)
        await self.db.commit()
        return True