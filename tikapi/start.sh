#!/bin/bash

# Проверка наличия config.json
if [ ! -f "config.json" ]; then
    echo "Ошибка: файл config.json не найден!"
    exit 1
fi

# Проверка наличия директории для инициализационных скриптов PostgreSQL
if [ ! -d "postgres/init-scripts" ]; then
    echo "Создание директории для инициализационных скриптов PostgreSQL..."
    mkdir -p postgres/init-scripts
    
    # Если скрипта нет, создаем базовый
    if [ ! -f "postgres/init-scripts/01-init.sql" ]; then
        echo "Создание базового инициализационного скрипта..."
        echo '-- Базовая инициализация PostgreSQL' > postgres/init-scripts/01-init.sql
    fi
fi

# Создание скрипта проверки инициализации
if [ ! -f "postgres/init-check.sh" ]; then
    echo "Ошибка: файл postgres/init-check.sh не найден!"
    echo "Создайте этот файл по инструкции или скопируйте из документации."
    exit 1
fi

# Генерация .env файла из config.json
echo "Генерация переменных окружения из config.json..."
python3 config_loader.py config.json .env

# Проверка результата
if [ $? -ne 0 ]; then
    echo "Ошибка при генерации .env файла!"
    exit 1
fi

# Проверка и создание директории для данных PostgreSQL
source .env
PG_DATA_DIR=${POSTGRES_DATA_DIR:-./pgdata}

# Проверяем наличие директории данных
if [ ! -d "$PG_DATA_DIR" ]; then
    echo "Создание директории для данных PostgreSQL: $PG_DATA_DIR"
    mkdir -p "$PG_DATA_DIR"
else
    echo "Директория для данных PostgreSQL уже существует: $PG_DATA_DIR"
    
    # Проверяем, есть ли там уже данные PostgreSQL
    if [ -f "$PG_DATA_DIR/PG_VERSION" ]; then
        echo "Обнаружена существующая база данных PostgreSQL"
        echo "Установка POSTGRES_INIT_DB=false для предотвращения повторной инициализации"
        sed -i 's/POSTGRES_INIT_DB=true/POSTGRES_INIT_DB=false/' .env
    fi
fi

# Создание необходимых директорий
mkdir -p logs

# Ключ для запуска только PostgreSQL
if [ "$1" == "postgres" ]; then
    echo "Запуск только контейнера PostgreSQL..."
    docker-compose up -d postgres
    echo "PostgreSQL запущен. Для проверки статуса используйте 'docker-compose ps'"
    exit 0
fi

# Ключ для запуска только API
if [ "$1" == "api" ]; then
    echo "Запуск только контейнера API..."
    docker-compose up -d api
    echo "API запущен. Для проверки статуса используйте 'docker-compose ps'"
    exit 0
fi

# Запуск всех контейнеров
echo "Запуск контейнеров..."

# В режиме разработки добавляем флаг build для пересборки образов
if grep -q '"environment": *"development"' config.json; then
    docker-compose up -d --build
else
    docker-compose up -d
fi

# Проверка статуса контейнеров
echo "Проверка статуса контейнеров..."
docker-compose ps

echo "Система запущена! Для просмотра логов используйте 'docker-compose logs -f'"