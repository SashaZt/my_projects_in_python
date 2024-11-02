import psycopg2
from psycopg2 import sql
import pandas as pd
from pathlib import Path
from configuration.logger_setup import logger
import os

data_directory = Path.cwd() / "data"
edrpou_csv_file = data_directory / "edrpou.csv"
output_csv_file = data_directory / "output.csv"


class DataVerification:
    def __init__(self, conn_pool):
        self.conn_pool = conn_pool

    def export_edrpou_to_csv(self, table_name="ua_region_com_ua"):
        # Извлечение столбца "Код ЄДРПОУ" из БД и запись в edrpou.csv
        try:
            conn = self.conn_pool.getconn()
            with conn.cursor() as cursor:
                query = sql.SQL('SELECT DISTINCT "Код ЄДРПОУ" FROM {};').format(
                    sql.Identifier(table_name)
                )
                cursor.execute(query)
                edrpou_data = cursor.fetchall()

            # Создание DataFrame и сохранение в CSV
            edrpou_df = pd.DataFrame(edrpou_data, columns=["edrpou"])
            edrpou_df.to_csv(edrpou_csv_file, index=False)
            logger.info(f"Данные успешно экспортированы в файл {edrpou_csv_file}")
        except Exception as e:
            logger.error(f"Ошибка при экспорте данных из БД: {e}")
        finally:
            self.conn_pool.putconn(conn)

    def verify_and_update_output(self):
        # Загрузка данных из edrpou.csv
        if not edrpou_csv_file.exists():
            logger.error(f"Файл {edrpou_csv_file} не найден.")
            return

        edrpou_df = pd.read_csv(edrpou_csv_file)
        edrpou_set = set(edrpou_df["edrpou"].astype(str))

        # Загрузка данных из output.csv
        if not output_csv_file.exists():
            logger.error(f"Файл {output_csv_file} не найден.")
            return

        output_df = pd.read_csv(output_csv_file)

        # Проверка наличия столбца "url"
        if "url" not in output_df.columns:
            logger.error("Отсутствует столбец 'url' в файле output.csv.")
            return

        # Извлечение идентификатора из URL и удаление совпадающих строк
        output_df["id"] = output_df["url"].apply(
            lambda x: x.split("/")[-1]
        )  # Получаем идентификатор из URL
        initial_count = len(output_df)
        output_df = output_df[~output_df["id"].isin(edrpou_set)]
        final_count = len(output_df)

        # Сохранение обновленного output.csv без удаленных строк
        output_df.drop(columns=["id"], inplace=True)  # Удаляем временную колонку "id"
        output_df.to_csv(output_csv_file, index=False)
        logger.info(
            f"Удалено {initial_count - final_count} записей из файла {output_csv_file}"
        )
