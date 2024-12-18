@echo off
setlocal

:: Определение текущей директории
set "CURRENT_DIR=%~dp0"

:: Установка виртуального окружения в текущей директории
echo Creating virtual environment...
python -m venv "%CURRENT_DIR%venv"

:: Проверка существования виртуального окружения
if exist "%CURRENT_DIR%venv\Scripts\activate" (
    echo Virtual environment created successfully.
) else (
    echo Failed to create virtual environment.
    exit /b 1
)

:: Активация виртуального окружения
echo Activating virtual environment...
call "%CURRENT_DIR%venv\Scripts\activate"

:: Обновление pip
echo Upgrading pip...
python.exe -m pip install --upgrade pip

:: Установка модулей из requirements.txt
if exist "%CURRENT_DIR%requirements.txt" (
    echo Installing modules from requirements.txt...
    pip install -r "%CURRENT_DIR%requirements.txt"
) else (
    echo requirements.txt not found.
    exit /b 1
)

:: Установка Chromium для Playwright
:: echo Installing Chromium for Playwright...
:: python -m playwright install chromium

echo Setup complete.
