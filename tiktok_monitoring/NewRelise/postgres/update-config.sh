#!/bin/bash
set -e

# Этот скрипт можно запускать вручную для обновления конфигурации уже существующей базы данных

echo "Обновление конфигурации PostgreSQL для существующей базы данных"

# Проверяем, что PostgreSQL запущен
if ! pg_isready -q; then
    echo "PostgreSQL не запущен. Запустите контейнер перед выполнением этого скрипта."
    exit 1
fi

# Обновляем postgresql.conf
psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} -c "
ALTER SYSTEM SET listen_addresses = '*';
ALTER SYSTEM SET max_connections = ${PG_MAX_CONNECTIONS:-200};
ALTER SYSTEM SET shared_buffers = '${PG_SHARED_BUFFERS:-512MB}';
ALTER SYSTEM SET effective_cache_size = '${PG_EFFECTIVE_CACHE_SIZE:-1536MB}';
ALTER SYSTEM SET maintenance_work_mem = '${PG_MAINTENANCE_WORK_MEM:-128MB}';
ALTER SYSTEM SET checkpoint_completion_target = ${PG_CHECKPOINT_COMPLETION_TARGET:-0.9};
ALTER SYSTEM SET wal_buffers = '${PG_WAL_BUFFERS:-16MB}';
ALTER SYSTEM SET default_statistics_target = ${PG_DEFAULT_STATISTICS_TARGET:-100};
ALTER SYSTEM SET random_page_cost = ${PG_RANDOM_PAGE_COST:-1.1};
ALTER SYSTEM SET effective_io_concurrency = ${PG_EFFECTIVE_IO_CONCURRENCY:-200};
ALTER SYSTEM SET work_mem = '${PG_WORK_MEM:-6553kB}';
ALTER SYSTEM SET min_wal_size = '${PG_MIN_WAL_SIZE:-1GB}';
ALTER SYSTEM SET max_wal_size = '${PG_MAX_WAL_SIZE:-4GB}';
"

# Добавляем правила доступа в pg_hba.conf
# Копируем текущий pg_hba.conf
cat > /tmp/pg_hba.conf <<EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
# Разрешаем подключения по локальному сокету
local   all             all                                     trust
# Разрешаем подключения с локального хоста
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
# Разрешаем подключения из сети Docker
host    all             all             10.0.0.0/8              md5
# Разрешаем подключения из всех сетей (для разработки)
host    all             all             all                     md5
EOF

# Получаем путь к pg_hba.conf
PG_HBA_PATH=$(psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} -t -c "SHOW hba_file;")
PG_HBA_PATH=$(echo $PG_HBA_PATH | xargs)  # Удаляем пробелы

echo "Обновление файла $PG_HBA_PATH"
cat /tmp/pg_hba.conf > "$PG_HBA_PATH"

# Перезагружаем конфигурацию
psql -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} -c "SELECT pg_reload_conf();"

echo "Конфигурация PostgreSQL успешно обновлена"