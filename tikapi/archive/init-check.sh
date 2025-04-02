#!/bin/bash
set -e

# Проверка, установлена ли переменная POSTGRES_INIT_DB и она равна false
if [ "${POSTGRES_INIT_DB}" = "false" ]; then
    echo "Инициализация базы данных отключена (POSTGRES_INIT_DB=false)"
    
    # Проверяем наличие данных в PGDATA
    if [ -d "$PGDATA" ] && [ -f "$PGDATA/PG_VERSION" ]; then
        echo "База данных уже существует в $PGDATA, инициализация пропускается"
        
        # Удаляем все скрипты инициализации, чтобы они не запускались
        rm -f /docker-entrypoint-initdb.d/*
        
        # Создаем пустой файл-флаг, чтобы PostgreSQL не пытался инициализировать директорию
        touch /docker-entrypoint-initdb.d/.skip-init
    else
        echo "Директория $PGDATA пуста или не содержит базу данных PostgreSQL"
        echo "Инициализация будет выполнена несмотря на POSTGRES_INIT_DB=false"
    fi
else
    echo "Инициализация базы данных включена (POSTGRES_INIT_DB=true или не задана)"
fi