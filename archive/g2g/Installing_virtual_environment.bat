#!/bin/bash

# Установка кодировки UTF-8
export LANG=en_US.UTF-8

# Получение директории, где находится скрипт
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Путь к виртуальному окружению
VENV_DIR="$CURRENT_DIR/venv"

# Создание виртуального окружения
echo "Создание виртуального окружения..."
python3 -m venv "$VENV_DIR"

# Проверка успешности создания виртуального окружения
if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
    echo "Виртуальное окружение создано успешно."
else
    echo "Ошибка: Не удалось создать виртуальное окружение."
    exit 1
fi

# Активация виртуального окружения
echo "Активация виртуального окружения..."
source "$VENV_DIR/bin/activate"

# Обновление pip
echo "Обновление pip..."
python3 -m pip install --upgrade pip

# Проверка наличия requirements.txt
if [ ! -f "$CURRENT_DIR/requirements.txt" ]; then
    echo "Ошибка: Файл requirements.txt не найден. Установка остановлена."
    exit 1
fi

# Установка зависимостей из requirements.txt
echo "Установка зависимостей из requirements.txt..."
pip install -r "$CURRENT_DIR/requirements.txt"

# Проверка наличия playwright в requirements.txt
if grep -i "playwright" "$CURRENT_DIR/requirements.txt" > /dev/null; then
    echo "Установка Chromium для Playwright..."
    python3 -m playwright install chromium
else
    echo "Playwright не найден в requirements.txt, пропускаем установку Chromium."
fi

echo "Установка завершена."