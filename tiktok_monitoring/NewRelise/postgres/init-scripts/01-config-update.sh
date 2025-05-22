#!/bin/bash
set -e

# Этот скрипт запускается при инициализации PostgreSQL

# Обновляем postgresql.conf с нашими настройками
cat >> "$PGDATA/postgresql.conf" <<EOF

# Дополнительные настройки (добавлены скриптом init)
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

# Добавляем правила доступа в pg_hba.conf
cat >> "$PGDATA/pg_hba.conf" <<EOF

# Дополнительные правила доступа (добавлены скриптом init)
# Разрешаем подключения из сети Docker
host    all             all             10.0.0.0/8              md5
# Разрешаем подключения из всех сетей (для разработки)
host    all             all             all                     md5
EOF

echo "PostgreSQL настроен с пользовательскими параметрами и правилами доступа"