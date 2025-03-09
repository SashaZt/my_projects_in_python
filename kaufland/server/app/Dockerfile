FROM python:3.12-slim

RUN apt-get update && apt-get install -y openssl curl

WORKDIR /root
ENV PYTHONPATH=/root 

COPY app/requirements.txt /root/app/
RUN pip install --no-cache-dir -r /root/app/requirements.txt

# Копируем код приложения
COPY app/ /root/app/

RUN mkdir -p /etc/ssl/private && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/key.pem \
    -out /etc/ssl/private/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

# Запускаем приложение
CMD ["python", "-m", "app.main"]