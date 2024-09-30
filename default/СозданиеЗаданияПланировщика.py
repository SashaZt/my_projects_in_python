"""
Для планирования задач на Windows можно использовать стандартный модуль
Python subprocess для взаимодействия с командой schtasks, которая
добавляет задачи в Планировщик задач.
"""

import os
import subprocess
import shutil

# Определяем текущую директорию
current_dir = os.path.dirname(os.path.abspath(__file__))

# Поиск интерпретатора Python в виртуальной среде \venv\Scripts
python_exe = os.path.join(current_dir, "venv", "Scripts", "python.exe")

# Если интерпретатор не найден в \venv\Scripts, ищем в системной переменной PATH
if not os.path.exists(python_exe):
    python_exe = shutil.which("python")

    if python_exe:
        print(f"Используется системный интерпретатор Python: {python_exe}")
    else:
        print("Интерпретатор Python не найден.")
        exit(1)
else:
    print(f"Используется интерпретатор Python из виртуальной среды: {python_exe}")

# Определяем путь к main.py
main_py = os.path.join(current_dir, "main.py")

# Проверяем, существует ли main.py
if not os.path.exists(main_py):
    print(f"Файл main.py не найден в {current_dir}.")
    exit(1)

# Создаем команду для планировщика задач, запускать каждые 3 минуты
task_name = "RunMainPyEvery3Minutes"
command = f'schtasks /create /tn "{task_name}" /tr "{python_exe} {main_py}" /sc minute /mo 3 /f'

# Выполнение команды для создания задачи
try:
    subprocess.run(command, check=True, shell=True)
    print(
        f"Задача '{task_name}' успешно добавлена в Планировщик задач для запуска main.py каждые 3 минуты."
    )
except subprocess.CalledProcessError as e:
    print(f"Ошибка при добавлении задачи в Планировщик задач: {e}")
