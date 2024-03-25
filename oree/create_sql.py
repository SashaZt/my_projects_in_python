"""Код для создания БД в MySql"""

import mysql.connector
import json
import os
import sys
import time


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
                    sales_date DATE,
                    sales_time TIME,
                    amount_time DECIMAL(10,2),
                    price_time DECIMAL(10,2),
                    delivery_date DATE,
                    delivery_time VARCHAR(5)
                       )
        """
    )

    cnx.close()


if __name__ == "__main__":
    create_sql_oree()
