# Проект buff_163_com

## Требования

### Установка Python
1. Убедитесь, что у вас установлена версия Python не ниже 3.10.9.
2. Скачать установочный файл Python можно с официального сайта [python.org](https://www.python.org/).
3. Во время установки не забудьте поставить галочку "Add Python to PATH".
4. После завершения установки перезагрузите компьютер.

### Установка pip
Если pip не установлен автоматически, выполните следующие шаги:

1. Откройте PowerShell или командную строку.
2. Скачайте установочный скрипт pip, выполнив следующую команду:
    ```bash
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    ```
3. Установите pip, выполнив следующую команду:
    ```bash
    python get-pip.py
    ```

### Установка окружения
Запустите файл setup_env.bat для создания виртуального окружения и установки всех необходимых пакетов.

setup_env.bat
### Этот файл выполняет следующие действия:

Создает виртуальное окружение в текущей директории.
1. Активирует виртуальное окружение.
2. Обновляет pip до последней версии.
3. Усанавливает необходимые модули из файла requirements.txt.

### Запуск проекта

Для запуска проекта используйте файл run_project.bat.
run_project.bat

Этот файл выполняет следующие действия:

1. Определяет текущую директорию.
2. Находит python.exe в подкаталоге \venv\Scripts.
3. Запускает main.py с использованием найденного интерпретатора Python.

### Конфигурация

В проекте есть файлы конфигурации, которые можно изменять при необходимости.
config_01.json
config_02.json
Также присутствует файл конфигурации для прокси, который можно настроить под ваши нужды.
proxi.json