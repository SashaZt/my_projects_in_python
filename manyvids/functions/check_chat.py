import mysql.connector
from config import (
    db_config,
    database,
)


def check_chat():
    """
    Функция для получение из БД чатов
    """
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(
        f"""
        SELECT msg_last_id, CONCAT(date_part, ' ', time_part) AS datetime FROM {database}.chat;
    """
    )
    data = {(row[0], row[1]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data
