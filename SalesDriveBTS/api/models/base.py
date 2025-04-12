# api/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime,BigInteger
from datetime import datetime
import pytz
import time

Base = declarative_base()

class BaseModel:
    id = Column(Integer, primary_key=True)
    created_at = Column(BigInteger, default=lambda: int(time.time()))
    updated_at = Column(BigInteger, default=lambda: int(time.time()), onupdate=lambda: int(time.time()))