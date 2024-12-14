import requests
from configuration.logger_setup import logger


class TgBot:
    def __init__(self, telegram_token, telegram_chat_ids):
        """
        Конструктор класса TgBot.

        Args:
            telegram_token (str): Токен вашего Telegram-бота.
            telegram_chat_ids (list): Список ID чатов, куда отправлять сообщения.
        """
        self.telegram_token = telegram_token
        self.telegram_chat_ids = telegram_chat_ids

    def send_message(self, message):
        """
        Отправляет сообщение в Telegram чаты через бота.

        Args:
            message (str): Текст сообщения, которое нужно отправить.
        """

        for chat_id in self.telegram_chat_ids:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {"chat_id": chat_id, "text": message}
            try:
                response = requests.post(url, timeout=30, json=payload)
                response.raise_for_status()  # Проверка на успешный HTTP-статус
                logger.info(f"Сообщение успешно отправлено в чат {chat_id}!")
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 400:
                    logger.error(
                        f"Ошибка отправки сообщения: {http_err} | "
                        f"Чат {chat_id} не подписан на бота {self.telegram_token}."
                    )
                else:
                    logger.error(
                        f"Ошибка отправки сообщения в чат {chat_id}: {http_err}"
                    )
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка отправки сообщения в чат {chat_id}: {e}")
