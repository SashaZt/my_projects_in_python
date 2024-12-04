import json
import os
import shutil

import pandas as pd
from configuration.logger_setup import logger


class Writer:

    def __init__(self, csv_output_file, json_result, xlsx_result):
        self.csv_output_file = csv_output_file
        self.json_result = json_result
        self.xlsx_result = xlsx_result

    def save_to_csv(self, href_set):
        """Сохраняет множество ссылок в CSV-файл.

        Args:
            href_set (set): Множество URL-адресов, которые необходимо сохранить.

        Примечания:
            - Ссылки сохраняются в CSV-файл с одной колонкой "url".
            - Кодировка файла: UTF-8.
        """
        df = pd.DataFrame(list(href_set), columns=["url"])
        df.to_csv(self.csv_output_file, index=False, encoding="utf-8")

        logger.info(f"Данные успешно сохранены в {self.csv_output_file}")

    def save_results_to_json(self, all_results):
        """Сохраняет результаты в JSON файл.

        Args:
            all_results (dict): Словарь с результатами, которые необходимо сохранить.

        Примечания:
            - Данные сохраняются в JSON файл с отступом в 4 пробела и без ASCII экранирования.
            - В случае ошибки выводится сообщение в лог и происходит повторное возбуждение исключения.
        """
        try:
            with open(self.json_result, "w", encoding="utf-8") as json_file:
                json.dump(all_results, json_file, ensure_ascii=False, indent=4)
            # shutil.rmtree(self.json_files_directory)
            # logger.info(f"Данные успешно сохранены в файл {self.json_result}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных в файл {self.json_result}: {e}")
            raise

    def save_json_to_excel(self):
        """Сохраняет данные из JSON файла в Excel файл.

        Примечания:
            - Данные из JSON файла преобразуются в DataFrame и записываются в Excel файл.
            - При успешном сохранении JSON файл удаляется.
            - В случае ошибки выводится сообщение в лог и происходит повторное возбуждение исключения.
        """
        try:
            with open(self.json_result, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
            df = pd.DataFrame(data)
            df.to_excel(self.xlsx_result, index=False)
            logger.info(f"Данные успешно сохранены в Excel файл {self.xlsx_result}")
            # Удаление файла
            if os.path.exists(self.xlsx_result):
                os.remove(self.json_result)

        except Exception as e:
            logger.error(
                f"Ошибка при сохранении данных в Excel файл {self.xlsx_result}: {e}"
            )
            raise
