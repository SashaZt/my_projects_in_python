import json

from configuration.logger_setup import logger


class Writer:
    def __init__(self, output_json, tg_bot):
        """
        Конструктор класса Writer.

        Args:
            output_json (str): Путь к JSON-файлу, куда будут сохраняться результаты.
            tg_bot (TgBot): Объект Telegram-бота для отправки сообщений (по умолчанию None).
        """
        self.output_json = output_json
        self.tg_bot = tg_bot  # Telegram-бот для отправки сообщений (опционально)

    def save_results_to_json(self, all_results, tg_bot):
        """Сохраняет результаты в JSON файл и отправляет сообщение в Telegram.

        Args:
            all_results (dict): Словарь с результатами, которые необходимо сохранить.

        Примечания:
            - Данные сохраняются в JSON файл с отступом в 4 пробела и без ASCII экранирования.
            - В случае ошибки выводится сообщение в лог и происходит повторное возбуждение исключения.
        """
        try:
            with open(self.output_json, "w", encoding="utf-8") as json_file:
                json.dump(all_results, json_file, ensure_ascii=False, indent=4)
            # Отправляем сообщение в Telegram, если бот задан
            if self.tg_bot:
                self.tg_bot.send_message(
                    f"Данные успешно сохранены в файл {self.output_json}"
                )
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных в файл {self.output_json}: {e}")
            # Отправляем сообщение об ошибке в Telegram
            if self.tg_bot:
                self.tg_bot.send_message(f"Ошибка при сохранении данных: {e}")
            raise
