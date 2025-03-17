FROM nginx:alpine

# Метаданные
LABEL maintainer="user@example.com"
LABEL description="Nginx для проксирования MinIO и обеспечения доступа по красивым URL"
LABEL version="1.0"

# Установка дополнительных пакетов
RUN apk add --no-cache curl bash

# Создание скрипта проверки здоровья напрямую
RUN echo '#!/bin/bash\n\n# Проверяем доступность Nginx\nif curl -s http://localhost/nginx-health > /dev/null; then\n  echo "Nginx is healthy"\n  exit 0\nelse\n  echo "Nginx is not healthy"\n  exit 1\nfi' > /usr/local/bin/healthcheck.sh && \
    chmod +x /usr/local/bin/healthcheck.sh

# Порты
EXPOSE 80 443

# Проверка здоровья
HEALTHCHECK --interval=30s --timeout=5s \
    CMD /usr/local/bin/healthcheck.sh || exit 1

# Заменим стандартный конфиг, чтобы не было страницы по умолчанию
RUN rm -rf /etc/nginx/conf.d/default.conf

# Создадим директорию для сертификатов Let's Encrypt
RUN mkdir -p /etc/letsencrypt