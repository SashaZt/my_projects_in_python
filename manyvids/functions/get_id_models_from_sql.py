import mysql.connector
from config import (
    db_config,
    database,
)


def get_id_models_from_sql():
    """
    Функция для получения данных с Mysql
    """
    # Подключение к базе данных
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()

    # Выполнение запроса для получения уникальных значений
    cursor.execute(f"SELECT DISTINCT model_fm, model_id FROM {database}.daily_sales")

    dict_models = {}
    # Получение и вывод результатов
    results = cursor.fetchall()
    for row in results:
        model_id, mvtoken = row
        dict_models[model_id] = mvtoken
    # Закрытие курсора и соединения
    cursor.close()
    cnx.close()
    return dict_models
