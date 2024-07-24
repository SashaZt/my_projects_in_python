import asyncio
import websockets
from websockets.exceptions import InvalidStatusCode


async def connect_to_websocket(ws_url):
    headers = {
        "Pragma": "no-cache",
        "Origin": "https://bandit.camp",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Sec-WebSocket-Key": "s/ik/rkXAzLFGMIQ+DhQDw==",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Upgrade": "websocket",
        "Cache-Control": "no-cache",
        "Connection": "Upgrade",
        "Sec-WebSocket-Version": "13",
        "Sec-WebSocket-Extensions": "permessage-deflate; client_max_window_bits",
    }

    try:
        # Устанавливаем соединение с WebSocket сервером напрямую с дополнительными заголовками
        async with websockets.connect(
            ws_url, extra_headers=headers, open_timeout=10
        ) as websocket:
            print("Connected to WebSocket directly")
            # Здесь можно выполнять дальнейшие работы
            await websocket.send("Hello WebSocket!")
            response = await websocket.recv()
            print(f"Received: {response}")
    except InvalidStatusCode as e:
        print(f"Failed to connect to WebSocket directly: {e.status_code}")
    except asyncio.TimeoutError:
        print("Direct connection to WebSocket timed out")
    except Exception as e:
        print(f"An error occurred during direct connection: {str(e)}")


# Замените URL-адрес WebSocket на ваш собственный
ws_url = "wss://api.bandit.camp/"

# Используем новый метод для запуска asyncio
asyncio.run(connect_to_websocket(ws_url))
