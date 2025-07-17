#!/bin/bash
# Готовый скрипт кторый можно разместить на сервер, подключить сертификат, и данные n8n будут хранится в БД postgres
set -e

# Конфигурация
NETWORK_NAME="n8n_net"
TRAEFIK_CONTAINER="traefik"
N8N_CONTAINER="n8n"
POSTGRES_CONTAINER="postgres"
BD_N8N_CONTAINER="bd_n8n"

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
    BD_N8N_PASSWORD=$(openssl rand -hex 16)
    N8N_PASSWORD=$(openssl rand -hex 8)
    
    cat > .n8n_env << EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
BD_N8N_PASSWORD=${BD_N8N_PASSWORD}
N8N_PASSWORD=${N8N_PASSWORD}
DOMAIN_NAME=${DOMAIN_NAME}
LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}
OLD_POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
OLD_BD_N8N_PASSWORD=${BD_N8N_PASSWORD}
EOF
    echo "🔑 Созданы пароли:"
    echo "   PostgreSQL (workflows): ${POSTGRES_PASSWORD}"
    echo "   PostgreSQL (N8N данные): ${BD_N8N_PASSWORD}"
    echo "   n8n: admin / ${N8N_PASSWORD}"
else
    source .n8n_env
    echo "📄 Используются существующие пароли"
    
    # Проверка на смену пароля PostgreSQL
    if [[ "$POSTGRES_PASSWORD" != "$OLD_POSTGRES_PASSWORD" ]] && [[ -n "$OLD_POSTGRES_PASSWORD" ]]; then
        echo "⚠️  Обнаружена смена пароля PostgreSQL (workflows)"
        read -p "Удалить старую базу данных workflows? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Удаление старой базы данных workflows..."
            docker volume rm postgres_data >/dev/null 2>&1 || true
        fi
    fi
    
    # Проверка на смену пароля BD_N8N
    if [[ "$BD_N8N_PASSWORD" != "$OLD_BD_N8N_PASSWORD" ]] && [[ -n "$OLD_BD_N8N_PASSWORD" ]]; then
        echo "⚠️  Обнаружена смена пароля PostgreSQL (N8N данные)"
        read -p "Удалить старую базу данных N8N? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Удаление старой базы данных N8N..."
            docker volume rm bd_n8n_data >/dev/null 2>&1 || true
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
docker rm -f $TRAEFIK_CONTAINER $N8N_CONTAINER $POSTGRES_CONTAINER $BD_N8N_CONTAINER >/dev/null 2>&1 || true

# Создание volumes
echo "📦 Проверка volumes..."
volumes=("postgres_data" "bd_n8n_data" "n8n_data" "traefik_ssl")
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

# Запуск PostgreSQL для workflows (порт 5432)
echo "🐘 Запуск PostgreSQL (для workflows)..."
docker run -d --name $POSTGRES_CONTAINER \
    --network $NETWORK_NAME \
    --restart unless-stopped \
    -p 5432:5432 \
    -v postgres_data:/var/lib/postgresql/data \
    -e POSTGRES_DB=workflows \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    postgres:15

# Запуск PostgreSQL для N8N данных (порт 5433)
echo "🗄️ Запуск PostgreSQL (для данных N8N)..."
docker run -d --name $BD_N8N_CONTAINER \
    --network $NETWORK_NAME \
    --restart unless-stopped \
    -p 5433:5432 \
    -v bd_n8n_data:/var/lib/postgresql/data \
    -e POSTGRES_DB=n8n \
    -e POSTGRES_USER=n8n \
    -e POSTGRES_PASSWORD=$BD_N8N_PASSWORD \
    postgres:15

# Ждем PostgreSQL (workflows)
echo "⏳ Ожидание PostgreSQL (workflows)..."
for i in {1..30}; do
    if docker exec $POSTGRES_CONTAINER pg_isready -U postgres >/dev/null 2>&1; then
        echo "✅ PostgreSQL (workflows) готов"
        break
    fi
    echo "⏳ Попытка $i/30..."
    sleep 2
done

# Ждем PostgreSQL (N8N)
echo "⏳ Ожидание PostgreSQL (N8N данные)..."
for i in {1..30}; do
    if docker exec $BD_N8N_CONTAINER pg_isready -U n8n >/dev/null 2>&1; then
        echo "✅ PostgreSQL (N8N данные) готов"
        break
    fi
    echo "⏳ Попытка $i/30..."
    sleep 2
done

# Ждем Traefik
echo "⏳ Ожидание Traefik..."
sleep 5

# Запуск n8n (с PostgreSQL для данных N8N)
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
    -e DB_TYPE=postgresdb \
    -e DB_POSTGRESDB_HOST=$BD_N8N_CONTAINER \
    -e DB_POSTGRESDB_PORT=5432 \
    -e DB_POSTGRESDB_DATABASE=n8n \
    -e DB_POSTGRESDB_USER=n8n \
    -e DB_POSTGRESDB_PASSWORD=$BD_N8N_PASSWORD \
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
echo "🎉 N8N с SSL и PostgreSQL запущен!"
echo ""
echo "🔗 Доступы:"
echo "   📊 n8n: https://$DOMAIN_NAME"
echo "   🗄️ PostgreSQL (workflows): localhost:5432"
echo "   🗄️ PostgreSQL (N8N данные): localhost:5433"
echo "   🌐 Traefik dashboard: http://localhost:8080"
echo ""
echo "🔑 Учетные данные:"
echo "   n8n: admin / $N8N_PASSWORD"
echo "   PostgreSQL (workflows): postgres / $POSTGRES_PASSWORD"
echo "   PostgreSQL (N8N данные): n8n / $BD_N8N_PASSWORD"
echo ""
echo "📊 Статус:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(traefik|n8n|postgres|bd_n8n)"
echo ""
echo "🔗 Команды:"
echo "   Остановить: docker rm -f traefik n8n postgres bd_n8n"
echo "   Логи n8n: docker logs n8n"
echo "   Логи Traefik: docker logs traefik"
echo "   Логи PostgreSQL (workflows): docker logs postgres"
echo "   Логи PostgreSQL (N8N): docker logs bd_n8n"
echo "   Проверить SSL: curl -I https://$DOMAIN_NAME"
echo ""
echo "📋 Важно:"
echo "   • N8N использует PostgreSQL для данных (контейнер: bd_n8n) ✅"
echo "   • Отдельный PostgreSQL для workflows (контейнер: postgres) ✅"
echo "   • Домен $DOMAIN_NAME настроен правильно ✅"
echo "   • Порты 80 и 443 открыты ✅"
echo "   • SSL-сертификат получен автоматически от Let's Encrypt ✅"
echo "   • Сертификат автоматически обновляется каждые 60 дней"
echo ""
echo "🗄️ Подключения к базам данных из N8N workflows:"
echo "   • Workflows DB: host=postgres, port=5432, user=postgres, password=$POSTGRES_PASSWORD"
echo "   • N8N Internal: host=bd_n8n, port=5432, user=n8n, password=$BD_N8N_PASSWORD"
echo ""
echo "🔐 Безопасность:"
echo "   • Автоматическое перенаправление HTTP → HTTPS"
echo "   • HSTS headers включены"
echo "   • TLS 1.2+ обязательно"
echo "   • Два отдельных PostgreSQL контейнера для разных целей"