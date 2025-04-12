from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class Address(BaseModel):
    """Модель для адреса"""
    city: str
    street: str
    house: str
    apartment: Optional[str] = None
    postal_code: Optional[str] = None
    comment: Optional[str] = None

class Contact(BaseModel):
    """Модель для контактных данных"""
    name: str
    phone: str
    email: Optional[str] = None
    additional_phone: Optional[str] = None

class Item(BaseModel):
    """Модель для товара в заказе"""
    id: str
    name: str
    quantity: int
    price: float
    weight: Optional[float] = None
    dimensions: Optional[Dict[str, float]] = None

class CRMWebhookRequest(BaseModel):
    """Модель данных webhook от CRM"""
    order_id: str
    order_number: str
    created_at: datetime
    customer: Contact
    shipping_address: Address
    items: List[Item]
    total_amount: float
    delivery_type: str
    payment_method: str
    comment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CRMWebhookResponse(BaseModel):
    """Модель ответа для CRM"""
    success: bool
    order_id: str
    message: str
    request_id: Optional[str] = None
    bts_order_id: Optional[str] = None
    delivery_cost: Optional[float] = None
    estimated_delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }