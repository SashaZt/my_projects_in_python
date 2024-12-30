# Используем минимальный образ Python 3.12
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем только файл зависимостей для установки
COPY requirements.txt ./

# Устанавливаем зависимости и очищаем временные файлы
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache

# Копируем все файлы проекта в контейнер
COPY . .

# Указываем точку входа для запуска приложения
CMD ["python", "main.py"]
