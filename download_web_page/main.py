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
        "isMobileDevice": "0",
        ".cdneshopsid": "yiJb0XR6wEVzPM+5hYqBBffDR+zZOc+IbKF+C5opvqqWZ7zJ5apz1o+5TQSMJjimh2ciM8mE9M3BuciApQ|003",
        "_ga": "GA1.2.508426758.1725959759",
        "_gid": "GA1.2.1979942024.1725959759",
        "_gat_UA-232962489-1": "1",
        "cf_clearance": "OdPqRpb_EgMk_Ser_weJx7o6.5iswFevi9tH55nmWlc-1725959759-1.2.1.1-CMiZSyC0WFyq_zvNrW1qIr2qrmI69AXPQqjWvig3s0LpEQiJjN90UdhTa.siTdobWtZ8cqD7k6LWAWYVvkHKVzfOKgXTP6ZvL6NHoQwWz2plfCEUnYFkRylgUnnfIuY3E_S0fidDnsDaZLpMrX1Ncg9au5lENrYnqi7eMAn828QkZ31kpVK9ip6NtBgi3qcjF4dndLCWSBcmGxoO8BGhXmiTYg9w0Gveg.jrH15IXza_TKHcDdtBzZ_LhdZ0F8TEN1BStYHIg5nHJhjCu84.hXmcsNfvTYx4OlklFMu75DsUYZeSHVp.4X9TqI6.SrPiJVp7UcUAiNV3MPIRxt4n44BcazBRw_w87NjmOyOThCLZ13JEp5NIrODUAZUR.wO49KR5fyPr4YsLSSYWnD58mw",
        "_clck": "1x3nc8a%7C2%7Cfp2%7C0%7C1714",
        "_clsk": "160g9l0%7C1725959760625%7C1%7C1%7Cw.clarity.ms%2Fcollect",
        "config-message-9a416f1c-aecf-4d89-8458-ad39f3a31671": "hidden",
        "cookieSettings": "granted",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://shop.olekmotocykle.com/acerbis-nowy-towar-2024-02-lampa-przednia-elba-ow,3,1339,192618",
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
    save_path = "sitemap.products.xml.gz"
    url = "https://www.xos.ro/sitemap.products.xml.gz"
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
