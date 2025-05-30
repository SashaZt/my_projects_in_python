#!/bin/bash
# verify-timezone.sh - Скрипт для проверки настройки временной зоны

echo "=== Проверка временной зоны PostgreSQL ==="

# Проверяем переменные окружения
echo "Переменные окружения:"
echo "TZ: ${TZ:-не установлено}"
echo "PGTZ: ${PGTZ:-не установлено}"

# Проверяем системную временную зону
echo ""
echo "Системная временная зона:"
if [ -f /etc/timezone ]; then
    echo "Файл /etc/timezone: $(cat /etc/timezone)"
fi
echo "Команда date: $(date)"
echo "Команда timedatectl (если доступна): $(timedatectl show --property=Timezone --value 2>/dev/null || echo 'недоступно')"

# Подключаемся к PostgreSQL и проверяем настройки
echo ""
echo "Проверка PostgreSQL:"
echo "Подключение к базе данных..."

# Ждем, пока PostgreSQL будет готов
until pg_isready -h localhost -p 5432 -U ${POSTGRES_USER:-postgres}; do
    echo "Ожидание готовности PostgreSQL..."
    sleep 2
done

# Выполняем SQL запросы для проверки
psql -h localhost -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-postgres} << 'EOF'
\echo 'Текущие настройки временной зоны в PostgreSQL:'
SELECT 
    current_setting('timezone') as postgresql_timezone,
    now() as current_timestamp_with_tz,
    extract(timezone from now()) as tz_offset_hours,
    to_char(now(), 'YYYY-MM-DD HH24:MI:SS TZ') as formatted_time;

\echo ''
\echo 'Проверка функций (если существуют):'
SELECT 
    get_local_time() as local_time,
    get_formatted_local_time() as formatted_local_time
WHERE EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'get_local_time');

\echo ''
\echo 'Сравнение времени:'
SELECT 
    now() as utc_time,
    now() AT TIME ZONE 'Europe/Kiev' as kiev_time,
    now() AT TIME ZONE current_setting('timezone') as configured_tz_time;
EOF

echo ""
echo "=== Проверка завершена ==="