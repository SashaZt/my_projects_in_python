FROM python:3.12-slim

WORKDIR /app

COPY app.py /app/
# Устанавливаем необходимые пакеты
RUN pip install --no-cache-dir aiohttp

VOLUME /data

EXPOSE 8080

CMD ["python", "app.py"]