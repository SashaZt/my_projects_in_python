#!/bin/bash

echo "=== Запуск парсера клиента ==="
echo "Время запуска: $(date)"

# Переходим в директорию клиента
cd /app/client

# Проверяем наличие файлов
if [ ! -f "main_controller.py" ]; then
    echo "Ошибка: main_controller.py не найден!"
    exit 1
fi

if [ ! -f "/app/config.json" ]; then
    echo "Ошибка: config.json не найден!"
    exit 1
fi

echo "Запускаем парсер..."

# Устанавливаем зависимости если нужно
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --root-user-action=ignore --disable-pip-version-check -q
fi

# Запускаем парсер
python main_controller.py

echo "=== Парсер завершен ==="