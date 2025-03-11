# app/models/base.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from typing import Any

class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy"""
    
    # Генерация repr для моделей
    def __repr__(self) -> str:
        columns = [c.name for c in self.__table__.columns]
        values = {c: getattr(self, c) for c in columns}
        return f"<{self.__class__.__name__} {values}>"

# Пример базовой модели
class BaseModel(Base):
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)