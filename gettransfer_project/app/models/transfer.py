# app/models/transfer.py
from sqlalchemy import Column, Date, Time, String, Integer, Float
from app.database import (
    Base,
)  # предположим, что Base импортируется от declarative_base()


class Transfer(Base):
    __tablename__ = "transfers"

    id = Column(Integer, primary_key=True, index=True)
    created_at_date = Column(Date, nullable=False)
    created_at_time = Column(Time, nullable=False)
    transfer_id = Column(String, unique=True, index=True, nullable=False)
    date_to_local = Column(Date, nullable=True)
    time_to_local = Column(Time, nullable=True)
    type = Column(String, nullable=True)
    distance = Column(Float, nullable=True)
    from_location = Column(String, nullable=True)
    to_location = Column(String, nullable=True)
    pax = Column(Integer, nullable=True)
    transport_type_ids = Column(String, nullable=True)
    carrier_offer_price = Column(Float, nullable=True)
