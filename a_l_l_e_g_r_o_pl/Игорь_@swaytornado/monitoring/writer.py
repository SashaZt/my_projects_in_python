import json

from configuration.logger_setup import logger


class Writer:

    def __init__(self, output_json):
        self.output_json = output_json

    def save_results_to_json(self, all_results):
        """Сохраняет результаты в JSON файл.

        Args:
            all_results (dict): Словарь с результатами, которые необходимо сохранить.

        Примечания:
            - Данные сохраняются в JSON файл с отступом в 4 пробела и без ASCII экранирования.
            - В случае ошибки выводится сообщение в лог и происходит повторное возбуждение исключения.
        """
        try:
            with open(self.output_json, "w", encoding="utf-8") as json_file:
                json.dump(all_results, json_file, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных в файл {self.json_result}: {e}")
            raise
