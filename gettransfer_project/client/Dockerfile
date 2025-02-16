# # client/Dockerfile
# FROM python:3.12-slim

# LABEL maintainer="your-email@example.com"
# LABEL version="1.0"
# LABEL description="Client application"

# # Установить только необходимые пакеты
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     curl \
#     && rm -rf /var/lib/apt/lists/*

# # Создать непривилегированного пользователя
# RUN useradd -m clientuser

# WORKDIR /client

# # Оптимизировать установку зависимостей
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Копировать код приложения
# COPY . .

# # Сменить владельца файлов
# RUN chown -R clientuser:clientuser /client
# USER clientuser


# CMD ["python", "main.py"]
# client/Dockerfile
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /client
RUN apt-get update && apt-get install -y openssl curl 

# Копируем файл зависимостей и устанавливаем библиотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код клиента
COPY . /client

# Запускаем клиент
CMD ["python", "main.py"]