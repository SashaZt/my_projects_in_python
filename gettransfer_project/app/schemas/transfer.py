# app/schemas/transfer.py
from datetime import date, time
from typing import Optional
from pydantic import BaseModel


class TransferBase(BaseModel):
    created_at_date: date
    created_at_time: time
    transfer_id: str
    date_to_local: Optional[date] = None
    time_to_local: Optional[time] = None
    type: Optional[str] = None
    distance: Optional[float] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    pax: Optional[int] = None
    transport_type_ids: Optional[str] = None
    carrier_offer_price: Optional[float] = None


class TransferCreate(TransferBase):
    # Здесь можно добавить дополнительные проверки или обязательные поля для создания
    pass


class Transfer(TransferBase):
    id: int

    class Config:
        from_attributes = True

#Для фильтрации по ключевых слов
class TransportOption(BaseModel):
    name: str
    passengers: str
    luggage: str
    price: float


class Direction(BaseModel):
    name: str
    transport_options: List[TransportOption]


class TransferStats(BaseModel):
    pax_distribution: Dict[int, int]


class AutoSuggestionResponse(BaseModel):
    directions: List[Direction]
    notes: List[str]
    available_transfers: int
    transfer_stats: Optional[TransferStats] = None