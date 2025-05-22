#!/usr/bin/env python3
"""
Webhook-сервер для Docker
"""

import asyncio
import http.server
import json
import logging
import os
import socketserver
from datetime import datetime

import aiohttp

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],  # Логи идут в stdout для Docker
)
logger = logging.getLogger("webhook_server")

PORT = 8080
WEBHOOK_DATA_DIR = "/data"
CLIENT_API_URL = os.getenv("CLIENT_API_URL", "http://client:8081/api/stream")

os.makedirs(WEBHOOK_DATA_DIR, exist_ok=True)


async def forward_to_client(data):
    """Пересылает данные в API клиента"""
    try:
        async with aiohttp.ClientSession() as session:
            logger.info(f"Пересылаем данные в клиент: {CLIENT_API_URL}")
            async with session.post(CLIENT_API_URL, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Успешный ответ от клиента: {result}")
                    return {"success": True, "client_response": result}
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка от клиента: {response.status} - {error_text}")
                    return {
                        "success": False,
                        "error": f"Клиент вернул ошибку: {response.status}",
                        "details": error_text,
                    }
    except Exception as e:
        logger.error(f"Не удалось переслать данные в клиент: {e}")
        return {"success": False, "error": str(e)}


class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            logger.info(
                f"Получен POST-запрос от {self.client_address} на путь: {self.path}"
            )
            logger.info(f"Заголовки: {dict(self.headers)}")

            content_length = int(self.headers.get("Content-Length", 0))
            logger.info(f"Content-Length: {content_length}")

            client_response = None
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                logger.info(f"Получено {len(post_data)} байт данных")

                # Сохраняем в файл
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                log_file = os.path.join(WEBHOOK_DATA_DIR, f"webhook_{timestamp}.json")

                try:
                    json_data = json.loads(post_data)
                    logger.info(f"JSON данные: {json.dumps(json_data, indent=2)}")
                    with open(log_file, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4)

                    # Пересылаем данные в клиент
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    client_response = loop.run_until_complete(
                        forward_to_client(json_data)
                    )
                    loop.close()
                except json.JSONDecodeError:
                    logger.warning(f"Данные не в формате JSON")
                    raw_file = os.path.join(
                        WEBHOOK_DATA_DIR, f"webhook_{timestamp}.raw"
                    )
                    with open(raw_file, "wb") as f:
                        f.write(post_data)
                    log_file = raw_file

                logger.info(f"Данные сохранены в {log_file}")
            else:
                logger.warning("Получен POST без тела")

            # Отправляем ответ
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            response_data = {
                "status": "ok",
                "received": True,
                "timestamp": datetime.now().isoformat(),
            }

            # Добавляем ответ от клиента, если он есть
            if client_response:
                response_data["forwarded"] = client_response

                # Проверяем на наличие ошибок от клиента
                if client_response.get("success") == False:
                    response_data["warning"] = "Ошибка при обработке клиентом"
                    logger.warning(
                        f"Клиент вернул ошибку: {client_response.get('error')}"
                    )

            response = json.dumps(response_data)
            self.wfile.write(response.encode())
            logger.info("Отправлен успешный ответ 200 OK")

        except Exception as e:
            logger.error(f"Ошибка обработки запроса: {e}")
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_response = json.dumps({"status": "error", "message": str(e)})
            self.wfile.write(error_response.encode())

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_OPTIONS(self):
        logger.info(
            f"Получен OPTIONS-запрос от {self.client_address} на путь: {self.path}"
        )
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        logger.info("Отправлен ответ на OPTIONS")

    def do_GET(self):
        logger.info(f"Получен GET-запрос от {self.client_address} на путь: {self.path}")
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Webhook Server</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #333; }}
                .status {{ padding: 20px; background-color: #f0f0f0; border-radius: 5px; }}
                .success {{ color: green; }}
            </style>
        </head>
        <body>
            <h1>Webhook Server</h1>
            <div class="status">
                <p class="success">✅ Сервер активен и работает в Docker</p>
                <p>Время сервера: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>Путь запроса: <code>{self.path}</code></p>
                <p>Client API URL: <code>{CLIENT_API_URL}</code></p>
            </div>
            <h2>Информация:</h2>
            <ul>
                <li>Webhook URL: <code>https://{self.headers.get('Host', 'ваш-домен.com')}/webhook</code></li>
                <li>Данные сохраняются в контейнере</li>
                <li>Данные пересылаются в клиент для обработки</li>
            </ul>
        </body>
        </html>
        """

        self.wfile.write(html.encode())
        logger.info("Отправлена статусная страница")

    def log_message(self, format, *args):
        # Переопределяем встроенный метод логирования
        logger.info(f"{self.client_address[0]} - {args[0]}")


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Многопоточный HTTP-сервер"""

    daemon_threads = True
    allow_reuse_address = True


def run_server():
    try:
        server = ThreadedHTTPServer(("0.0.0.0", PORT), WebhookHandler)
        logger.info("\n=====================")
        logger.info(" Webhook Server Started ")
        logger.info("=====================")
        logger.info(f"Слушаем на порту {PORT}")
        logger.info(f"Данные сохраняются в {WEBHOOK_DATA_DIR}")
        logger.info(f"Client API URL: {CLIENT_API_URL}")
        logger.info("=====================\n")

        # Запускаем сервер
        server.serve_forever()

    except KeyboardInterrupt:
        logger.info("\nПолучен сигнал прерывания, завершаем работу...")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")


if __name__ == "__main__":
    run_server()
