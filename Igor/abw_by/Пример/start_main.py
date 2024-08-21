from datetime import datetime
import subprocess
import os
import time

# Инициализация счетчика ошибок
error_count = 0
# Имя скрипта, который будет запускаться
script_name = "main.py"

# Определяем текущую директорию, где находится start_main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
# Определяем полный путь к скрипту main.py
script_path = os.path.join(current_dir, script_name)

# Бесконечный цикл, который будет выполняться до тех пор, пока скрипт не завершится успешно
while True:
    # Проверка, существует ли файл скрипта
    if os.path.exists(script_path):
        # Запуск скрипта main.py с использованием Python версии 3.12
        return_code = subprocess.call(["python3.12", script_path], cwd=current_dir)
        # Если скрипт завершился успешно с кодом 200, выходим из цикла
        if return_code == 200:
            print("Скрипт завершился успешно с кодом 200")
            break
        else:
            # Увеличиваем счетчик ошибок и выводим сообщение об ошибке
            error_count += 1
            print(f"Количество ошибок: {error_count}")
            print("Скрипт завершился с ошибкой, перезапускаем")
    else:
        # Если файл не найден, выводим сообщение и увеличиваем счетчик ошибок
        print(f"Файл не найден: {script_path}")
        error_count += 1
        print(f"Количество ошибок: {error_count}")

    # Получаем текущее время и выводим его
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Текущее время:", current_time)

    # Задержка перед повторным запуском
    time.sleep(5)
