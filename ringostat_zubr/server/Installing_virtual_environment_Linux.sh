# Сохраните этот скрипт с расширением .sh, например setup_venv.sh
# Чтобы сделать файл исполняемым, выполните команду: chmod +x setup_venv.sh
# Для запуска скрипта выполните команду: ./setup_venv.sh

#!/bin/bash

# Определение текущей директории (полный путь к директории, в которой находится этот скрипт)
CURRENT_DIR=$(dirname "$(realpath "$0")")

# Установка виртуального окружения в текущей директории
# Используем python3 для создания виртуального окружения в директории venv внутри текущей директории
echo "Установка виртуального окружения..."
python3 -m venv "$CURRENT_DIR/venv"

# Проверка существования виртуального окружения
# Проверяем, существует ли директория bin внутри venv, чтобы убедиться, что виртуальное окружение создано
if [ -d "$CURRENT_DIR/venv/bin" ]; then
    echo "Виртуальное окружение создано успешно."
else
    echo "Ошибка при создании виртуального окружения."
    exit 1
fi

# Активация виртуального окружения
# Активация виртуального окружения, чтобы использовать его для установки зависимостей
echo "Активация виртуального окружения..."
source "$CURRENT_DIR/venv/bin/activate"

# Обновление pip
# Обновляем pip до последней версии, чтобы избежать проблем с устаревшими версиями
echo "Обновление pip..."
pip install --upgrade pip

# Проверка наличия файла requirements.txt
# Проверяем, существует ли файл requirements.txt, чтобы установить зависимости из него
if [ ! -f "$CURRENT_DIR/requirements.txt" ]; then
    echo "Файл requirements.txt не найден. Установка остановлена."
    exit 1
fi

# Установка модулей из requirements.txt
# Устанавливаем все зависимости, указанные в файле requirements.txt
echo "Установка модулей из requirements.txt..."
pip install -r "$CURRENT_DIR/requirements.txt"

echo "Установка завершена."