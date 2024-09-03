import requests
import json
import aiohttp
import asyncio
import ssl
import requests
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from configuration.logger_setup import logger


def get_html():
    cookies = {
        "AMCVS_A3995F265DFB8C020A495E71%40AdobeOrg": "1",
        "didomi_token": "eyJ1c2VyX2lkIjoiMTkxYjZjOGYtNzY1NC02OWY0LWFkYzgtOTU2M2I2OWE3NTczIiwiY3JlYXRlZCI6IjIwMjQtMDktMDNUMDc6Mjg6MjkuNTQxWiIsInVwZGF0ZWQiOiIyMDI0LTA5LTAzVDA3OjI4OjMwLjk3OVoiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzpob3RqYXIiLCJjOmdvb2dsZWFuYS00VFhuSmlnUiIsImM6dHJvdml0IiwiYzpicmF6ZSJdfSwicHVycG9zZXMiOnsiZW5hYmxlZCI6WyJnZW9sb2NhdGlvbl9kYXRhIiwiYW5hbHl0aWNzLUhwQkpycks3Il19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFGbUFDQUZrLkFBQUEifQ==",
        "euconsent-v2": "CQEXy8AQEXy8AAHABBENBFFoAP_AAAAAAAAAF5wBQAIAAtABkAFsBeYAAABSUAGAAIKalIAMAAQU1IQAYAAgpqOgAwABBTUJABgACCmo.f_gAAAAAAAAA",
        "jhtAuthToken": "Bearer%20eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3ODQ2NTExMDUwNTkzMTA4IiwiaXAiOiIxOTMuMjQuMjIxLjM0IiwiZXhwIjoxNzI1MzUzODA3LCJpYXQiOjE3MjUzNTAyMDd9.gu59JOp9HHWKCjULXIjscNidz8LoX9f%2BAy8rzGftkAw%3D",
        "AMCV_A3995F265DFB8C020A495E71%40AdobeOrg": "179643557%7CMCIDTS%7C19970%7CMCMID%7C06790549973647704871454466574375462332%7CMCAID%7CNONE%7CMCOPTOUT-1725357407s%7CNONE%7CvVersion%7C5.5.0",
        "datadome": "zpl~f4Z7MhqXBnGCqrMV1MlDw5dpPkNkBA7QRWQAIb~n45JafzJAzTTWQtCf7z_WJ6eFhVgyEz8UddeoweuY_FgcZYhbH6XgBW7aWy8BY7Zf6GthtWRS9WKjmfqov8Nn",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        # 'cookie': 'AMCVS_A3995F265DFB8C020A495E71%40AdobeOrg=1; didomi_token=eyJ1c2VyX2lkIjoiMTkxYjZjOGYtNzY1NC02OWY0LWFkYzgtOTU2M2I2OWE3NTczIiwiY3JlYXRlZCI6IjIwMjQtMDktMDNUMDc6Mjg6MjkuNTQxWiIsInVwZGF0ZWQiOiIyMDI0LTA5LTAzVDA3OjI4OjMwLjk3OVoiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzpob3RqYXIiLCJjOmdvb2dsZWFuYS00VFhuSmlnUiIsImM6dHJvdml0IiwiYzpicmF6ZSJdfSwicHVycG9zZXMiOnsiZW5hYmxlZCI6WyJnZW9sb2NhdGlvbl9kYXRhIiwiYW5hbHl0aWNzLUhwQkpycks3Il19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFGbUFDQUZrLkFBQUEifQ==; euconsent-v2=CQEXy8AQEXy8AAHABBENBFFoAP_AAAAAAAAAF5wBQAIAAtABkAFsBeYAAABSUAGAAIKalIAMAAQU1IQAYAAgpqOgAwABBTUJABgACCmo.f_gAAAAAAAAA; jhtAuthToken=Bearer%20eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3ODQ2NTExMDUwNTkzMTA4IiwiaXAiOiIxOTMuMjQuMjIxLjM0IiwiZXhwIjoxNzI1MzUzODA3LCJpYXQiOjE3MjUzNTAyMDd9.gu59JOp9HHWKCjULXIjscNidz8LoX9f%2BAy8rzGftkAw%3D; AMCV_A3995F265DFB8C020A495E71%40AdobeOrg=179643557%7CMCIDTS%7C19970%7CMCMID%7C06790549973647704871454466574375462332%7CMCAID%7CNONE%7CMCOPTOUT-1725357407s%7CNONE%7CvVersion%7C5.5.0; datadome=zpl~f4Z7MhqXBnGCqrMV1MlDw5dpPkNkBA7QRWQAIb~n45JafzJAzTTWQtCf7z_WJ6eFhVgyEz8UddeoweuY_FgcZYhbH6XgBW7aWy8BY7Zf6GthtWRS9WKjmfqov8Nn',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://www.yaencontre.com/",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://www.yaencontre.com/venta/piso/inmueble-46261-105869332",
        cookies=cookies,
        headers=headers,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    print(response.status_code)


def get_json():
    response = requests.get(
        "https://b.abw.by/api/v2/adverts/1/phones", cookies=cookies, headers=headers
    )

    # Проверка кода ответа
    if response.status_code == 200:
        json_data = response.json()
        # filename = os.path.join(json_path, f"0.json")
        with open("proba.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    else:
        print(response.status_code)


def download_xml():
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }
    save_path = "image_sitemap_00006.xml"
    url = "https://abw.by/sitemap.xml"
    # Отправка GET-запроса на указанный URL
    response = requests.get(url, headers=headers)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


def fetch_and_save():
    url = "https://www.bizcaf.ro/"
    headers = {
        "DNT": "1",
        "Referer": "https://www.bizcaf.ro/foisor-patrat-cu-masa-si-banci-tip-picnic-rexal-ro_bizcafAd_2321294.dhtml",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    # Создание SSL-контекста с понижением уровня безопасности
    ssl_context = ssl.create_default_context()
    ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")

    # Создание сессии requests с использованием адаптера SSL
    session = requests.Session()
    adapter = SSLAdapter(ssl_context=ssl_context)
    session.mount("https://", adapter)

    try:
        # Выполнение запроса
        response = session.get(url, headers=headers)

        # Проверка успешности запроса
        if response.status_code == 200:
            # Сохранение содержимого в файл
            with open("response_content.html", "w", encoding="utf-8") as file:
                file.write(response.text)
            print("Контент успешно сохранен в 'response_content.html'.")
        else:
            print(f"Ошибка: код ответа {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Произошла ошибка при выполнении запроса: {e}")


if __name__ == "__main__":
    get_html()
    # get_json()
    # download_xml()
    # fetch_and_save()
