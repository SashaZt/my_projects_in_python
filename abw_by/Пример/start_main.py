from datetime import datetime
import subprocess
import os
import time

error_count = 0
script_name = 'main.py'

# Определяем текущую директорию, где находится start_main.py
current_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(current_dir, script_name)

while True:
    if os.path.exists(script_path):
        return_code = subprocess.call(['python3.12', script_path], cwd=current_dir)
        if return_code == 200:
            print('Скрипт завершился успешно с кодом 200')
            break
        else:
            error_count += 1
            print(f'Количество ошибок: {error_count}')
            print('Скрипт завершился с ошибкой, перезапускаем')
    else:
        print(f'Файл не найден: {script_path}')
        error_count += 1
        print(f'Количество ошибок: {error_count}')
    
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Текущее время:", current_time)
    
    # Задержка перед повторным запуском
    time.sleep(5)
