from sqlalchemy import Column, Integer, String, Boolean, Text, Numeric, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base import Base, BaseModel


class Contact(BaseModel):
    """Модель контакта."""
    
    form_id = Column(Integer)
    version = Column(Integer)
    active = Column(Boolean, default=True)
    
    # Дополнительные поля
    con_ugc = Column(Text, nullable=True)
    con_bloger = Column(Text, nullable=True)
    
    # Личные данные
    last_name = Column(String(100))
    first_name = Column(String(100))
    middle_name = Column(String(100), nullable=True)
    company = Column(String(100), nullable=True)
    con_povnaoplata = Column(Text, nullable=True)
    
    # Контрагент
    counterparty_id = Column(Integer, nullable=True)
    
    # Комментарий
    comment = Column(Text, nullable=True)
    
    # Менеджер
    user_id = Column(Integer, ForeignKey("manager.id"), nullable=True)
    manager = relationship("Manager")
    user_name = Column(String(100), nullable=True)
    
    # Время создания
    create_time = Column(DateTime)
    
    # Статистика
    leads_count = Column(Integer, default=0)
    leads_sales_count = Column(Integer, default=0)
    leads_sales_amount = Column(Numeric(10, 2), default=0)
    
    # Телефоны и email
    phones = relationship("ContactPhone", back_populates="contact", cascade="all, delete-orphan")
    emails = relationship("ContactEmail", back_populates="contact", cascade="all, delete-orphan")
    
    # Связь с заказами
    orders = relationship("OrderContact", back_populates="contact")


class ContactPhone(Base):
    """Модель телефонов контакта."""
    
    contact_id = Column(Integer, ForeignKey("contact.id"), primary_key=True)
    contact = relationship("Contact", back_populates="phones")
    
    phone = Column(String(20), primary_key=True)


class ContactEmail(Base):
    """Модель email контакта."""
    
    contact_id = Column(Integer, ForeignKey("contact.id"), primary_key=True)
    contact = relationship("Contact", back_populates="emails")
    
    email = Column(String(100), primary_key=True)


class OrderContact(Base):
    """Связующая таблица для заказов и контактов."""
    
    order_id = Column(Integer, ForeignKey("order.id"), primary_key=True)
    order = relationship("Order", back_populates="contacts")
    
    contact_id = Column(Integer, ForeignKey("contact.id"), primary_key=True)
    contact = relationship("Contact", back_populates="orders")
    
    is_primary = Column(Boolean, default=False)