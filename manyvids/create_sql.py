"""Код для создания БД в MySql"""
import mysql.connector

from config import db_config, use_bd, use_table_daily_sales, use_table_monthly_sales, use_table_payout_history, \
    use_table_login_pass,use_table_chat,use_table_unique_users


def create_sql_bd():
    def create_sql_login_pass():
        # 1. Подключаемся к серверу MySQL
        cnx = mysql.connector.connect(**db_config)

        # Создаем объект курсора, чтобы выполнять SQL-запросы
        cursor = cnx.cursor()

        # 2. Создаем базу данных с именем kupypai_com
        cursor.execute(f"CREATE DATABASE {use_bd}")


def create_sql_login_pass():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # 2. Создаем базу данных с именем kupypai_com
    # cursor.execute("CREATE DATABASE vpromo2_usa")

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    # 3. В базе данных создаем таблицу ad
    # 4. Создаем необходимые колонки

    cursor.execute(f"""
        CREATE TABLE {use_table_login_pass} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    identifier VARCHAR(255),
                    login VARCHAR(255),
                    pass VARCHAR(255)
                       )
        """)

    cnx.close()


def create_sql_daily_sales():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # 2. Создаем базу данных с именем kupypai_com
    # cursor.execute("CREATE DATABASE vpromo2_usa")

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    cursor.execute(f"""
        CREATE TABLE {use_table_daily_sales} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    buyer_username VARCHAR(255),
                    model_id VARCHAR(255),
                    buyer_stage_name VARCHAR(255),
                    buyer_user_id VARCHAR(255),
                    title VARCHAR(255),
                    type_content VARCHAR(255),
                    sales_date DATE,
                    sales_time TIME,
                    seller_commission_price VARCHAR(255),
                    mvtoken VARCHAR(255),
                    model_fm  VARCHAR(255)
                       )
        """)

    cnx.close()


def create_sql_monthly_sales():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # 2. Создаем базу данных с именем kupypai_com
    # cursor.execute("CREATE DATABASE vpromo2_usa")

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    cursor.execute(f"""
            CREATE TABLE {use_table_monthly_sales} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        model_id VARCHAR(255),
                        sales_month INT,
                        sales_year INT,
                        total_sum VARCHAR(255),
                        pending_custom float,
                        chat_user int


                        )
            """)

    cnx.close()


def create_sql_payout_history():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    # 4. Создаем необходимые колонки

    cursor.execute(f"""
                CREATE TABLE {use_table_payout_history} (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            model_id VARCHAR(255),
                            payment_date DATE,
                            paid VARCHAR(255)
                            )
                """)
    cnx.close()

def create_sql_chat():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    # 4. Создаем необходимые колонки

    cursor.execute(f"""
                    CREATE TABLE {use_table_chat} (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        msg_last_id INT NOT NULL,
                        user_id INT,
                        sender_id INT,
                        date_part DATE,
                        time_part TIME,
                        UNIQUE (msg_last_id));
                    """)
    cnx.close()

def create_sql_unique_users():
    # 1. Подключаемся к серверу MySQL
    cnx = mysql.connector.connect(**db_config)

    # Создаем объект курсора, чтобы выполнять SQL-запросы
    cursor = cnx.cursor()

    # Указываем, что будем использовать эту базу данных
    cursor.execute(f"USE {use_bd}")

    # 4. Создаем необходимые колонки

    cursor.execute(f"""
                    CREATE TABLE {use_table_unique_users} (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                model_id VARCHAR(255),
                                sales_month INT,
                                chat_user INT
                                )
                    """)
    cnx.close()


if __name__ == '__main__':
    # create_sql_bd()
    create_sql_login_pass()
    create_sql_daily_sales()
    create_sql_monthly_sales()
    create_sql_payout_history()
    create_sql_chat()
    create_sql_unique_users()
