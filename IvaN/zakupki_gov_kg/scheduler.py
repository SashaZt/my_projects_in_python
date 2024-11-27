import time
import subprocess
import os
import sys

if len(sys.argv) < 2:
    print("Не указан путь к интерпретатору Python.")
    sys.exit(1)

python_exe = sys.argv[1]  # Путь к Python, переданный из .bat файла
print("Запустили планировщик")
# Бесконечный цикл
while True:
    # Запускаем скрипт main_new.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_new_path = os.path.join(current_dir, "main.py")

    process = subprocess.Popen([python_exe, main_new_path])

    # Ожидание 10 минут
    time.sleep(600)

    # Завершаем процесс после 10 минут работы
    process.terminate()
    process.wait()

    # После завершения снова запускаем (возврат к началу цикла)
