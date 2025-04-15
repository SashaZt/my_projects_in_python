# models/branches.py
from sqlalchemy import Table, Column, Integer, String, Text, MetaData, ForeignKey, TIMESTAMP, text

metadata = MetaData()

branches = Table(
    'branches', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('branche_id', String(100), nullable=False, unique=True),
    Column('branche_name', String(255), nullable=False),
    Column('address', Text, nullable=False),
    Column('region_id', Integer, nullable=False),
    Column('city_id', Integer, nullable=False),
    Column('created_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
)