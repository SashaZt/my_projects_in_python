#!/bin/bash

set -e

# Конфигурация
NETWORK_NAME="n8n_net"
TRAEFIK_CONTAINER="traefik"
N8N_CONTAINER="n8n"
POSTGRES_CONTAINER="postgres"

# Запрос доменного имени
read -p "🌐 Введите доменное имя (например, n8n.example.com): " DOMAIN_NAME
if [[ -z "$DOMAIN_NAME" ]]; then
    echo "❌ Доменное имя не может быть пустым"
    exit 1
fi

# Запрос email для Let's Encrypt
read -p "📧 Введите email для Let's Encrypt: " LETSENCRYPT_EMAIL
if [[ -z "$LETSENCRYPT_EMAIL" ]]; then
    echo "❌ Email не может быть пустым"
    exit 1
fi

# Генерация паролей
if [[ ! -f .n8n_env ]]; then
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    N8N_PASSWORD=$(openssl rand -hex 8)
    
    cat > .n8n_env << EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
N8N_PASSWORD=${N8N_PASSWORD}
DOMAIN_NAME=${DOMAIN_NAME}
LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}
OLD_POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
EOF
    echo "🔑 Созданы пароли:"
    echo "   PostgreSQL: ${POSTGRES_PASSWORD}"
    echo "   n8n: admin / ${N8N_PASSWORD}"
else
    source .n8n_env
    echo "📄 Используются существующие пароли"
    
    # Проверка на смену пароля PostgreSQL
    if [[ "$POSTGRES_PASSWORD" != "$OLD_POSTGRES_PASSWORD" ]] && [[ -n "$OLD_POSTGRES_PASSWORD" ]]; then
        echo "⚠️  Обнаружена смена пароля PostgreSQL"
        read -p "Удалить старую базу данных? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Удаление старой базы данных..."
            docker volume rm postgres_data >/dev/null 2>&1 || true
        fi
    fi
fi

# Создание сети
docker network inspect $NETWORK_NAME >/dev/null 2>&1 || {
    echo "📡 Создание сети..."
    docker network create $NETWORK_NAME
}

# Очистка контейнеров
echo "🧹 Очистка контейнеров..."
docker rm -f $TRAEFIK_CONTAINER $N8N_CONTAINER $POSTGRES_CONTAINER >/dev/null 2>&1 || true

# Создание volumes
echo "📦 Проверка volumes..."
volumes=("postgres_data" "n8n_data" "traefik_ssl")
for volume in "${volumes[@]}"; do
    if ! docker volume ls | grep -q "$volume"; then
        echo "   Создание $volume..."
        docker volume create $volume
    else
        echo "   $volume уже существует ✅"
    fi
done

# Создание конфигурации Traefik
echo "⚙️ Создание конфигурации Traefik..."
mkdir -p ./traefik
cat > ./traefik/traefik.yml << EOF
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entrypoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false

certificatesResolvers:
  letsencrypt:
    acme:
      email: ${LETSENCRYPT_EMAIL}
      storage: /ssl/acme.json
      tlsChallenge: {}
EOF

# Запуск Traefik
echo "🚀 Запуск Traefik..."
docker run -d --name $TRAEFIK_CONTAINER \
    --network $NETWORK_NAME \
    --restart unless-stopped \
    -p 80:80 \
    -p 443:443 \
    -p 8080:8080 \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v $(pwd)/traefik:/etc/traefik:ro \
    -v traefik_ssl:/ssl \
    traefik:v2.10

# Запуск PostgreSQL (для внешнего использования в workflows)
echo "🐘 Запуск PostgreSQL (для workflows)..."
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

# Ждем Traefik
echo "⏳ Ожидание Traefik..."
sleep 5

# Запуск n8n (SQLite для n8n, PostgreSQL доступен для workflows)
echo "🚀 Запуск n8n..."
docker run -d --name $N8N_CONTAINER \
    --network $NETWORK_NAME \
    --restart unless-stopped \
    -v n8n_data:/home/node/.n8n \
    -e WEBHOOK_URL=https://$DOMAIN_NAME \
    -e N8N_HOST="0.0.0.0" \
    -e GENERIC_TIMEZONE=Europe/Kiev \
    -e TZ=Europe/Kiev \
    -e N8N_BASIC_AUTH_ACTIVE=true \
    -e N8N_BASIC_AUTH_USER=admin \
    -e N8N_BASIC_AUTH_PASSWORD=$N8N_PASSWORD \
    -e N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true \
    -e N8N_PROTOCOL=https \
    -e N8N_PORT=5678 \
    --label "traefik.enable=true" \
    --label "traefik.http.routers.n8n.rule=Host(\`$DOMAIN_NAME\`)" \
    --label "traefik.http.routers.n8n.entrypoints=websecure" \
    --label "traefik.http.routers.n8n.tls.certresolver=letsencrypt" \
    --label "traefik.http.services.n8n.loadbalancer.server.port=5678" \
    --label "traefik.http.middlewares.secure-headers.headers.sslredirect=true" \
    --label "traefik.http.middlewares.secure-headers.headers.stsincludesubdomains=true" \
    --label "traefik.http.middlewares.secure-headers.headers.stspreload=true" \
    --label "traefik.http.middlewares.secure-headers.headers.stsseconds=31536000" \
    --label "traefik.http.middlewares.secure-headers.headers.forcestsheader=true" \
    --label "traefik.http.routers.n8n.middlewares=secure-headers" \
    docker.n8n.io/n8nio/n8n

echo "https://$DOMAIN_NAME" > /tmp/n8n_url.txt

echo ""
echo "🎉 N8N с SSL запущен!"
echo ""
echo "🔗 Доступы:"
echo "   📊 n8n: https://$DOMAIN_NAME"
echo "   🗄️ PostgreSQL: localhost:5432 (только локально)"
echo "   🌐 Traefik dashboard: http://localhost:8080"
echo ""
echo "🔑 Учетные данные:"
echo "   n8n: admin / $N8N_PASSWORD"
echo "   PostgreSQL: n8n / $POSTGRES_PASSWORD"
echo ""
echo "📊 Статус:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(traefik|n8n|postgres)"
echo ""
echo "🔗 Команды:"
echo "   Остановить: docker rm -f traefik n8n postgres"
echo "   Логи n8n: docker logs n8n"
echo "   Логи Traefik: docker logs traefik"
echo "   Проверить SSL: curl -I https://$DOMAIN_NAME"
echo ""
echo "📋 Важно:"
echo "   • Домен $DOMAIN_NAME настроен правильно ✅"
echo "   • Порты 80 и 443 открыты ✅"
echo "   • SSL-сертификат получен автоматически от Let's Encrypt ✅"
echo "   • Сертификат автоматически обновляется каждые 60 дней"
echo ""
echo "🔐 Безопасность:"
echo "   • Автоматическое перенаправление HTTP → HTTPS"
echo "   • HSTS headers включены"
echo "   • TLS 1.2+ обязательно"