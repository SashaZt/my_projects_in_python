# app/schemas/resarvation
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    """Base schema for customer information."""

    name: str
    email: Optional[str] = ""
    telephone: Optional[str] = ""
    remarks: Optional[str] = ""

    # Добавляем поля Booking.com
    address: Optional[str] = None
    city: Optional[str] = None
    countryCode: Optional[str] = None
    zip: Optional[str] = None
    ccName: Optional[str] = None
    ccNumber: Optional[str] = None
    ccExpirationDate: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Schema for creating a customer."""

    pass


class CustomerResponse(CustomerBase):
    """Schema for customer response."""

    pass


class RoomReservationBase(BaseModel):
    """Base schema for room reservation information."""

    roomReservationId: str
    roomId: str
    categoryId: int
    arrival: int  # Unix timestamp in milliseconds
    departure: int  # Unix timestamp in milliseconds
    guestName: str
    numberOfGuests: int
    rateId: int
    status: str
    currencyCode: str
    invoice: float
    paid: float
    locked: bool = False
    detailed: bool = False
    addOns: List = Field(default_factory=list)
    guestExtraCharges: List[Dict[str, Any]] = Field(default_factory=list)
    remarks: Optional[str] = None


class RoomReservationCreate(RoomReservationBase):
    """Schema for creating a room reservation."""

    pass


class RoomReservationResponse(RoomReservationBase):
    """Schema for room reservation response."""

    pass


class ReservationBase(BaseModel):
    """Base schema for reservation information."""

    id: str
    organizationId: int
    customer: CustomerBase
    rooms: List[RoomReservationBase]
    status: str
    services: List = Field(default_factory=list)
    bookedAt: int  # Unix timestamp in milliseconds
    modifiedAt: int  # Unix timestamp in milliseconds
    source: str
    responsibleUserId: int


class ReservationCreate(BaseModel):
    """Schema for creating a reservation."""

    id: str
    organizationId: int
    customer: CustomerCreate
    rooms: List[RoomReservationCreate]
    status: str = "ok"
    services: List = Field(default_factory=list)
    bookedAt: Optional[int] = None  # Will be set in the service
    modifiedAt: Optional[int] = None  # Will be set in the service
    source: str
    responsibleUserId: Optional[int] = 1203  # Дефолтное значение если не указано

    class Config:
        extra = "ignore"  # Игнорировать дополнительные поля


class ReservationUpdate(BaseModel):
    """Schema for updating a reservation."""

    customer: Optional[CustomerBase] = None
    rooms: Optional[List[RoomReservationBase]] = None
    status: Optional[str] = None
    services: Optional[List] = None
    modifiedAt: Optional[int] = None  # Will be set in the service
    source: Optional[str] = None
    responsibleUserId: Optional[int] = None


class ReservationResponse(ReservationBase):
    """Schema for reservation response."""

    pass


class ReservationFilter(BaseModel):
    """Schema for filtering reservations."""

    id: Optional[str] = None
    organizationId: Optional[int] = None
    status: Optional[str] = None
    source: Optional[str] = None
    responsibleUserId: Optional[int] = None
    bookedAt_from: Optional[int] = None
    bookedAt_to: Optional[int] = None
    arrival_from: Optional[int] = None
    arrival_to: Optional[int] = None
    departure_from: Optional[int] = None
    departure_to: Optional[int] = None
    customer_name: Optional[str] = None
    status_webhook: bool = False
