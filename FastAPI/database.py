from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import db_config, use_bd, use_table
DATABASE_URL = f"mysql+mysqlconnector://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
