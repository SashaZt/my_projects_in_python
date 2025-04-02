#!/bin/bash

# Генерация SSL-сертификатов
if [ ! -f "$SSL_KEYFILE" ] || [ ! -f "$SSL_CERTFILE" ]; then
    echo "Генерация самоподписанных SSL-сертификатов..."
    
    # Убедимся, что директории существуют
    mkdir -p $(dirname "$SSL_KEYFILE")
    mkdir -p $(dirname "$SSL_CERTFILE")
    
    # Генерируем сертификаты одной командой
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_KEYFILE" \
        -out "$SSL_CERTFILE" \
        -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"
    
    echo "SSL-сертификаты созданы успешно!"
fi

# Запускаем переданную команду
exec "$@"