from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import Column, DateTime, func, Integer, MetaData
from datetime import datetime
from typing import Any

# Создаем метаданные заранее
metadata = MetaData()

class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy моделей."""
    
    # Используем созданные метаданные
    metadata = metadata
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Генерирует имя таблицы на основе имени класса.
        Например, класс OrderItem => таблица order_item
        """
        # Преобразуем CamelCase в snake_case
        name = cls.__name__
        # Вставляем "_" перед каждой заглавной буквой и преобразуем в нижний регистр
        table_name = ""
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                table_name += "_"
            table_name += char.lower()
        return table_name


class TimestampMixin:
    """Миксин для добавления полей created_at и updated_at."""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class BaseModel(Base, TimestampMixin):
    """
    Базовый класс модели с идентификатором и временными метками.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)