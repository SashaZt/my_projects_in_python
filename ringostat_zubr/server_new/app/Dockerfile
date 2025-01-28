# Используем базовый образ
FROM python:3.12-slim

# Установим openssl для генерации ключей и сертификатов
RUN apt-get update && apt-get install -y openssl

# Создаём рабочую директорию
WORKDIR /app

# Копируем файлы приложения
COPY . /app

# Генерация SSL-ключей и сертификатов
RUN mkdir -p /etc/ssl/private && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/key.pem \
    -out /etc/ssl/private/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

# Устанавливаем зависимости и очищаем временные файлы
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache
# Запуск приложения
CMD ["python", "main.py"]
