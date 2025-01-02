import json
import os
from math import log

import pandas as pd
from configuration.logger_setup import logger


class Writer:

    def __init__(self, output_json, tg_bot, xlsx_result):
        """
        Конструктор класса Writer.

        Args:
            output_json (str): Путь к JSON-файлу, куда будут сохраняться результаты.
            tg_bot (TgBot): Объект Telegram-бота для отправки сообщений (по умолчанию None).
        """
        self.output_json = output_json
        self.xlsx_result = xlsx_result
        self.tg_bot = tg_bot

    # def save_results_to_json(self, all_results):
    #     """Сохраняет результаты в JSON файл и отправляет сообщение в Telegram.

    #     Args:
    #         all_results (dict): Словарь с результатами, которые необходимо сохранить.

    #     Примечания:
    #         - Данные сохраняются в JSON файл с отступом в 4 пробела и без ASCII экранирования.
    #         - В случае ошибки выводится сообщение в лог и происходит повторное возбуждение исключения.
    #     """
    #     try:
    #         with open(self.output_json, "w", encoding="utf-8") as json_file:
    #             json.dump(all_results, json_file, ensure_ascii=False, indent=4)
    #         logger.info(self.output_json)
    #         # Отправляем сообщение в Telegram, если бот задан
    #         if self.tg_bot:
    #             self.tg_bot.send_message(
    #                 f"Данные успешно сохранены в файл {self.output_json}"
    #             )
    #     except Exception as e:
    #         logger.error(f"Ошибка при сохранении данных в файл {self.output_json}: {e}")
    #         # Отправляем сообщение об ошибке в Telegram
    #         if self.tg_bot:
    #             self.tg_bot.send_message(f"Ошибка при сохранении данных: {e}")
    #         raise

    # def save_json_to_excel(self):
    #     """Сохраняет данные из JSON файла в Excel файл.

    #     Примечания:
    #         - Данные из JSON файла преобразуются в DataFrame и записываются в Excel файл.
    #         - При успешном сохранении JSON файл удаляется.
    #         - В случае ошибки выводится сообщение в лог и происходит повторное возбуждение исключения.
    #     """
    #     try:
    #         with open(self.output_json, "r", encoding="utf-8") as json_file:
    #             data = json.load(json_file)
    #         df = pd.DataFrame(data)
    #         df.to_excel(self.xlsx_result, index=False)

    #         logger.info(f"Данные успешно сохранены в Excel файл {self.xlsx_result}")

    #         self.tg_bot.send_message(
    #             f"Данные успешно сохранены в Excel файл {self.xlsx_result}"
    #         )
    #         # Удаление файла
    #         if os.path.exists(self.xlsx_result):
    #             os.remove(self.output_json)

    #     except Exception as e:
    #         logger.error(
    #             f"Ошибка при сохранении данных в Excel файл {self.xlsx_result}: {e}"
    #         )
    #         self.tg_bot.send_message(
    #             f"Ошибка при сохранении данных в Excel файл {self.xlsx_result}: {e}"
    #         )
    #         raise
    def save_results_to_json(self, all_results):
        """Сохраняет результаты в JSON файл и отправляет сообщение в Telegram."""
        try:
            with open(self.output_json, "w", encoding="utf-8") as json_file:
                json.dump(all_results, json_file, ensure_ascii=False, indent=4)
            logger.info(f"Результаты успешно сохранены в JSON файл: {self.output_json}")
            if self.tg_bot:
                self.tg_bot.send_message(
                    f"Данные успешно сохранены в файл {self.output_json}"
                )
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных в файл {self.output_json}: {e}")
            if self.tg_bot:
                self.tg_bot.send_message(f"Ошибка при сохранении данных: {e}")
            raise

    def save_results_to_excel(self, all_results):
        """Сохраняет данные из списка в Excel файл."""
        try:
            df = pd.DataFrame(all_results)
            df.to_excel(self.xlsx_result, index=False, engine="openpyxl")
            logger.info(
                f"Результаты успешно сохранены в Excel файл: {self.xlsx_result}"
            )
            if self.tg_bot:
                self.tg_bot.send_message(
                    f"Данные успешно сохранены в Excel файл {self.xlsx_result}"
                )
        except Exception as e:
            logger.error(
                f"Ошибка при сохранении данных в Excel файл {self.xlsx_result}: {e}"
            )
            if self.tg_bot:
                self.tg_bot.send_message(f"Ошибка при сохранении данных: {e}")
            raise
