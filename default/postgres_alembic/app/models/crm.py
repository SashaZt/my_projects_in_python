# app/models/crm
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, JSON
from datetime import datetime

Base = declarative_base()


# Расширенная модель контакта с абсолютно всеми полями
class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    form_id = Column(Integer)
    version = Column(Integer)
    active = Column(Boolean)

    # Все возможные поля из исходных данных
    con_ugc = Column(String, nullable=True)
    con_bloger = Column(String, nullable=True)

    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)

    phones = Column(ARRAY(String), nullable=True)
    emails = Column(ARRAY(String), nullable=True)
    telegram = Column(String, nullable=True)
    instagram_nick = Column(String, nullable=True)

    counterparty_id = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)
    create_time = Column(DateTime, nullable=True)

    leads_count = Column(Integer, nullable=True)
    leads_sales_count = Column(Integer, nullable=True)
    leads_sales_amount = Column(Float, nullable=True)

    company = Column(String, nullable=True)
    con_povna_oplata = Column(String, nullable=True)

    # Связи
    orders = relationship("Order", back_populates="customer")


# Расширенная модель продукта
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)

    # Все поля из исходных данных о продукте
    product_id = Column(Integer)
    sku = Column(String, nullable=True)
    barcode = Column(String, nullable=True)
    name = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    manufacturer = Column(String, nullable=True)

    # Дополнительные атрибуты
    parameter = Column(String, nullable=True)
    document_name = Column(String, nullable=True)
    uktzed = Column(String, nullable=True)

    # Связи
    order_items = relationship("OrderItem", back_populates="product")


# Модель позиции заказа с полными деталями
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))

    # Все возможные поля из исходных данных
    amount = Column(Integer)
    price = Column(Float, nullable=True)
    cost_price = Column(Float, nullable=True)

    percent_commission = Column(Float, nullable=True)
    pre_sale = Column(Integer, nullable=True)
    stock_id = Column(Integer, nullable=True)

    discount = Column(Float, nullable=True)
    commission = Column(Float, nullable=True)
    percent_discount = Column(Float, nullable=True)

    # Связи
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# Расширенная модель заказа со всеми возможными метками и атрибутами
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    form_id = Column(Integer)
    version = Column(Integer)

    # Связи
    customer_id = Column(Integer, ForeignKey("contacts.id"))
    customer = relationship("Contact", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

    # Временные метки и статусы
    order_time = Column(DateTime)
    update_time = Column(DateTime)
    payment_date = Column(DateTime, nullable=True)
    time_entry_order = Column(DateTime, nullable=True)
    holder_time = Column(DateTime, nullable=True)

    # Финансовые показатели
    total_amount = Column(Float, nullable=True)
    discount_amount = Column(Float, nullable=True)
    payment_amount = Column(Float, nullable=True)
    commission_amount = Column(Float, nullable=True)
    cost_price_amount = Column(Float, nullable=True)
    shipping_costs = Column(Float, nullable=True)
    expenses_amount = Column(Float, nullable=True)
    profit_amount = Column(Float, nullable=True)

    # Статусы и методы
    status_id = Column(Integer)
    shipping_method = Column(Integer)
    payment_method = Column(Integer)
    type_id = Column(Integer, nullable=True)

    # Платежные детали
    payed_amount = Column(Float, nullable=True)
    rest_pay = Column(Float, nullable=True)

    # Организационные детали
    organization_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)

    # Метки и дополнительные атрибуты
    shipping_address = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    rejection_reason = Column(String, nullable=True)

    # UTM и маркетинговые метки
    external_id = Column(String, nullable=True)
    utm_page = Column(String, nullable=True)
    utm_medium = Column(String, nullable=True)
    campaign_id = Column(Integer, nullable=True)
    utm_source_full = Column(String, nullable=True)
    utm_source = Column(String, nullable=True)
    utm_campaign = Column(String, nullable=True)
    utm_content = Column(String, nullable=True)
    utm_term = Column(String, nullable=True)

    # Дополнительные массивы
    tip_prodazu = Column(ARRAY(Integer), nullable=True)
    dzerelo_komentar_vid_kliienta = Column(ARRAY(Integer), nullable=True)

    # Прочие метки
    call = Column(String, nullable=True)
    sajt = Column(String, nullable=True)
    document_ord_check = Column(Integer, nullable=True)


# Модель доставки с максимально полной информацией
class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)

    # Полные детали доставки
    sender_id = Column(Integer, nullable=True)
    back_delivery = Column(Integer, nullable=True)
    city_name = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    pay_for_delivery = Column(String, nullable=True)
    delivery_type = Column(String, nullable=True)
    tracking_number = Column(String, nullable=True)
    status_code = Column(Integer, nullable=True)
    delivery_date = Column(DateTime, nullable=True)

    branch_number = Column(Integer, nullable=True)
    address = Column(String, nullable=True)

    # Связь с заказом
    order = relationship("Order", backref="delivery")
