# Используем базовый образ
FROM python:3.12-slim

# Создаём рабочую директорию
WORKDIR /client

# Копируем файлы приложения
COPY . /client


# Устанавливаем зависимости и очищаем временные файлы
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache
# Запуск приложения
CMD ["python", "main.py"]
