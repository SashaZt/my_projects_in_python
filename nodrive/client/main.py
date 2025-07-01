import asyncio
import json
import sys

from loguru import logger
from rnet import Client, Impersonate

cookies = {
    "XSRF-TOKEN": "eyJpdiI6IjdxUFRUcDM4VlhzQkdsUWxaZTNKZmc9PSIsInZhbHVlIjoieTN2Wm15VkVZZ25WSGc5R09LcitXTXpnb0R2UUxWK0YxelFsS3c3d05vY2VWSTZ0ZWpZS2FuUmdoOUNIaVhFNXFZR1FJUk16dkUxQlduZTlDU2htWGozRFA3Vk9OWW9sRE1MQ2xpQ3BFdCsyb2ZRVFVQWWcyVmJPeHZpSGxCYXYiLCJtYWMiOiI3MDgxNzI0ODIyNjI2ZDJkZWUyZmI0M2Y4NTlkMTFhZWU1NGVlNTIwYjc4OTQ4Y2IwNzdkYTVlOTA3NjI4Y2U5IiwidGFnIjoiIn0%3D",
    "tikleap_session": "eyJpdiI6IjgvTUFnNE5jcC9PdERCMkJVODlTdmc9PSIsInZhbHVlIjoiVG1lNTU5czBoWUVheFFaNXVocDRhR0lBUkwwWUhYdEwvOGZ5aXFBeEl3NXoxVG00Z2FkWlNMc0NrM1VOelFjL08vUHlRSUpSSTB3QmlrZFVqNDUrQzFhS0NMd25SWDk4NXVINFRNTGNjU3dZSWNmem95bFJsR1pLaHg0dmNyRkUiLCJtYWMiOiI3MGFmNGM3MmIxNGJmNTM2MjI0MDVhODJmOGQ1MmNlMzZjMWQ2Yjg1ZmU0NWVlMzg5YWQ2ZTcwMTQxY2YyYTBiIiwidGFnIjoiIn0%3D",
}

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=1, i",
    "referer": "https://www.tikleap.com/country/kz",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}

logger.remove()

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


async def response_methods():
    client = Client(impersonate=Impersonate.Chrome137)

    response = await client.get(
        "https://www.tikleap.com/country-load-more/kz/1",
        cookies=cookies,
        headers=headers,
    )

    logger.info(f"Status Code: {response.status_code}")
    try:
        text_content = await response.json()
        with open("file_name.json", "w", encoding="utf-8") as f:
            json.dump(text_content, f, ensure_ascii=False, indent=4)
        return text_content
    except Exception as e:
        logger.error(f"❌ response.text() ошибка: {e}")

    return None


if __name__ == "__main__":
    asyncio.run(response_methods())
