from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import db_config, use_bd, use_table

DATABASE_URL = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ColdCall(Base):
    __tablename__ = "cold_calls"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date_of_creation = Column(Date, index=True)
    nomer = Column(String(10), index=True)
    status = Column(String(1000))
    date_of_status_change = Column(Date)
