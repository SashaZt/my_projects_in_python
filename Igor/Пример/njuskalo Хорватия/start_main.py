from datetime import datetime
import subprocess
import os

error_count = 0

while True:
    return_code = subprocess.call(['py', 'main.py'])
    if return_code == 200:
        print('Скрипт завершился успешно с кодом 200')
        break
    else:
        error_count += 1
        os.system(f'title Количество ошибок: {error_count}')
        print('Скрипт завершился с ошибкой, перезапускаем')
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Текущее время:", current_time)