import requests


def send_message(token: str, chat_id: str, message: str):
    """
    Отправляет сообщение в Telegram чат через бота.

    :param token: Токен бота.
    :param chat_id: ID чата, куда отправить сообщение.
    :param message: Текст сообщения.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Проверка на успешный HTTP-статус
        print("Сообщение успешно отправлено!")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки сообщения: {e}")


if __name__ == "__main__":
    # Замените на ваш токен бота и ID чата
    TELEGRAM_TOKEN = "1977008636:AAF6VWrTwOvSGfTPw_xGrRSFBqBvffe-X1I"
    TELEGRAM_CHAT_IDS = ["137555269"]

    # Сообщение, которое нужно отправить
    message_text = "Программа завершена успешно!"

    for TELEGRAM_CHAT_ID in TELEGRAM_CHAT_IDS:
        # Отправка сообщения
        send_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message_text)
