#!/bin/bash
# 
# Этот скрипт запускает контейнеры Docker для проекта.
# Для правильной настройки прав доступа к директории данных PostgreSQL
# может потребоваться выполнение команд с правами суперпользователя (sudo).
#

# Проверка наличия config.json
if [ ! -f "config.json" ]; then
    echo "Ошибка: файл config.json не найден!"
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

# Загружаем переменные окружения из сгенерированного .env файла
source .env
PG_DATA_DIR=${POSTGRES_DATA_DIR:-./pgdata}

# Проверка наличия директории для инициализационных скриптов PostgreSQL
if [ ! -d "postgres/init-scripts" ]; then
    echo "Создание директории для инициализационных скриптов PostgreSQL..."
    mkdir -p postgres/init-scripts
fi

# Проверка наличия основных скриптов инициализации
if [ ! -f "postgres/init-scripts/01-config-update.sh" ]; then
    echo "Ошибка: файл postgres/init-scripts/01-config-update.sh не найден!"
    exit 1
fi

if [ ! -f "postgres/init-scripts/02-init.sql" ]; then
    echo "Ошибка: файл postgres/init-scripts/02-init.sql не найден!"
    exit 1
fi

if [ ! -f "postgres/init-scripts/03-schema.sql" ]; then
    echo "Ошибка: файл postgres/init-scripts/03-schema.sql не найден!"
    exit 1
fi

# Проверяем наличие директории данных
if [ ! -d "$PG_DATA_DIR" ]; then
    echo "Создание директории для данных PostgreSQL: $PG_DATA_DIR"
    mkdir -p "$PG_DATA_DIR"
    
    # Устанавливаем правильные права доступа для пользователя postgres (UID 999)
    echo "Установка прав доступа для директории данных PostgreSQL..."
    sudo chown -R 999:999 "$PG_DATA_DIR"
else
    echo "Директория для данных PostgreSQL уже существует: $PG_DATA_DIR"
    
    # Проверяем права доступа и исправляем их при необходимости
    if [ "$(stat -c '%u:%g' "$PG_DATA_DIR")" != "999:999" ]; then
        echo "Исправление прав доступа для директории данных PostgreSQL..."
        sudo chown -R 999:999 "$PG_DATA_DIR"
    fi
    
    # Проверяем, есть ли там уже данные PostgreSQL
    if [ -f "$PG_DATA_DIR/PG_VERSION" ]; then
        echo "Обнаружена существующая база данных PostgreSQL"
        echo "Установка POSTGRES_INIT_DB=false для предотвращения повторной инициализации"
        sed -i 's/POSTGRES_INIT_DB=true/POSTGRES_INIT_DB=false/' .env
    fi
fi

# Создание необходимых директорий
mkdir -p logs

# Экспортируем текущий UID и GID для использования в контейнере
export USER_ID=$(id -u)
export GROUP_ID=$(id -g)

# Ключ для запуска только PostgreSQL
if [ "$1" == "postgres" ]; then
    echo "Запуск только контейнера PostgreSQL..."
    docker-compose up -d postgres
    echo "PostgreSQL запущен. Для проверки статуса используйте 'docker-compose ps'"
    exit 0
fi

# # Ключ для запуска только API
# if [ "$1" == "api" ]; then
#     echo "Запуск только контейнера API..."
#     docker-compose up -d api
#     echo "API запущен. Для проверки статуса используйте 'docker-compose ps'"
#     exit 0
# fi

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