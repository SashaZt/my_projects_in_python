#!/bin/bash

# Определение текущей директории (полный путь к директории, в которой находится этот скрипт)
CURRENT_DIR=$(dirname "$(realpath "$0")")

while true; do
    # Предложение выбора действия: установка venv или установка Python
    echo "Выберите действие:"
    echo "1. Установить виртуальное окружение (venv)"
    echo "2. Установить Python 3.12"
    echo "3. Закрыть программу"
    read -p "Введите номер действия (1/2/3): " action

    case $action in
        1)
            # Установка виртуального окружения в текущей директории
            # Используем команду python для создания виртуального окружения в директории venv внутри текущей директории
            echo "Установка виртуального окружения..."
            PYTHON_CMD="python3"
            if command -v python3.12 &> /dev/null; then
                PYTHON_CMD="python3.12"
            fi
            $PYTHON_CMD -m venv "$CURRENT_DIR/venv"

            # Проверка существования виртуального окружения
            # Проверяем, существует ли директория bin внутри venv, чтобы убедиться, что виртуальное окружение создано
            if [ ! -d "$CURRENT_DIR/venv/bin" ]; then
                # Если директория не найдена, выводим ошибку и завершаем выполнение скрипта
                echo "Ошибка при создании виртуального окружения."
                continue
            fi

            # Активация виртуального окружения
            # Активируем виртуальное окружение, чтобы использовать его для установки зависимостей
            echo "Активация виртуального окружения..."
            source "$CURRENT_DIR/venv/bin/activate"

            # Обновление pip
            # Обновляем pip до последней версии, чтобы избежать проблем с устаревшими версиями
            echo "Обновление pip..."
            pip install --upgrade pip

            # Проверка наличия файла requirements.txt
            # Проверяем, существует ли файл requirements.txt, чтобы установить зависимости из него
            if [ ! -f "$CURRENT_DIR/requirements.txt" ]; then
                # Если файл не найден, выводим сообщение и завершаем выполнение скрипта
                echo "Файл requirements.txt не найден. Установка остановлена."
                deactivate
                continue
            fi

            # Установка модулей из requirements.txt
            # Устанавливаем все зависимости, указанные в файле requirements.txt
            echo "Установка модулей из requirements.txt..."
            pip install -r "$CURRENT_DIR/requirements.txt"

            # Выводим сообщение об успешной установке
            echo "Установка завершена."

            # Деактивация виртуального окружения
            # Деактивируем виртуальное окружение, чтобы выйти из него
            deactivate
            ;;
        2)
            # Проверка версии Python
            # Получаем текущую версию Python и выводим её
            python_version=$(python3 --version 2>&1)
            echo "Текущая версия Python: $python_version"

            # Предложение установки Python 3.12, если версия ниже
            # Проверяем, что версия Python >= 3.12; если нет, предлагаем установить
            if ! python3 -c 'import sys; assert sys.version_info >= (3, 12)' 2>/dev/null; then
                read -p "Установить Python 3.12? (y/n): " install_python
                if [ "$install_python" = "y" ]; then
                    # Обновление списка пакетов
                    echo "Обновление списка пакетов..."
                    sudo apt update

                    # Установка необходимых пакетов для Python 3.12
                    echo "Установка необходимых пакетов для Python 3.12..."
                    sudo apt install -y software-properties-common
                    # Добавляем репозиторий, содержащий Python 3.12
                    sudo add-apt-repository -y ppa:deadsnakes/ppa
                    sudo apt update
                    # Устанавливаем Python 3.12 и необходимые компоненты для виртуального окружения
                    sudo apt install -y python3.12 python3.12-venv python3.12-dev
                else
                    # Если пользователь отказался от установки, завершаем скрипт
                    echo "Установка Python 3.12 пропущена."
                fi
            else
                echo "Версия Python 3.12 или выше уже установлена."
            fi
            ;;
        3)
            # Закрыть программу
            echo "Программа завершена."
            exit 0
            ;;
        *)
            # Обработка неверного ввода
            echo "Неверный ввод. Пожалуйста, введите 1, 2 или 3."
            ;;
    esac

done
