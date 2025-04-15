# models/orders.py
from sqlalchemy import Table, Column, Integer, String, Float, Boolean, Text, MetaData, ForeignKey, TIMESTAMP, text, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

orders = Table(
    'orders', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('id_order_crm', String(100), nullable=False),
    
    # Данные отправителя
    Column('sender_city_id', Integer, nullable=False),
    Column('sender_address', Text, nullable=False),
    Column('sender_real', String(200), nullable=False),
    Column('sender_phone', String(100), nullable=False),
    Column('sender_delivery', Integer, default=0),
    
    # Данные отправления
    Column('weight', DECIMAL(8, 3), nullable=False),
    Column('package_id', Integer, nullable=False),
    Column('post_type_id', Integer, nullable=False),
    Column('piece', Integer, default=1),
    
    # Данные получателя
    Column('receiver', String(200), nullable=False),
    Column('receiver_address', Text, nullable=False),
    Column('receiver_city_id', Integer, nullable=False),
    Column('receiver_phone', String(100), nullable=False),
    Column('receiver_delivery', Integer, default=0),
    Column('receiver_branch_id', Integer, nullable=True),
    
    # Данные оплаты
    Column('bring_back_money', Integer, default=0),
    Column('back_money', DECIMAL(12, 2), nullable=True),
    
    # Служебные данные
    Column('is_test', Integer, default=0),
    Column('ttn', String(100), nullable=True),
    Column('shipping_amount', DECIMAL(12, 2), nullable=True),
    Column('submission_status_bts', String(50), nullable=True),
    Column('submission_status_crm', String(50), nullable=True),
    
    # Исходные данные и время
    Column('raw_data', JSONB, nullable=True),
    Column('bts_response', JSONB, nullable=True),
    Column('crm_response', JSONB, nullable=True),
    Column('created_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
)

order_items = Table(
    'order_items',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('order_id', Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
    Column('name', String(255), nullable=False),
    Column('quantity', Integer, nullable=False),
    Column('price', DECIMAL(12, 2), nullable=False),
    Column('sku', String(100), nullable=True),  # Добавленное поле для SKU

    Column('created_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
)