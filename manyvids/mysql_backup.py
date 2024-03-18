import os
import subprocess

from config import host, user, password, database

# Замените следующие значения на актуальные данные для подключения к вашей базе данных
current_directory = os.getcwd()
backup_directory = 'backup'
# Создайте полный путь к папке temp
backup_file_name = "backup.sql"
backup_path = os.path.join(current_directory, backup_directory, backup_file_name)


# Создание команды для запуска mysqldump
command = f'"C:\\Program Files\\MySQL\\MySQL Server 8.2\\bin\\mysqldump.exe" -u {user} -p"{password}" -h {host} {database} > "{backup_path}"'


# Запуск процесса
process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, encoding='utf-8')

process.wait()

print(f"Backup of {database} completed")
