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
        "ci_session": "a%3A4%3A%7Bs%3A10%3A%5C%22session_id%5C%22%3Bs%3A32%3A%5C%22084dce2dcb7e33677a3da4296925fc9a%5C%22%3Bs%3A10%3A%5C%22ip_address%5C%22%3Bs%3A7%3A%5C%220.0.0.0%5C%22%3Bs%3A10%3A%5C%22user_agent%5C%22%3Bs%3A111%3A%5C%22Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F128.0.0.0+Safari%2F537.36%5C%22%3Bs%3A13%3A%5C%22last_activity%5C%22%3Bi%3A1725004760%3B%7D084104efe43c9d462e911378840e850b",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'ci_session=a%3A4%3A%7Bs%3A10%3A%5C%22session_id%5C%22%3Bs%3A32%3A%5C%22084dce2dcb7e33677a3da4296925fc9a%5C%22%3Bs%3A10%3A%5C%22ip_address%5C%22%3Bs%3A7%3A%5C%220.0.0.0%5C%22%3Bs%3A10%3A%5C%22user_agent%5C%22%3Bs%3A111%3A%5C%22Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F128.0.0.0+Safari%2F537.36%5C%22%3Bs%3A13%3A%5C%22last_activity%5C%22%3Bi%3A1725004760%3B%7D084104efe43c9d462e911378840e850b',
        "DNT": "1",
        "Pragma": "no-cache",
        "Referer": "https://goszakup.gov.kz/ru/announce/index/10791510?tab=documents",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    params = {
        "tab": "protocols",
    }

    response = requests.get(
        "https://goszakup.gov.kz/ru/announce/index/10791510",
        params=params,
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
