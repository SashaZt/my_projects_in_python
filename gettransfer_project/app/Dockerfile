# app/Dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y openssl curl

WORKDIR /app
ENV PYTHONPATH=/app 

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install alembic

# Копируем весь код приложения (включая main.py и другие модули)
COPY app/ /app/
COPY ./alembic /app/alembic
# COPY ./alembic.ini /app/alembic.ini


RUN mkdir -p /etc/ssl/private && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/key.pem \
    -out /etc/ssl/private/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

# Изменяем на использование entrypoint и cmd
ENTRYPOINT ["python"]
CMD ["main.py"]