#!/bin/bash
# n8n + PostgreSQL + ngrok
set -e

# Конфигурация
NETWORK_NAME="simple_net"
NGROK_CONTAINER="ngrok"
N8N_CONTAINER="n8n"
POSTGRES_CONTAINER="postgres"
NGROK_TOKEN="2yuJNHCYsq1waUCF7FkLApfEcPX_2Rcqiy36oaV6wMhyJdbQK"

# Генерация паролей
if [[ ! -f .simple_env ]]; then
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    N8N_PASSWORD=$(openssl rand -hex 8)
    
    cat > .simple_env << EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
N8N_PASSWORD=${N8N_PASSWORD}
EOF
    echo "🔑 Созданы пароли:"
    echo "   PostgreSQL: ${POSTGRES_PASSWORD}"
    echo "   n8n: admin / ${N8N_PASSWORD}"
else
    source .simple_env
    echo "📄 Используются существующие пароли"
fi

# Создание сети
docker network inspect $NETWORK_NAME >/dev/null 2>&1 || {
    echo "📡 Создание сети..."
    docker network create $NETWORK_NAME
}

# Очистка
echo "🧹 Очистка контейнеров..."
docker rm -f $NGROK_CONTAINER $N8N_CONTAINER $POSTGRES_CONTAINER >/dev/null 2>&1 || true

# Создание volumes (только если не существуют)
echo "📦 Проверка volumes..."
if ! docker volume ls | grep -q "postgres_data"; then
    echo "   Создание postgres_data..."
    docker volume create postgres_data
else
    echo "   postgres_data уже существует ✅"
fi

if ! docker volume ls | grep -q "n8n_data"; then
    echo "   Создание n8n_data..."
    docker volume create n8n_data
else
    echo "   n8n_data уже существует ✅"
fi

# Запуск PostgreSQL
echo "🐘 Запуск PostgreSQL..."
docker run -d --name $POSTGRES_CONTAINER \
    --network $NETWORK_NAME \
    --restart unless-stopped \
    -p 5432:5432 \
    -v postgres_data:/var/lib/postgresql/data \
    -e POSTGRES_DB=n8n \
    -e POSTGRES_USER=n8n \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    postgres:15

# Ждем PostgreSQL
echo "⏳ Ожидание PostgreSQL..."
for i in {1..30}; do
    if docker exec $POSTGRES_CONTAINER pg_isready -U n8n >/dev/null 2>&1; then
        echo "✅ PostgreSQL готов"
        break
    fi
    echo "⏳ Попытка $i/30..."
    sleep 2
done

# Запуск ngrok
echo "🚀 Запуск ngrok..."
docker run -d --name $NGROK_CONTAINER \
    --network $NETWORK_NAME \
    --restart unless-stopped \
    -e NGROK_AUTHTOKEN=$NGROK_TOKEN \
    -p 4040:4040 \
    ngrok/ngrok http $N8N_CONTAINER:5678 >/dev/null

# Получение ngrok URL
echo "⏳ Получение ngrok URL..."
for i in {1..15}; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[a-zA-Z0-9.-]*\.ngrok-free\.app' | head -n 1)
    if [[ -n "$NGROK_URL" ]]; then
        echo "✅ URL получен: $NGROK_URL"
        break
    fi
    echo "⏳ Попытка $i/15..."
    sleep 2
done

if [[ -z "$NGROK_URL" ]]; then
    echo "❌ Не удалось получить ngrok URL"
    exit 1
fi

# Запуск n8n
echo "🚀 Запуск n8n..."
docker run -d --name $N8N_CONTAINER \
    --network $NETWORK_NAME \
    --restart unless-stopped \
    -p 5678:5678 \
    -v n8n_data:/home/node/.n8n \
    -e WEBHOOK_URL=$NGROK_URL \
    -e N8N_HOST="0.0.0.0" \
    -e GENERIC_TIMEZONE=Europe/Kiev \
    -e TZ=Europe/Kiev \
    -e N8N_BASIC_AUTH_ACTIVE=true \
    -e N8N_BASIC_AUTH_USER=admin \
    -e N8N_BASIC_AUTH_PASSWORD=$N8N_PASSWORD \
    -e DB_TYPE=postgresdb \
    -e DB_POSTGRESDB_HOST=$POSTGRES_CONTAINER \
    -e DB_POSTGRESDB_PORT=5432 \
    -e DB_POSTGRESDB_DATABASE=n8n \
    -e DB_POSTGRESDB_USER=n8n \
    -e DB_POSTGRESDB_PASSWORD=$POSTGRES_PASSWORD \
    docker.n8n.io/n8nio/n8n

echo $NGROK_URL > /tmp/n8n_url.txt

echo ""
echo "🎉 Простой стек запущен!"
echo ""
echo "🔗 Доступы:"
echo "   📊 n8n (внешний): $NGROK_URL"
echo "   📊 n8n (локальный): http://localhost:5678"
echo "   🗄️ PostgreSQL: localhost:5432"
echo "   🌐 ngrok dashboard: http://localhost:4040"
echo ""
echo "🔑 Учетные данные:"
echo "   n8n: admin / $N8N_PASSWORD"
echo "   PostgreSQL: n8n / $POSTGRES_PASSWORD"
echo ""
echo "📊 Статус:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(ngrok|n8n|postgres)"
echo ""
echo "🔗 Команды:"
echo "   Остановить: docker rm -f ngrok n8n postgres"
echo "   Логи n8n: docker logs n8n"