FROM python:3.12-slim

WORKDIR /client

# Устанавливаем bash для выполнения скриптов
RUN apt-get update && apt-get install -y bash && apt-get clean

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем папку для монтированных файлов
RUN mkdir -p /app


# Запуск с обработкой сигналов
CMD ["python", "main.py"]