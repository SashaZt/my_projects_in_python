import os
from datetime import datetime

# Замените эти значения на соответствующие параметры вашей базы данных
db_name = "btc"
backup_dir = "/home/binance/backup/"

# Создаем директорию для бэкапов, если она не существует
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

# Получаем текущую дату для имени файла
current_date = datetime.now().strftime("%Y-%m-%d")

# Формируем имя файла с датой создания
backup_file = f"{backup_dir}{db_name}_backup_{current_date}.sql"

# Команда для создания резервной копии базы данных
backup_command = (
    f"mysqldump --defaults-file=/home/binance/.my.cnf {db_name} > {backup_file}"
)

# Выполнение команды
os.system(backup_command)

print(f"Резервная копия базы данных {db_name} создана в файле {backup_file}")
