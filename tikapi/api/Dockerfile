# api/Dockerfile
FROM python:3.12-slim

WORKDIR /api

RUN apt-get update && apt-get install -y openssl curl

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем директорию для SSL-сертификатов
RUN mkdir -p /etc/ssl/private

# Создаем правильный скрипт для генерации SSL-сертификатов
RUN echo '#!/bin/bash\n\
    # Генерация SSL-сертификатов\n\
    CERT_DIR="/etc/ssl/private"\n\
    SSL_KEYFILE="$CERT_DIR/server.key"\n\
    SSL_CERTFILE="$CERT_DIR/server.crt"\n\
    if [ ! -f "$SSL_KEYFILE" ] || [ ! -f "$SSL_CERTFILE" ]; then\n\
    echo "Генерация самоподписанных SSL-сертификатов..."\n\
    mkdir -p "$CERT_DIR"\n\
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\\n\
    -keyout "$SSL_KEYFILE" \\\n\
    -out "$SSL_CERTFILE" \\\n\
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"\n\
    echo "SSL-сертификаты созданы успешно!"\n\
    fi\n\
    # Запускаем переданную команду\n\
    exec "$@"' > /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]