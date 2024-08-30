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
        "PODID": "app0",
        "currency": "EUR",
        "language": "en",
        "cf_clearance": "fFTvUNYvkNDJp6l3Wyc_7pVC.4R9VuWD7eXKgcMapeo-1725012260-1.2.1.1-fK8MkAHBDTjOFRLR295P6vw6yIroW79SC7mAApE1SGf4L8CJIw7642edRNnu3sVUOSj4.25ok2drdOeGW4ENM7a0heJYqUhzTwrDjplxp2Qh.9018vIHeq556DFabpIuu9e1DZRhxktOWgCvnhAcKUUFhTkcwPiQeonyiQtY24MNrs7vtumH6DTPAKOhA2mNQ7fHr85K22HlDqeGULwR9iRbCjyjjLHM44KjoxQguGpbiHRoSKFPcpPqs3nVNgBSgYehfNqqtGOL4ELERmv19Y1fIjdomw_1QeJcmuCQMwkgFqAt1NjV9QoMXngwK_.KnBTO3DrMY723mUwWtORsflQjdUAh.GatFgWxtlGKFkWhqLiXKIAFY0zeJLPcDtZ2Uo2khlBKh_ixAc4lyX6EH8bb66jSV3iaRNDf1.CxscLzTPgM_HiZr_lbVx4G9Dd6",
        "SESSION": "eeda5cc4-e16c-43c4-a1d3-2b221b9a8411.app-0",
        "beforeUnloadTime": "1725012465978",
        "unloadTime": "1725012466123",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        # 'cookie': 'PODID=app0; currency=EUR; language=en; cf_clearance=fFTvUNYvkNDJp6l3Wyc_7pVC.4R9VuWD7eXKgcMapeo-1725012260-1.2.1.1-fK8MkAHBDTjOFRLR295P6vw6yIroW79SC7mAApE1SGf4L8CJIw7642edRNnu3sVUOSj4.25ok2drdOeGW4ENM7a0heJYqUhzTwrDjplxp2Qh.9018vIHeq556DFabpIuu9e1DZRhxktOWgCvnhAcKUUFhTkcwPiQeonyiQtY24MNrs7vtumH6DTPAKOhA2mNQ7fHr85K22HlDqeGULwR9iRbCjyjjLHM44KjoxQguGpbiHRoSKFPcpPqs3nVNgBSgYehfNqqtGOL4ELERmv19Y1fIjdomw_1QeJcmuCQMwkgFqAt1NjV9QoMXngwK_.KnBTO3DrMY723mUwWtORsflQjdUAh.GatFgWxtlGKFkWhqLiXKIAFY0zeJLPcDtZ2Uo2khlBKh_ixAc4lyX6EH8bb66jSV3iaRNDf1.CxscLzTPgM_HiZr_lbVx4G9Dd6; SESSION=eeda5cc4-e16c-43c4-a1d3-2b221b9a8411.app-0; beforeUnloadTime=1725012465978; unloadTime=1725012466123',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-full-version": '"128.0.6613.85"',
        "sec-ch-ua-full-version-list": '"Chromium";v="128.0.6613.85", "Not;A=Brand";v="24.0.0.0", "Google Chrome";v="128.0.6613.85"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"15.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://aleo.com/pl/firma/-abis-sp-z-oo-platforma-zakupowa-abispl-art-biurowe-i-szkolne-warszawa",
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
