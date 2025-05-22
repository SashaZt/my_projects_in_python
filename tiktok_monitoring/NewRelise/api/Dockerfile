FROM python:3.12-slim

RUN apt-get update && apt-get install -y openssl

# Устанавливаем рабочую директорию /app
WORKDIR /app

ENV PYTHONPATH=/app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все содержимое текущей директории (api) в /app
COPY . .

# Создаем SSL-сертификаты
RUN mkdir -p /etc/ssl/private && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/key.pem \
    -out /etc/ssl/private/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

# Создаем директорию для логов, если её ещё нет
RUN mkdir -p /app/logs

# Запускаем main.py из текущей директории (/app)
ENTRYPOINT ["python"]
CMD ["main.py"]