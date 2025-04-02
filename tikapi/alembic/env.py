# alembic/env.py
import os
import sys
import json
from logging.config import fileConfig
from api.models import Base
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Добавляем директорию проекта в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Импорт моделей SQLAlchemy (нужно будет создать)
# from api.models import Base  # Импортируйте вашу базовую модель SQLAlchemy

# этот раздел конфигурации объекта Alembic
# надо ли это в файле alembic.ini

config = context.config


# Загрузка конфигурации из config.json
def load_config_from_json():
    try:
        with open('config.json', 'r') as file:
            config_data = json.load(file)
            
            # Получаем параметры подключения из config.json
            db_user = config_data.get('postgres', {}).get('user', 'tiktok_user')
            db_password = config_data.get('postgres', {}).get('password', 'your_secure_password')
            db_name = config_data.get('postgres', {}).get('db', 'tiktok_analytics')
            
            # Используем localhost вместо postgres для локального запуска
            db_host = 'localhost'  # Изменено с config_data.get('postgres', {}).get('host', 'postgres')
            db_port = config_data.get('postgres', {}).get('port', 5432)
            
            # Формируем URL для SQLAlchemy
            sqlalchemy_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            return sqlalchemy_url
    except Exception as e:
        print(f"Ошибка при загрузке config.json: {e}")
        return None

# Установка URL подключения
sqlalchemy_url = load_config_from_json()
if sqlalchemy_url:
    config.set_main_option("sqlalchemy.url", sqlalchemy_url)
else:
    print("Не удалось загрузить URL подключения из config.json")
    # Можно также загрузить URL из переменных окружения, если он там есть
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        config.set_main_option("sqlalchemy.url", database_url)

# интерпретируйте конфигурационный файл alembic.ini для Python logging.
fileConfig(config.config_file_name)

target_metadata = Base.metadata

# другие значения из конфигурации, определенные пользователем, передаются в 
# call to context.configure()
def run_migrations_offline():
    """Выполнение миграций в режиме 'оффлайн'."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Выполнение миграций в режиме 'онлайн'."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()