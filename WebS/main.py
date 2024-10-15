import requests
import websocket
from requests.auth import HTTPBasicAuth
from loguru import logger
import base64

# Метод 1: REST API через requests
base_url = "http://62.149.25.79:8088/asterisk"
username = "user_help"
password = "kEPXKK1IKzfa49Ex"

def get_asterisk_info():
    try:
        # Логируем начало отправки запроса к REST API
        logger.info("Отправка запроса к REST API для получения информации о Asterisk")
        # Выполняем GET-запрос к API с использованием базовой аутентификации
        response = requests.get(f"{base_url}/ari/asterisk/info", auth=HTTPBasicAuth(username, password))
        # Проверяем статус ответа; если не успешный, будет вызвано исключение
        response.raise_for_status()
        # Логируем успешный ответ
        logger.info("Ответ от REST API получен успешно")
        # Логируем детали ответа для отладки
        logger.debug(f"Ответ: {response.json()}")
    except requests.exceptions.RequestException as e:
        # Логируем ошибку, если запрос не удался
        logger.error(f"Ошибка при вызове REST API: {e}")

# Вызов метода для получения информации
get_asterisk_info()

# Метод 2: WebSocket через websocket-client
# Формируем URL для подключения к WebSocket
ws_url = f"ws://62.149.25.79:8088/asterisk/ari/events?app=my_app"

def on_message(ws, message):
    # Логируем получение сообщения через WebSocket
    logger.info("Получено сообщение через WebSocket")
    # Логируем детали сообщения для отладки
    logger.debug(f"Сообщение: {message}")

def on_error(ws, error):
    # Логируем ошибку, если она произошла в WebSocket соединении
    logger.error(f"Ошибка в WebSocket: {error}")

def on_close(ws, close_status_code, close_msg):
    # Логируем закрытие WebSocket соединения
    logger.warning("Соединение WebSocket закрыто")

def on_open(ws):
    # Логируем успешное установление WebSocket соединения
    logger.info("Соединение WebSocket установлено")

# Создание и подключение WebSocket клиента
logger.info("Подключение к WebSocket для получения событий Asterisk")
# Создаем WebSocket клиент и передаем заголовок авторизации
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode()).decode("utf-8")
headers = [
    f"Authorization: Basic {encoded_credentials}",
    "Origin: http://62.149.25.79:8088"
]

ws = websocket.WebSocketApp(ws_url,
                            header=headers,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
# Устанавливаем функцию для обработки события успешного подключения
ws.on_open = on_open

# Запуск WebSocket клиента
# Запускаем WebSocket клиента в бесконечном цикле для прослушивания событий
ws.run_forever()