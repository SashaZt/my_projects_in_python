#!/bin/bash

set -e  # Выход при ошибке

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COOKIES_FILE="$PROJECT_ROOT/cookies/cookies_important.json"

echo "🔄 Начинаем цикл TikLeap..."
echo "📁 Рабочая директория: $PROJECT_ROOT"

# Шаг 1: Авторизация
echo "🔐 Запускаем авторизацию..."
cd "$PROJECT_ROOT"

# Удаляем старые cookies
if [ -f "$COOKIES_FILE" ]; then
    rm "$COOKIES_FILE"
    echo "🗑️ Удалили старые cookies"
fi

# Запускаем GUI авторизацию
python3 app/auth_gui.py

# Проверяем что cookies получены
if [ ! -f "$COOKIES_FILE" ]; then
    echo "❌ Ошибка: cookies файл не найден после авторизации"
    exit 1
fi

echo "✅ Авторизация завершена, cookies получены"

# Шаг 2: Сбор данных
echo "📊 Запускаем сбор данных..."
cd "$PROJECT_ROOT/client"

python3 main.py

echo "🎉 Цикл завершен успешно!"

# ===========================================
# docker-compose.yml - Обновленный
# ===========================================

# ===========================================
# Dockerfile - Новый
# ===========================================

FROM python:3.12-slim

# Устанавливаем системные зависимости для GUI
RUN apt-get update && apt-get install -y \
    python3-tk \
    xvfb \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем requirements
COPY requirements.txt client/requirements.txt ./
RUN pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем необходимые директории
RUN mkdir -p cookies client/data client/json client/log logs

# Права на выполнение скриптов
RUN chmod +x run_cycle.sh

CMD ["python3", "main_orchestrator.py"]