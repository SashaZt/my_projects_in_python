#!/bin/bash
set -e

# Проверяем, существуют ли сертификаты
if [ ! -f /etc/ssl/private/cert.pem ] || [ ! -f /etc/ssl/private/key.pem ]; then
    echo "SSL certificates not found, generating self-signed certificates..."
    generate-certs.sh
else
    echo "Using mounted SSL certificates"
fi

# Запускаем команду, переданную в CMD
exec "$@"