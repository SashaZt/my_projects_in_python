from sqlalchemy import Column, Integer, String, Boolean
from app.db.base import Base


class OrderStatus(Base):
    """Справочник статусов заказов."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)
    type = Column(Integer)
    sort = Column(Integer)


class OrderType(Base):
    """Справочник типов заказов."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


class Organization(Base):
    """Справочник организаций."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


class ShippingMethod(Base):
    """Справочник методов доставки."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


class PaymentMethod(Base):
    """Справочник методов оплаты."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


class Campaign(Base):
    """Справочник рекламных кампаний."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


class Manager(Base):
    """Справочник менеджеров."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


class TipProdajuType(Base):
    """Справочник типов продаж."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


class ClientSourceType(Base):
    """Справочник источников от клиентов (dzereloKomentarVidKlienta)."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)


class Stock(Base):
    """Справочник складов."""
    
    id = Column(Integer, primary_key=True)
    text = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)