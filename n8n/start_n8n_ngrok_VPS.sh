#!/bin/bash

set -e

# Конфигурация
NETWORK_NAME="n8n_net"
NGROK_CONTAINER="ngrok"
N8N_CONTAINER="n8n"
NGROK_TOKEN="2yuJNHCYsq1waUCF7FkLApfEcPX_2Rcqiy36oaV6wMhyJdbQK"

# Создание сети, если не существует
docker network inspect $NETWORK_NAME >/dev/null 2>&1 || {
  echo "📡 Создание Docker-сети $NETWORK_NAME..."
  docker network create $NETWORK_NAME
}

# Удаление старых контейнеров при необходимости
echo "🧹 Очистка старых контейнеров..."
docker rm -f $NGROK_CONTAINER >/dev/null 2>&1 || true
docker rm -f $N8N_CONTAINER >/dev/null 2>&1 || true

# Создание volume для данных (важно для VPS!)
echo "💾 Создание volume для данных n8n..."
docker volume create n8n_data >/dev/null 2>&1 || true

# Запуск ngrok с автореstart
echo "🚀 Запуск ngrok..."
docker run -d --name $NGROK_CONTAINER \
  --network $NETWORK_NAME \
  --restart unless-stopped \
  -e NGROK_AUTHTOKEN=$NGROK_TOKEN \
  -p 4040:4040 \
  ngrok/ngrok http $N8N_CONTAINER:5678 >/dev/null

# Ожидание и парсинг URL (увеличено время ожидания для VPS)
echo "⏳ Получение URL от ngrok..."
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
  echo "🔍 Проверим логи ngrok:"
  docker logs $NGROK_CONTAINER
  docker rm -f $NGROK_CONTAINER
  exit 1
fi

# Запуск n8n с нужным WEBHOOK_URL и автореstart
echo "🚀 Запуск n8n с WEBHOOK_URL=$NGROK_URL"
docker run -d --name $N8N_CONTAINER \
  --network $NETWORK_NAME \
  --restart unless-stopped \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e WEBHOOK_URL=$NGROK_URL \
  -e N8N_HOST="0.0.0.0" \
  -e GENERIC_TIMEZONE=Europe/Kiev \
  -e TZ=Europe/Kiev \
  docker.n8n.io/n8nio/n8n

echo "🎉 n8n доступен по адресу: $NGROK_URL"

# Сохранение URL для удобства
echo $NGROK_URL > /tmp/n8n_url.txt
echo "💾 URL сохранен в /tmp/n8n_url.txt"

# Показать статус контейнеров
echo ""
echo "📊 Статус контейнеров:"
docker ps | grep -E "($NGROK_CONTAINER|$N8N_CONTAINER)"

echo ""
echo "🔗 Полезные команды:"
echo "   Проверить URL: cat /tmp/n8n_url.txt"
echo "   Логи n8n: docker logs n8n"
echo "   Логи ngrok: docker logs ngrok"
echo "   Остановить: docker rm -f n8n ngrok"