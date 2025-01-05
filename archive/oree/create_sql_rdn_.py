"""Код для создания БД в MySql"""

import mysql.connector
import json
import os
import sys
import time
from datetime import datetime, timedelta


def load_connection_to_sql():
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "connection_to_sql.json")
    if not os.path.exists(filename_config):
        print("Нету файла config.json конфигурации!!!!!!!!!!!!!!!!!!!!!!!")
        time.sleep(3)
        sys.exit(1)
    else:
        with open(filename_config, "r") as config_file:
            config = json.load(config_file)

    return config


def create_sql_oree():
    config = load_connection_to_sql()
    db_config = config["db_config"]
    use_bd = db_config["database"]
    use_table = config["other_config"]["use_table"]
    cnx = mysql.connector.connect(**db_config)

    cursor = cnx.cursor()
    cursor.execute(f"USE {use_bd}")
    cursor.execute(
        f"""
        CREATE TABLE {use_table} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    hour INT,
                    delivery_date DATE,
                    price DECIMAL(10,2),
                    sales_volume DECIMAL(10,2),
                    purchase_volume DECIMAL(10,2),
                    declared_sales_volume DECIMAL(10,2),
                    declared_volume_of_purchase DECIMAL(10,2),
                    deficiency_rdn DECIMAL(10,2),
                    hour INT
                       )
        """
    )

    cnx.close()

def add_column_oree():
    config = load_connection_to_sql()
    db_config = config["db_config"]
    use_bd = db_config["database"]
    use_table = config["other_config"]["use_table"]
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    cursor.execute(f"USE {use_bd}")
    add_column_command = f"ALTER TABLE {use_table} ADD COLUMN deficiency_rdn DECIMAL(10,2) NOT NULL"

    # Выполнение команды
    cursor.execute(add_column_command)

    # Не забудьте закрыть курсор и соединение, когда закончите
    cursor.close()
    cnx.close()

def modify_column():
    config = load_connection_to_sql()
    db_config = config["db_config"]
    use_bd = db_config["database"]
    use_table = config["other_config"]["use_table"]
    
    # Установка соединения с базой данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    
    # Выбор базы данных (опционально, если уже указана в db_config)
    cursor.execute(f"USE {use_bd}")
    
    # Команда для изменения типа колонки
    # Замените 'column_name' на имя колонки, которую вы хотите изменить
    modify_column_command = f"ALTER TABLE {use_table} MODIFY COLUMN column_name TIME"
    
    # Выполнение команды
    cursor.execute(modify_column_command)
    
    # Закрытие соединения
    cursor.close()
    cnx.close()

    print(f"Колонка 'column_name' в таблице '{use_table}' успешно изменена на тип TIME.")

if __name__ == "__main__":
    # create_sql_oree()
    add_column_oree()
    # modify_column()
