@echo off
setlocal enabledelayedexpansion

REM Функция для обработки папок рекурсивно
:process_folder
set "current_folder=%~1"
set /a indent_level=%~2

REM Проверка на превышение вложенности
if %indent_level% GTR 1 (
    exit /b
)

REM Отображение текущей папки с отступами
set "indent="
for /l %%i in (1,1,%indent_level%) do set "indent=!indent!    "

REM Подсчёт общего размера папки
for /f "tokens=1-3 delims= " %%A in ('dir "%current_folder%" /s /a ^| findstr /r "^[ ]*[0-9][0-9]*[ ]bytes"') do (
    set "size=%%C"
)

REM Преобразование байтов в мегабайты
set /a "sizeMB=%size%/1024/1024"
echo !indent![!sizeMB! MB] %~nx1

REM Рекурсивная обработка вложенных папок
for /d %%D in ("%current_folder%\*") do call :process_folder "%%D" !indent_level!+1

exit /b

:start
if "%~1"=="" (
    echo Укажите путь к папке как аргумент.
    exit /b
)

call :process_folder "%~1" 0
