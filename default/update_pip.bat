@echo off
chcp 65001 >nul
setlocal
:: Определение текущей директории
set "CURRENT_DIR=%~dp0"

:: Проверка существования виртуального окружения
if not exist "%CURRENT_DIR%venv\Scripts\activate" (
    echo Виртуальное окружение не найдено. Создайте его перед выполнением этого скрипта.
    exit /b 1
)

:: Активация виртуального окружения
echo Активация виртуального окружения...
call "%CURRENT_DIR%venv\Scripts\activate"

:: Обновление pip
echo Обновление pip до последней версии...
python.exe -m pip install --upgrade pip

:: Обновление всех установленных пакетов
echo Обновление всех установленных пакетов...
for /f "skip=2 tokens=1" %%i in ('pip list --outdated --format=columns') do (
    echo Обновление %%i...
    pip install --upgrade %%i
)

echo Все пакеты успешно обновлены.
pause
