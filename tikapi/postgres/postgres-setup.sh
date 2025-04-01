#!/bin/bash
set -e

# Этот скрипт запускается при старте контейнера

# Применяем настройки конфигурации PostgreSQL
cat > "$PGDATA/postgresql.conf" <<EOF
# Основные настройки
listen_addresses = '*'
max_connections = ${PG_MAX_CONNECTIONS:-200}
shared_buffers = ${PG_SHARED_BUFFERS:-512MB}
effective_cache_size = ${PG_EFFECTIVE_CACHE_SIZE:-1536MB}
maintenance_work_mem = ${PG_MAINTENANCE_WORK_MEM:-128MB}
checkpoint_completion_target = ${PG_CHECKPOINT_COMPLETION_TARGET:-0.9}
wal_buffers = ${PG_WAL_BUFFERS:-16MB}
default_statistics_target = ${PG_DEFAULT_STATISTICS_TARGET:-100}
random_page_cost = ${PG_RANDOM_PAGE_COST:-1.1}
effective_io_concurrency = ${PG_EFFECTIVE_IO_CONCURRENCY:-200}
work_mem = ${PG_WORK_MEM:-6553kB}
min_wal_size = ${PG_MIN_WAL_SIZE:-1GB}
max_wal_size = ${PG_MAX_WAL_SIZE:-4GB}
EOF

# Настраиваем pg_hba.conf для доступа
cat > "$PGDATA/pg_hba.conf" <<EOF
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

echo "PostgreSQL настроен с пользовательскими параметрами и правилами доступа"

# Функция для выполнения SQL-запросов
run_sql() {
    su -c "psql -c \"$1\"" postgres
}

# Проверяем существование базы данных и пользователя
if ! su -c "psql -lqt" postgres | cut -d \| -f 1 | grep -qw "${POSTGRES_DB}"; then
    echo "База данных ${POSTGRES_DB} не существует, создаем..."
    run_sql "CREATE DATABASE ${POSTGRES_DB};"
fi

if ! su -c "psql -c '\du'" postgres | grep -qw "${POSTGRES_USER}"; then
    echo "Пользователь ${POSTGRES_USER} не существует, создаем..."
    run_sql "CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';"
    run_sql "ALTER USER ${POSTGRES_USER} WITH SUPERUSER;"
fi

# Назначаем права пользователю на базу данных
run_sql "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};"

echo "База данных ${POSTGRES_DB} и пользователь ${POSTGRES_USER} настроены"

# Запускаем PostgreSQL с привилегиями пользователя postgres
exec su postgres -c "postgres"