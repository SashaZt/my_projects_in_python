@echo off
chcp 65001 >nul
setlocal

:: Определение текущей директории
set "CURRENT_DIR=%~dp0"

:: Удаление папок dist, build и .spec файла, если они существуют
echo Удаление предыдущих сборок...
if exist "%CURRENT_DIR%dist" (
    rd /s /q "%CURRENT_DIR%dist"
)
if exist "%CURRENT_DIR%build" (
    rd /s /q "%CURRENT_DIR%build"
)
if exist "%CURRENT_DIR%main.spec" (
    del /f /q "%CURRENT_DIR%main.spec"
)

:: Активация виртуального окружения
call "%CURRENT_DIR%venv\Scripts\activate"

:: Проверка наличия pyinstaller
"%CURRENT_DIR%venv\Scripts\python.exe" -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller не найден. Устанавливаю...
    "%CURRENT_DIR%venv\Scripts\python.exe" -m pip install pyinstaller
) else (
    echo PyInstaller уже установлен.
)

:: Создание исполняемого файла с помощью PyInstaller
echo Создание исполняемого файла...
pyinstaller --onefile "%CURRENT_DIR%main.py"

:: Уведомление о завершении
echo Исполняемый файл успешно создан в папке dist.
echo Скрипт завершил работу.

endlocal
exit /b
