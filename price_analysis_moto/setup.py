from cx_Freeze import setup, Executable
import sys
import os
import curl_cffi  # Импортируем для доступа к файлам этой библиотеки

base = None
if sys.platform == "win32":
    base = (
        "Win32GUI"  # Используйте это, если ваше приложение имеет графический интерфейс.
    )

# Определение пути к site-packages в виртуальном окружении в текущей директории
current_directory = os.path.abspath(os.path.dirname(__file__))
venv_site_packages = os.path.join(current_directory, "venv", "Lib", "site-packages")

# Определение пути к библиотекам curl_cffi
curl_cffi_dll_path = os.path.dirname(curl_cffi.__file__)

options = {
    "build_exe": {
        "packages": [],  # Оставляем пустым, чтобы cx_Freeze автоматически нашел нужные пакеты
        "include_files": [
            (curl_cffi_dll_path, "curl_cffi")  # Включаем файлы curl_cffi
        ],  # Включение необходимых файлов
        "path": [
            venv_site_packages
        ],  # Указываем путь к site-packages в текущей директории
    },
}

setup(
    name="website_analysis",  # Название вашего приложения
    version="1.0",  # Версия вашего приложения
    description="A tool for analyzing websites",  # Краткое описание вашего приложения
    options=options,
    executables=[
        Executable(
            "main.py",  # Основной файл вашего проекта
            base=base,
        )
    ],
)
