# Используем официальный образ Python 3.12
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости и очищаем временные файлы
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache

# Копируем исходный код приложения
COPY . /app

# Указываем открытые порты и запускаем приложение
EXPOSE 5000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
