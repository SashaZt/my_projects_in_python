#!/bin/bash

set -e

# Конфигурация
NETWORK_NAME="n8n_net"
NGROK_CONTAINER="ngrok"
N8N_CONTAINER="n8n"
NGROK_TOKEN="2yDcz8stDzZVSzPxoCdt1pqJZdy_78Ce6TNwJrZj9X3oKY3Rj"

# Создание сети, если не существует
docker network inspect $NETWORK_NAME >/dev/null 2>&1 || {
  echo "📡 Создание Docker-сети $NETWORK_NAME..."
  docker network create $NETWORK_NAME
}

# Удаление старых контейнеров при необходимости
docker rm -f $NGROK_CONTAINER >/dev/null 2>&1 || true
docker rm -f $N8N_CONTAINER >/dev/null 2>&1 || true

# Запуск ngrok
echo "🚀 Запуск ngrok..."
docker run -d --name $NGROK_CONTAINER \
  --network $NETWORK_NAME \
  -e NGROK_AUTHTOKEN=$NGROK_TOKEN \
  -p 4040:4040 \
  ngrok/ngrok http $N8N_CONTAINER:5678 >/dev/null

# Ожидание и парсинг URL
echo "⏳ Получение URL от ngrok..."
for i in {1..10}; do
  NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[a-zA-Z0-9.-]*\.ngrok-free\.app' | head -n 1)
  if [[ -n "$NGROK_URL" ]]; then
    echo "✅ URL получен: $NGROK_URL"
    break
  fi
  sleep 1
done

if [[ -z "$NGROK_URL" ]]; then
  echo "❌ Не удалось получить ngrok URL"
  docker rm -f $NGROK_CONTAINER
  exit 1
fi

# Запуск n8n с нужным WEBHOOK_URL
echo "🚀 Запуск n8n с WEBHOOK_URL=$NGROK_URL"
docker run -d --name $N8N_CONTAINER \
  --network $NETWORK_NAME \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e WEBHOOK_URL=$NGROK_URL \
  docker.n8n.io/n8nio/n8n

echo "🎉 n8n доступен по адресу: $NGROK_URL"
