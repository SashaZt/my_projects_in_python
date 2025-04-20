# models/regions.py
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, TIMESTAMP, text

metadata = MetaData()

regions = Table(
    'regions', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(255), nullable=False),
    Column('created_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
)

cities = Table(
    'cities', 
    metadata,
    Column('id', Integer, primary_key=True),
    Column('region_id', Integer, ForeignKey('regions.id'), nullable=False),
    Column('name', String(255), nullable=False),
    Column('created_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP')),
    Column('updated_at', TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
)