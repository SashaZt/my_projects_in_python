@echo off
chcp 65001 > nul
REM Файл для создания зависимостей, сборки исполняемого файла и удаления папки venv

REM Проверка существования директории виртуального окружения
if not exist .\venv\Scripts\activate (
    echo Ошибка: Виртуальное окружение не найдено.
    exit /b 1
)

REM 1. Активация виртуального окружения
call .\venv\Scripts\activate

REM Проверка, была ли активация успешной
if errorlevel 1 (
    echo Ошибка активации виртуального окружения.
    exit /b 1
)

REM 2. Выполнение команды pyinstaller для создания исполняемого файла
pyinstaller --onefile --name=main main.py

REM Проверка, успешно ли выполнен pyinstaller
if errorlevel 1 (
    echo Ошибка при создании исполняемого файла через pyinstaller.
    exit /b 1
)

REM Проверка существования исполняемого файла
if not exist .\dist\main.exe (
    echo Ошибка: Исполняемый файл main.exe не найден.
    exit /b 1
)

echo Исполняемый файл main.exe успешно создан.

REM Завершение программы
exit /b 0
