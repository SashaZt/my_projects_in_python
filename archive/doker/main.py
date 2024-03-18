import docker
import mysql.connector
import os
import time

# Имя контейнера
container_name = "my-mysql-db"

# Параметры подключения к базе данных
db_config = {
    "user": "user",
    "password": "userpassword",
    "host": "localhost",
    "database": "mydatabase",
    "port": 3307
}

# Создаем клиента Docker
client = docker.from_env()

# Получаем путь к текущей директории, где запущен скрипт
current_dir = os.path.dirname(os.path.realpath(__file__))

# Путь к директории на локальной машине, где будут храниться данные MySQL
local_data_dir = os.path.join(current_dir, "mysql-data")

# Создаем директорию, если она еще не существует
if not os.path.exists(local_data_dir):
    os.makedirs(local_data_dir)

# Пытаемся остановить и удалить существующий контейнер, если он есть
try:
    container = client.containers.get(container_name)
    container.stop()
    container.remove()
    print("Останавливаем и удаляем контейнер...")

    # Ожидаем удаления контейнера
    while True:
        try:
            # Пытаемся получить контейнер
            container = client.containers.get(container_name)
            print("Ожидание завершения удаления контейнера...")
            time.sleep(1)
        except docker.errors.NotFound:
            # Если контейнер не найден, значит, он удален
            print("Контейнер удален")
            break
except docker.errors.NotFound:
    print("Контейнер не найден, продолжаем выполнение скрипта")

# Запускаем новый контейнер MySQL
container = client.containers.run(
    "mysql:latest",
    name=container_name,
    environment={
        "MYSQL_ROOT_PASSWORD": "rootpassword",
        "MYSQL_DATABASE": db_config["database"],
        "MYSQL_USER": db_config["user"],
        "MYSQL_PASSWORD": db_config["password"]
    },
    volumes={local_data_dir: {'bind': '/var/lib/mysql', 'mode': 'rw'}},
    ports={"3306/tcp": db_config["port"]},
    detach=True,
    remove=True
)
print("Контейнер MySQL запущен")

# Ждем запуска MySQL
time.sleep(30)  # Даем MySQL немного времени, чтобы полностью запуститься
# Теперь подключаемся к MySQL и настраиваем пользователя и права
try:
    # Подключаемся с правами root пользователя
    conn = mysql.connector.connect(
        user='root',
        password='rootpassword',
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["database"]
    )
    cursor = conn.cursor()

    # Создаем пользователя и даём ему права на любые действия
    cursor.execute(f"CREATE USER IF NOT EXISTS '{db_config['user']}'@'%' IDENTIFIED BY '{db_config['password']}';")
    cursor.execute(f"GRANT ALL PRIVILEGES ON {db_config['database']}.* TO '{db_config['user']}'@'%';")
    cursor.execute("FLUSH PRIVILEGES;")

    print("Пользователь настроен и готов к подключениям.")
except mysql.connector.Error as err:
    print("Ошибка:", err)
finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
# Подключаемся к базе данных и выполняем какие-либо действия
# ...
