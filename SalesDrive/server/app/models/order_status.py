# app/models/order_status.py
from sqlalchemy import Boolean, Column, Integer, String
from app.database import Base

class OrderStatus(Base):
    __tablename__ = "order_status"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    type = Column(Integer, nullable=False)  # Поле type из JSON
    sort = Column(Integer, nullable=False)  # Поле sort из JSON