from sqlalchemy import Column, Integer, String, Boolean, Text, Numeric, Date, DateTime, Time, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.base import Base, BaseModel


# Связка заказов с типами продаж (многие-ко-многим)
order_sales_type = Table(
    "order_sales_type",
    Base.metadata,
    Column("order_id", Integer, ForeignKey("order.id"), primary_key=True),
    Column("sales_type_id", Integer, ForeignKey("tip_prodaju_type.id"), primary_key=True),
)

# Связка заказов с источниками клиентов (многие-ко-многим)
order_client_source = Table(
    "order_client_source",
    Base.metadata,
    Column("order_id", Integer, ForeignKey("order.id"), primary_key=True),
    Column("source_id", Integer, ForeignKey("client_source_type.id"), primary_key=True),
)


class Order(BaseModel):
    """Модель заказа."""
    
    form_id = Column(Integer)
    version = Column(Integer)
    
    # Связь с организацией
    organization_id = Column(Integer, ForeignKey("organization.id"), nullable=True)
    organization = relationship("Organization")
    
    # Методы доставки и оплаты
    shipping_method_id = Column(Integer, ForeignKey("shipping_method.id"), nullable=True)
    shipping_method = relationship("ShippingMethod")
    shipping_method_text = Column(String(100))
    
    payment_method_id = Column(Integer, ForeignKey("payment_method.id"), nullable=True)
    payment_method = relationship("PaymentMethod")
    payment_method_text = Column(String(100))
    
    # Адрес доставки и комментарий
    shipping_address = Column(Text)
    comment = Column(Text)
    
    # Время и информация о приеме заказа
    time_entry_order = Column(Time, nullable=True)
    holder_time = Column(DateTime, nullable=True)
    
    # Типы продаж (многие-ко-многим)
    sales_types = relationship("TipProdajuType", secondary=order_sales_type)
    
    # Информация о скидке
    discount_amount = Column(Numeric(10, 2), nullable=True)
    
    # Даты и время
    order_time = Column(DateTime)
    update_at = Column(DateTime)
    
    # Статус заказа
    status_id = Column(Integer, ForeignKey("order_status.id"))
    status = relationship("OrderStatus")
    status_text = Column(String(100))
    
    # Дата и причина оплаты/отмены
    payment_date = Column(Date, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Менеджер
    user_id = Column(Integer, ForeignKey("manager.id"), nullable=True)
    manager = relationship("Manager")
    user_name = Column(String(100))
    
    # Финансовая информация
    payment_amount = Column(Numeric(10, 2), nullable=True)
    commission_amount = Column(Numeric(10, 2), nullable=True)
    cost_price_amount = Column(Numeric(10, 2), nullable=True)
    shipping_costs = Column(Numeric(10, 2), nullable=True)
    expenses_amount = Column(Numeric(10, 2), nullable=True)
    profit_amount = Column(Numeric(10, 2), nullable=True)
    
    # Тип заказа
    type_id = Column(Integer, ForeignKey("order_type.id"))
    order_type = relationship("OrderType")
    type_text = Column(String(100))
    
    # Информация о платеже
    payed_amount = Column(Numeric(10, 2), nullable=True)
    rest_pay = Column(Numeric(10, 2), nullable=True)
    
    # Дополнительная информация
    call = Column(Boolean, nullable=True)
    sajt = Column(String(100), nullable=True)
    external_id = Column(String(50), nullable=True)
    
    # UTM-метки
    utm_page = Column(Text, nullable=True)
    utm_medium = Column(String(100), nullable=True)
    
    # Кампания
    campaign_id = Column(Integer, ForeignKey("campaign.id"), nullable=True)
    campaign = relationship("Campaign")
    campaign_name = Column(String(100), nullable=True)
    
    # Другие UTM-метки
    utm_source_full = Column(Text, nullable=True)
    utm_source = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)
    utm_term = Column(String(100), nullable=True)
    
    # Источники от клиентов (многие-ко-многим)
    client_sources = relationship("ClientSourceType", secondary=order_client_source)
    
    # Связь с контактами
    contacts = relationship("OrderContact", back_populates="order")
    
    # Связь с данными доставки
    delivery_data = relationship("DeliveryData", back_populates="order")
    
    # Связь с товарами в заказе
    products = relationship("OrderProduct", back_populates="order")
    
    # Связь с данными Новой Почты
    novaposhta_data = relationship("NovaPoshtaData", back_populates="order", uselist=False)
    
    # Связь с чеками
    checks = relationship("OrderCheck", back_populates="order")


class DeliveryData(BaseModel):
    """Модель данных доставки."""
    
    order_id = Column(Integer, ForeignKey("order.id"))
    order = relationship("Order", back_populates="delivery_data")
    
    provider = Column(String(50))
    sender_id = Column(Integer)
    type = Column(String(50), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    city_name = Column(String(100), nullable=True)
    status_code = Column(String(50), nullable=True)
    delivery_date_and_time = Column(DateTime, nullable=True)
    back_delivery = Column(Boolean, default=False)
    pay_for_delivery = Column(Numeric(10, 2), nullable=True)


class NovaPoshtaData(BaseModel):
    """Модель данных Новой Почты."""
    
    order_id = Column(Integer, ForeignKey("order.id"))
    order = relationship("Order", back_populates="novaposhta_data")
    
    id_entity = Column(Integer)
    city_name = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    branch_number = Column(Integer, nullable=True)
    warehouse_type_id = Column(Integer, nullable=True)
    back_delivery_sum = Column(Numeric(10, 2), nullable=True)
    manual = Column(Boolean, default=False)


class OrderCheck(BaseModel):
    """Модель чека."""
    
    order_id = Column(Integer, ForeignKey("order.id"))
    order = relationship("Order", back_populates="checks")
    
    fiscal_code = Column(String(50))
    fiscal_id = Column(String(50))
    fiscalization_status = Column(String(50))
    receipt_id = Column(String(100))