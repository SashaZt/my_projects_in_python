@echo off
chcp 65001 >nul
setlocal

:: Определение текущей директории
set "CURRENT_DIR=%~dp0"

:: Поиск python.exe в папке \venv\Scripts
set "PYTHON_EXE=%CURRENT_DIR%venv\Scripts\python.exe"

:: Проверка существования python.exe в \venv\Scripts
if not exist "%PYTHON_EXE%" (
    echo Интерпретатор Python не найден в %CURRENT_DIR%venv\Scripts
    echo Попытка найти интерпретатор Python в переменной среды PATH...

    :: Поиск python.exe в системной переменной PATH
    for %%i in (python.exe) do set "PYTHON_EXE=%%~$PATH:i"

    if not defined PYTHON_EXE (
        echo Интерпретатор Python не найден в переменной среды PATH
        exit /b 1
    ) else (
        echo Используется системный интерпретатор Python: %PYTHON_EXE%
    )
) else (
    echo Используется интерпретатор Python из виртуальной среды: %PYTHON_EXE%
)

:: Запуск main.py
"%PYTHON_EXE%" "%CURRENT_DIR%main_th.py"
