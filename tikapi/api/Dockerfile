FROM python:3.12-slim

WORKDIR /api

RUN apt-get update && apt-get install -y openssl curl

COPY api/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install alembic

COPY api/ /api/

# Создаем директорию для сертификатов
RUN mkdir -p /etc/ssl/private

# Скрипт генерации сертификатов, который запускается только если сертификаты не смонтированы
COPY generate-certs.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/generate-certs.sh

# Entrypoint проверяет наличие сертификатов перед запуском приложения
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "main.py"]