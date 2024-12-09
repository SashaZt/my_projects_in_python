import requests

# Ваш токен бота
TELEGRAM_TOKEN = "1977008636:AAF6VWrTwOvSGfTPw_xGrRSFBqBvffe-X1I"


def get_chat_id():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print("Ответ от Telegram API:")
        print(data)

        # Поиск chat_id в данных
        for update in data["result"]:
            chat_id = update["message"]["chat"]["id"]
            print(f"Chat ID: {chat_id}")
            return chat_id
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")


if __name__ == "__main__":
    get_chat_id()
