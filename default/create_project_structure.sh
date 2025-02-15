#!/bin/bash
# Скрипт для создания структуры проекта

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
BASE_DIR="gettransfer_project"

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

# Создаём структуру директорий для приложения (app)
mkdir -p "$BASE_DIR/app/models"
mkdir -p "$BASE_DIR/app/schemas"
mkdir -p "$BASE_DIR/app/crud"
mkdir -p "$BASE_DIR/app/api/endpoints"

# Создаём пустые файлы в каталоге app
create_file "$BASE_DIR/app/__init__.py"
create_file "$BASE_DIR/app/main.py"           # Точка входа FastAPI-приложения
create_file "$BASE_DIR/app/models/transfer.py"  # SQLAlchemy-модель
create_file "$BASE_DIR/app/schemas/transfer.py" # Pydantic-схема
create_file "$BASE_DIR/app/crud/transfer.py"    # CRUD-операции
create_file "$BASE_DIR/app/api/endpoints/transfer.py"  # Эндпоинт

# Создаём структуру для Alembic
mkdir -p "$BASE_DIR/alembic/versions"
create_file "$BASE_DIR/alembic/env.py"         # Конфигурация Alembic
create_file "$BASE_DIR/alembic/script.py.mako"   # Шаблон скрипта миграции

# Создаём корневые файлы проекта
create_file "$BASE_DIR/alembic.ini"             # Основной конфигурационный файл Alembic
create_file "$BASE_DIR/Dockerfile"              # Dockerfile для сборки образа приложения
create_file "$BASE_DIR/docker-compose.yml"      # Файл docker-compose для стека (FastAPI + PostgreSQL)
create_file "$BASE_DIR/requirements.txt"        # Файл с зависимостями Python

echo "Структура проекта успешно создана в директории: $BASE_DIR"
