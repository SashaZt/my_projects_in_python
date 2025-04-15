# models/order_items.py
from sqlalchemy import Table, Column, Integer, String, Float, ForeignKey, TIMESTAMP, text, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import MetaData

metadata = MetaData()

order_items = Table(
    'order_items', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('order_id', Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
    Column('name', String(255), nullable=False),
    Column('quantity', Integer, nullable=False),
    Column('price', DECIMAL(12, 2), nullable=False),
    Column('created_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
)