#app/core/base.py
from sqlalchemy.ext.declarative import declarative_base

# Создаём базовый класс для моделей SQLAlchemy.
# Все модели в приложении будут наследоваться от этого класса.
Base = declarative_base()
