from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime, 
    ForeignKey, JSON, Table, MetaData, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class SubmissionStatus(Base):
    """Модель статусов отправки данных в BTS/CRM."""
    __tablename__ = "submission_statuses"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PaymentMethod(Base):
    """Модель для способов оплаты."""
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Region(Base):
    """Модель для регионов."""
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True)
    bts_region_id = Column(Integer, unique=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    cities = relationship("City", back_populates="region")

class City(Base):
    """Модель для городов."""
    __tablename__ = "cities"
    
    id = Column(Integer, primary_key=True)
    bts_city_id = Column(Integer, unique=True)
    region_id = Column(Integer, ForeignKey('regions.id'))
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    region = relationship("Region", back_populates="cities")
    branches = relationship("Branch", back_populates="city")

class Branch(Base):
    """Модель для филиалов."""
    __tablename__ = "branches"
    
    id = Column(Integer, primary_key=True)
    bts_branch_id = Column(Integer, unique=True)
    name = Column(String(200), nullable=False)
    city_id = Column(Integer, ForeignKey('cities.id'))
    address = Column(Text)
    location = Column(String(100))  # Координаты lat_long
    phone = Column(String(100))
    video_link = Column(Text)
    working_hours = Column(JSON)  # Расписание работы в формате JSON
    external_id = Column(String(100))  # "id_126_ТашкентЯккасарай2_BTS"
    extracted_branch_id = Column(String(50))  # "126"
    extracted_branch_name = Column(String(200))  # "ТашкентЯккасарай2"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    city = relationship("City", back_populates="branches")
    orders = relationship("Order", back_populates="branch", foreign_keys="Order.branch_id")

class PackageType(Base):
    """Модель для видов упаковки."""
    __tablename__ = "package_types"
    
    id = Column(Integer, primary_key=True)
    bts_package_id = Column(Integer, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PostType(Base):
    """Модель для типов отправки."""
    __tablename__ = "post_types"
    
    id = Column(Integer, primary_key=True)
    bts_post_type_id = Column(Integer, unique=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Contact(Base):
    """Модель для контактной информации."""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True)
    last_name = Column(String(100), nullable=False)
    first_name = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False, unique=True)
    email = Column(String(100))
    address = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    orders = relationship("Order", back_populates="contact")

class Order(Base):
    """Модель для заказов."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    branch_id = Column(Integer, ForeignKey('branches.id'))
    payment_method_id = Column(Integer, ForeignKey('payment_methods.id'))
    
    order_number = Column(String(50))  # Номер заказа в CRM
    client_id = Column(String(100))  # Штрих-код клиента
    wcs_code = Column(String(100))  # Уникальный код заказа для BTS
    bts_order_id = Column(String(100))  # Номер заказа в BTS
    
    # Данные отправителя
    sender_name = Column(String(200))
    sender_phone = Column(String(50))
    sender_city_id = Column(Integer, ForeignKey('cities.id'))
    sender_address = Column(Text)
    sender_delivery = Column(Boolean, default=False)
    sender_date = Column(DateTime)
    
    # Данные получателя
    receiver_name = Column(String(200))
    receiver_phone = Column(String(50))
    receiver_phone_alt = Column(String(50))
    receiver_city_id = Column(Integer, ForeignKey('cities.id'))
    receiver_branch_id = Column(Integer, ForeignKey('branches.id'))
    receiver_address = Column(Text)
    receiver_delivery = Column(Boolean, default=False)
    receiver_date = Column(DateTime)
    
    # Данные отправления
    weight = Column(Float)
    volume = Column(Float)
    package_id = Column(Integer, ForeignKey('package_types.id'))
    post_type_id = Column(Integer, ForeignKey('post_types.id'))
    piece = Column(Integer, default=1)
    take_photo = Column(Boolean, default=False)
    
    # Данные оплаты
    total_amount = Column(Float, nullable=False)
    ttn = Column(String(100))  # Номер транспортной накладной
    shipping_amount = Column(Float)
    bring_back_money = Column(Boolean, default=False)
    back_money = Column(Float)
    bring_back_waybill = Column(Boolean, default=False)
    
    # Дополнительные данные
    courier = Column(String(100))
    delivery_address = Column(Text)
    delivery_comment = Column(Text)
    tracking_url = Column(Text)
    label_sticker = Column(Text)
    
    # Статусы обработки
    submission_status_bts_id = Column(Integer, ForeignKey('submission_statuses.id'))
    submission_status_crm_id = Column(Integer, ForeignKey('submission_statuses.id'))
    
    # JSON хранилища для исходных данных и ответов API
    raw_data = Column(JSON)
    crm_response = Column(JSON)
    bts_response = Column(JSON)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    contact = relationship("Contact", back_populates="orders")
    branch = relationship("Branch", back_populates="orders", foreign_keys=[branch_id])

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_bts = relationship("SubmissionStatus", foreign_keys=[submission_status_bts_id])
    status_crm = relationship("SubmissionStatus", foreign_keys=[submission_status_crm_id])
    sender_city = relationship("City", foreign_keys=[sender_city_id])
    receiver_city = relationship("City", foreign_keys=[receiver_city_id])
    receiver_branch = relationship("Branch", foreign_keys=[receiver_branch_id])

    payment_method = relationship("PaymentMethod")
    package = relationship("PackageType")
    post_type = relationship("PostType")

class OrderItem(Base):
    """Модель для товаров в заказе."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    code = Column(String(100))
    mxik_goods_id = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Отношения
    order = relationship("Order", back_populates="items")