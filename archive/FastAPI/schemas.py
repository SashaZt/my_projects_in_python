from pydantic import BaseModel
import datetime

class ColdCallCreate(BaseModel):
    nomer: str
    status: str

class ColdCallModel(ColdCallCreate):
    id: int
    date_of_creation: datetime.date
    date_of_status_change: datetime.date

    class Config:
        from_attributes = True
