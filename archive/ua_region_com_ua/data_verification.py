import os
from pathlib import Path

import pandas as pd
import psycopg2
from configuration.logger_setup import logger
from psycopg2 import sql

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

                # Создание DataFrame с очисткой данных
                edrpou_df = pd.DataFrame(edrpou_data, columns=["edrpou"])
                edrpou_df["edrpou"] = edrpou_df["edrpou"].astype(
                    str).str.replace(",", "").str.strip()

                # Сохранение очищенных данных в CSV
                edrpou_df.to_csv(edrpou_csv_file, index=False)
                logger.info(f"Данные успешно экспортированы в файл {
                            edrpou_csv_file}")
        except Exception as e:
            logger.error(f"Ошибка при экспорте данных из БД: {e}")
        finally:
            self.conn_pool.putconn(conn)

    def verify_and_update_output(self):
        # Проверка наличия файла edrpou.csv
        if not edrpou_csv_file.exists():
            logger.error(f"Файл {edrpou_csv_file} не найден.")
            return

        # Загрузка и очистка данных из edrpou.csv с сохранением ведущих нулей
        edrpou_df = pd.read_csv(edrpou_csv_file, dtype={"edrpou": str})
        # Убираем только пробелы
        edrpou_df["edrpou"] = edrpou_df["edrpou"].str.strip()
        edrpou_set = set(edrpou_df["edrpou"])

        # Проверка наличия файла output.csv
        if not output_csv_file.exists():
            logger.error(f"Файл {output_csv_file} не найден.")
            return

        # Загрузка данных из output.csv
        output_df = pd.read_csv(output_csv_file)

        # Проверка наличия столбца 'url'
        if "url" not in output_df.columns:
            logger.error("Отсутствует столбец 'url' в файле output.csv.")
            return

        # Очистка и извлечение идентификаторов из URL
        output_df["id"] = output_df["url"].str.replace(
            "https://www.ua-region.com.ua/", "", regex=False).str.strip()

        # Фильтрация: Оставляем только строки, у которых id отсутствует в edrpou_set
        initial_count = len(output_df)
        output_df = output_df[~output_df["id"].isin(edrpou_set)]
        final_count = len(output_df)

        # Удаляем временную колонку 'id', сохраняя полный URL
        output_df.drop(columns=["id"], inplace=True)
        output_df.to_csv(output_csv_file, index=False)

        logger.info(
            f"Удалено {initial_count -
                       final_count} записей из файла {output_csv_file}"
        )
