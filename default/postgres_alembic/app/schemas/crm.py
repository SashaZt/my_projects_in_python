# app/schemas/crm.py
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from datetime import datetime


class ContactBase(BaseModel):
    """Базовая схема для контакта"""

    form_id: Optional[int] = None
    version: Optional[int] = None
    active: Optional[bool] = None

    con_ugc: Optional[str] = None
    con_bloger: Optional[str] = None

    last_name: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None

    phones: Optional[List[str]] = None
    emails: Optional[List[str]] = None
    telegram: Optional[str] = None
    instagram_nick: Optional[str] = None

    counterparty_id: Optional[int] = None
    comment: Optional[str] = None
    user_id: Optional[int] = None
    create_time: Optional[datetime] = None

    leads_count: Optional[int] = None
    leads_sales_count: Optional[int] = None
    leads_sales_amount: Optional[float] = None

    company: Optional[str] = None
    con_povna_oplata: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContactCreate(ContactBase):
    """Схема для создания контакта"""

    pass


class ContactUpdate(ContactBase):
    """Схема для обновления контакта"""

    pass


class ContactInDB(ContactBase):
    """Схема контакта с ID"""

    id: int


class ProductBase(BaseModel):
    """Базовая схема для продукта"""

    product_id: int
    sku: Optional[str] = None
    barcode: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None

    parameter: Optional[str] = None
    document_name: Optional[str] = None
    uktzed: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(ProductBase):
    """Схема для создания продукта"""

    pass


class ProductUpdate(ProductBase):
    """Схема для обновления продукта"""

    pass


class ProductInDB(ProductBase):
    """Схема продукта с ID"""

    id: int


class OrderItemBase(BaseModel):
    """Базовая схема для позиции заказа"""

    order_id: int
    product_id: int

    amount: int
    price: Optional[float] = None
    cost_price: Optional[float] = None

    percent_commission: Optional[float] = None
    pre_sale: Optional[int] = None
    stock_id: Optional[int] = None

    discount: Optional[float] = None
    commission: Optional[float] = None
    percent_discount: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class OrderItemCreate(OrderItemBase):
    """Схема для создания позиции заказа"""

    pass


class OrderItemUpdate(OrderItemBase):
    """Схема для обновления позиции заказа"""

    pass


class OrderItemInDB(OrderItemBase):
    """Схема позиции заказа с ID"""

    id: int


class OrderBase(BaseModel):
    """Базовая схема для заказа"""

    form_id: int
    version: int

    customer_id: Optional[int] = None

    # Временные метки
    order_time: datetime
    update_time: datetime
    payment_date: Optional[datetime] = None
    time_entry_order: Optional[datetime] = None
    holder_time: Optional[datetime] = None

    # Финансовые показатели
    total_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    payment_amount: Optional[float] = None
    commission_amount: Optional[float] = None
    cost_price_amount: Optional[float] = None
    shipping_costs: Optional[float] = None
    expenses_amount: Optional[float] = None
    profit_amount: Optional[float] = None

    # Статусы
    status_id: int
    shipping_method: int
    payment_method: int
    type_id: Optional[int] = None

    # Платежные детали
    payed_amount: Optional[float] = None
    rest_pay: Optional[float] = None

    # Организационные детали
    organization_id: Optional[int] = None
    user_id: Optional[int] = None

    # Дополнительные атрибуты
    shipping_address: Optional[str] = None
    comment: Optional[str] = None
    rejection_reason: Optional[str] = None

    # UTM-метки
    external_id: Optional[str] = None
    utm_page: Optional[str] = None
    utm_medium: Optional[str] = None
    campaign_id: Optional[int] = None
    utm_source_full: Optional[str] = None
    utm_source: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None

    # Дополнительные массивы
    tip_prodazu: Optional[List[int]] = None
    dzerelo_komentar_vid_kliienta: Optional[List[int]] = None

    # Прочие метки
    call: Optional[str] = None
    sajt: Optional[str] = None
    document_ord_check: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(OrderBase):
    """Схема для создания заказа"""

    # Можно добавить специфические валидации
    items: Optional[List[OrderItemCreate]] = None


class OrderUpdate(OrderBase):
    """Схема для обновления заказа"""

    pass


class OrderInDB(OrderBase):
    """Схема заказа с ID"""

    id: int

    # Связанные сущности
    customer: Optional[ContactInDB] = None
    items: Optional[List[OrderItemInDB]] = None


class DeliveryBase(BaseModel):
    """Базовая схема для доставки"""

    order_id: int

    sender_id: Optional[int] = None
    back_delivery: Optional[int] = None
    city_name: Optional[str] = None
    provider: Optional[str] = None
    pay_for_delivery: Optional[str] = None
    delivery_type: Optional[str] = None
    tracking_number: Optional[str] = None
    status_code: Optional[int] = None
    delivery_date: Optional[datetime] = None

    branch_number: Optional[int] = None
    address: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeliveryCreate(DeliveryBase):
    """Схема для создания доставки"""

    pass


class DeliveryUpdate(DeliveryBase):
    """Схема для обновления доставки"""

    pass


class DeliveryInDB(DeliveryBase):
    """Схема доставки с ID"""

    id: int
    order: Optional[OrderInDB] = None
