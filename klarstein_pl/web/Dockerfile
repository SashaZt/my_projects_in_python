FROM python:3.12-slim

WORKDIR /web

# Устанавливаем bash для выполнения скриптов
RUN apt-get update && apt-get install -y bash && apt-get clean

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем папку для монтированных файлов
RUN mkdir -p /app

# Убеждаемся что скрипты будут исполняемыми
RUN chmod +x /app/start.sh 2>/dev/null || true

EXPOSE 8000

# Запуск с обработкой сигналов
CMD ["python", "main.py"]