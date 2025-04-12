#!/bin/bash
# В /entrypoint.sh
CERT_DIR="/etc/ssl/private"
KEY_FILE="$CERT_DIR/server.key"
CERT_FILE="$CERT_DIR/server.crt"

# Генерация сертификатов
if [ ! -f "$KEY_FILE" ] || [ ! -f "$CERT_FILE" ]; then
    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"
    
    # Установка правильных переменных окружения для main.py
    export SSL_KEYFILE="$KEY_FILE"
    export SSL_CERTFILE="$CERT_FILE"
fi

# Запускаем переданную команду
exec "$@"