#!/bin/bash
# Скрипт для создания структуры проекта для работы с PostgreSQL

# Определяем тип ОС
OS_TYPE="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  OS_TYPE="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
  OS_TYPE="Mac"
elif [[ "$OSTYPE" == "cygwin" ]]; then
  OS_TYPE="Cygwin (Windows)"
elif [[ "$OSTYPE" == "msys" ]]; then
  OS_TYPE="Windows (MSYS)"
elif [[ "$OSTYPE" == "win32" ]]; then
  OS_TYPE="Windows"
else
  OS_TYPE="unknown"
fi

echo "Detected OS: $OS_TYPE"

# Базовая директория проекта
BASE_DIR="postgres_import_project"

# Функция для создания файла (если файл не существует)
create_file() {
  if [ ! -f "$1" ]; then
    touch "$1"
    echo "Создан файл: $1"
  else
    echo "Файл уже существует: $1"
  fi
}

# Создаём базовую директорию
mkdir -p "$BASE_DIR"

# Создаём структуру директорий для приложения
mkdir -p "$BASE_DIR/app/db"
mkdir -p "$BASE_DIR/app/models"
mkdir -p "$BASE_DIR/app/schemas"
mkdir -p "$BASE_DIR/app/services"
mkdir -p "$BASE_DIR/alembic/versions"

# Создаём пустые файлы в каталоге app
create_file "$BASE_DIR/app/__init__.py"
create_file "$BASE_DIR/app/config.py"           # Конфигурация подключения к БД

# Создаём файлы в каталоге db
create_file "$BASE_DIR/app/db/__init__.py"
create_file "$BASE_DIR/app/db/base.py"          # Базовые классы SQLAlchemy
create_file "$BASE_DIR/app/db/session.py"       # Настройка сессии
create_file "$BASE_DIR/app/db/engine.py"        # Настройка движка БД

# Создаём файлы в каталоге models
create_file "$BASE_DIR/app/models/__init__.py"
create_file "$BASE_DIR/app/models/contacts.py"  # Модели для контактов
create_file "$BASE_DIR/app/models/orders.py"    # Модели для заказов
create_file "$BASE_DIR/app/models/products.py"  # Модели для продуктов
create_file "$BASE_DIR/app/models/enums.py"     # Перечисления и справочники

# Создаём файлы в каталоге schemas
create_file "$BASE_DIR/app/schemas/__init__.py"
create_file "$BASE_DIR/app/schemas/json_schema.py"  # Pydantic-модели для JSON

# Создаём файлы в каталоге services
create_file "$BASE_DIR/app/services/__init__.py"
create_file "$BASE_DIR/app/services/import_service.py"  # Логика импорта данных

# Создаём структуру для Alembic
create_file "$BASE_DIR/alembic/env.py"          # Конфигурация Alembic
create_file "$BASE_DIR/alembic/script.py.mako"  # Шаблон скрипта миграции

# Создаём корневые файлы проекта
create_file "$BASE_DIR/alembic.ini"             # Основной конфигурационный файл Alembic
create_file "$BASE_DIR/main.py"                 # Точка входа приложения
create_file "$BASE_DIR/requirements.txt"        # Файл с зависимостями Python
create_file "$BASE_DIR/README.md"               # Документация проекта

# Записываем основные зависимости в requirements.txt
cat > "$BASE_DIR/requirements.txt" << EOF
sqlalchemy>=2.0.0
asyncpg>=0.27.0
pydantic>=2.0.0
alembic>=1.10.0
python-dotenv>=1.0.0
EOF

echo "Структура проекта успешно создана в директории: $BASE_DIR"