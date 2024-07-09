from collections import defaultdict
import mysql.connector
from config import (
    db_config,
)
import pandas as pd
from functions.get_id_models_from_sql import get_id_models

import pandas as pd


def unique_users_to_sql():
    """
    Функция для загрузки данных об уникальных клиентах
    """
    # # Подключение к базе данных
    cnx = mysql.connector.connect(
        **db_config
    )  # Замените db_config на ваш конфигурационный словарь
    cursor = cnx.cursor()

    # Выполнение SQL запроса для получения данных
    query = """
            SELECT sender_id, EXTRACT(MONTH FROM date_part) AS month, user_id
            FROM chat
            ORDER BY sender_id, month;
            """
    cursor.execute(query)

    # Считывание данных в DataFrame
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["sender_id", "month", "user_id"])

    # Группировка по sender_id и месяцу, подсчет уникальных user_id
    grouped = (
        df.groupby(["sender_id", "month"])["user_id"]
        .apply(lambda x: set(x))
        .reset_index(name="unique_users")
    )

    # Подготовка структуры для хранения результатов
    sender_monthly_new_users = defaultdict(dict)

    # Вычисление новых уникальных user_id для каждого sender_id по месяцам
    for sender_id, group in grouped.groupby("sender_id"):
        all_previous_users = set()
        for _, row in group.iterrows():
            month, unique_users = row["month"], row["unique_users"]
            new_users = unique_users - all_previous_users
            sender_monthly_new_users[sender_id][month] = len(new_users)
            all_previous_users.update(new_users)
    #
    # # Преобразование результатов в DataFrame для удобного отображения
    results = []
    for sender_id, months in sender_monthly_new_users.items():
        for month, new_users_count in months.items():
            # Добавляем префикс к названию месяца
            month_prefixed = f"sales_month_{month}"
            results.append({"sender_id": sender_id, month_prefixed: new_users_count})

    # Создание DataFrame из списка результатов
    results_df = pd.DataFrame(results)

    # Поскольку каждая строка теперь представляет отдельный месяц, необходимо агрегировать данные по sender_id
    pivot_df = pd.pivot_table(results_df, index="sender_id", aggfunc="sum").fillna(0)

    # Сохранение в CSV
    pivot_df.to_csv("monthly_new_unique_users.csv", index=True)

    cursor.close()
    cnx.close()

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    df = pd.read_csv("monthly_new_unique_users.csv")

    # Загрузка словаря id_models
    id_models = get_id_models()  # {'FM05': '1007686262', ...}

    df["sender_id"] = df["sender_id"].astype(
        str
    )  # Убедимся, что sender_id в строковом формате
    df["model_id"] = df["sender_id"].apply(
        lambda x: (
            [k for k, v in id_models.items() if v == x][0]
            if x in id_models.values()
            else None
        )
    )
    df["model_id"].fillna(0, inplace=True)

    # Удаление колонки sender_id
    df.drop(columns=["sender_id"], inplace=True)

    # Проверяем DataFrame после изменений
    df_long = df.melt(id_vars=["model_id"], var_name="month", value_name="chat_users")

    # Удаление строк, где model_id равно 0 (если это необходимо)
    df_long = df_long[df_long["model_id"] != 0]

    # Преобразование длинного DataFrame обратно в широкий формат с model_id в качестве строк, месяцев в качестве колонок и chat_users в качестве значений
    df_pivot = df_long.pivot(index="model_id", columns="month", values="chat_users")

    # Заполнение NaN нулями, если это необходимо
    df_pivot.fillna(0, inplace=True)
    # log_message(df_pivot)
    # Проверяем результат преобразования
    for index, row in df_long.iterrows():
        model_id = row["model_id"]
        sales_month = int(
            row["month"].replace("sales_month_", "")
        )  # Преобразование в int
        chat_users = row["chat_users"]

        # Формирование и выполнение SQL-запроса на обновление # UPDATE monthly_sales
        # Формирование и выполнение SQL-запроса на вставку с условием обновления при дубликате
        upsert_query = """
            INSERT INTO unique_users (model_id, sales_month, chat_user)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE chat_user = VALUES(chat_user);
        """
        cursor.execute(upsert_query, (model_id, sales_month, chat_users))

    # # Подтверждение изменений и закрытие подключения
    cnx.commit()
    update_query = """
        UPDATE monthly_sales m
        JOIN unique_users u ON m.model_id = u.model_id AND m.sales_month = u.sales_month
        SET m.chat_user = u.chat_user;
    """

    cursor.execute(update_query)
    cnx.commit()
    cursor.close()
    cnx.close()
