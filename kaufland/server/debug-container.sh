#!/bin/bash
# Сохраните этот скрипт как debug-container.sh и сделайте его исполняемым: chmod +x debug-container.sh

echo "=== Проверка Docker и контейнеров ==="
docker --version
docker-compose --version

echo -e "\n=== Остановка контейнеров, если они запущены ==="
docker-compose down

echo -e "\n=== Пересборка контейнеров без кэша ==="
docker-compose build --no-cache

echo -e "\n=== Запуск контейнеров в фоновом режиме ==="
docker-compose up -d postgres

echo -e "\n=== Ждем 10 секунд, чтобы PostgreSQL запустился ==="
sleep 10

echo -e "\n=== Проверка статуса PostgreSQL ==="
docker-compose exec postgres pg_isready -U postgres_user -d kaufland

echo -e "\n=== Запуск веб-контейнера ==="
docker-compose up -d web

echo -e "\n=== Логи веб-контейнера (последние 50 строк) ==="
docker-compose logs --tail=50 web

echo -e "\n=== Проверка установленных пакетов в контейнере ==="
docker-compose exec web pip freeze | grep -E "asyncpg|fastapi|sqlalchemy"

echo -e "\n=== Проверка структуры файлов в контейнере ==="
docker-compose exec web ls -la /root
docker-compose exec web ls -la /root/app
docker-compose exec web ls -la /root/app/api

echo -e "\n=== Проверка переменных окружения ==="
docker-compose exec web printenv | grep DATABASE_URL

echo -e "\n=== Тестовый импорт asyncpg ==="
docker-compose exec web python -c "import asyncpg; print('asyncpg импортирован успешно')"

echo -e "\n=== Завершение отладки ==="
echo "Для просмотра логов в реальном времени выполните: docker-compose logs -f web"