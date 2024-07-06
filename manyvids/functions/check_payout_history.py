import mysql.connector
from config import (
    db_config,
    database,
)


def check_payout_history():
    """
    Функция для получение из БД истории
    """
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(
        f"""
        SELECT model_id,payment_date,paid  FROM {database}.payout_history;
    """
    )
    data = {(row[0], row[1], row[2]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data
