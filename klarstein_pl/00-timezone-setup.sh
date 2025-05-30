#!/bin/bash
# init-scripts/00-timezone-setup.sh

set -e  # Остановка при любой ошибке

# Получаем временную зону из переменной окружения или используем значение по умолчанию
TIMEZONE=${TZ}

echo "=== Настройка временной зоны PostgreSQL ==="
echo "Устанавливаемая временная зона: $TIMEZONE"

# Проверяем, что временная зона существует
if [ ! -f "/usr/share/zoneinfo/$TIMEZONE" ]; then
    echo "ОШИБКА: Временная зона $TIMEZONE не найдена!"
    echo "Доступные зоны в /usr/share/zoneinfo/"
    ls /usr/share/zoneinfo/ | head -10
    echo "Используем Europe/Kiev по умолчанию"
    TIMEZONE="Europe/Kiev"
fi

# Настройка системной временной зоны
echo "Настройка системной временной зоны..."
ln -snf /usr/share/zoneinfo/$TIMEZONE /etc/localtime
echo $TIMEZONE > /etc/timezone

echo "Системная временная зона установлена: $(cat /etc/timezone)"

# Создание SQL скрипта для PostgreSQL
echo "Создание SQL скрипта для PostgreSQL..."
cat > /docker-entrypoint-initdb.d/01-timezone.sql << EOF
-- Автоматически сгенерированный скрипт настройки временной зоны
-- Временная зона: $TIMEZONE
-- Создан: $(date)

\echo 'Настройка временной зоны PostgreSQL: $TIMEZONE'

-- Устанавливаем временную зону для всего кластера
ALTER SYSTEM SET timezone = '$TIMEZONE';

-- Перезагружаем конфигурацию
SELECT pg_reload_conf();

-- Устанавливаем временную зону для текущей сессии
SET timezone = '$TIMEZONE';

-- Проверяем установленную временную зону
\echo 'Проверка временной зоны:'
SELECT 
    current_setting('timezone') as current_timezone,
    now() as current_time_with_timezone,
    extract(timezone from now()) as timezone_offset_hours;

-- Создание функции для получения времени в установленной зоне
CREATE OR REPLACE FUNCTION get_local_time() 
RETURNS timestamptz AS \$function\$
BEGIN
    RETURN now() AT TIME ZONE '$TIMEZONE';
END;
\$function\$ LANGUAGE plpgsql;

-- Создание функции для форматированного времени
CREATE OR REPLACE FUNCTION get_formatted_local_time() 
RETURNS text AS \$function\$
BEGIN
    RETURN to_char(now() AT TIME ZONE '$TIMEZONE', 'YYYY-MM-DD HH24:MI:SS TZ');
END;
\$function\$ LANGUAGE plpgsql;

-- Пример использования функций
\echo 'Примеры использования:'
SELECT 
    get_local_time() as local_time,
    get_formatted_local_time() as formatted_local_time;

\echo 'Временная зона PostgreSQL успешно настроена!'
EOF

echo "SQL скрипт создан: /docker-entrypoint-initdb.d/01-timezone.sql"
echo "=== Настройка временной зоны завершена ==="
echo "Временная зона: $TIMEZONE"
echo "Текущее время системы: $(date)"
echo "=========================================="