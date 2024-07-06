import mysql.connector
from config import (
    db_config,
    database,
)


def check_data_day():
    """
    Функция для получение из БД дневных продажах
    """
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    cursor.execute(
        f"""
        SELECT buyer_user_id, sales_date, sales_time, seller_commission_price FROM {database}.daily_sales;
    """
    )
    data = {(row[0], row[1], row[2], row[3]) for row in cursor.fetchall()}
    cursor.close()
    cnx.close()
    return data
