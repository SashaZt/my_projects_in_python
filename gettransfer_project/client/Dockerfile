# client/Dockerfile
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /client

# Копируем файл зависимостей и устанавливаем библиотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код клиента
COPY main.py .

# Запускаем клиент
CMD ["python", "main.py"]
