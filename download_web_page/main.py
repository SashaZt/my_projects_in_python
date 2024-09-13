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
        "form_key": "7MtDJOzkzcuHmy6c",
        "mage-cache-storage": "{}",
        "mage-cache-storage-section-invalidation": "{}",
        "recently_viewed_product": "{}",
        "recently_viewed_product_previous": "{}",
        "recently_compared_product": "{}",
        "recently_compared_product_previous": "{}",
        "product_data_storage": "{}",
        "mage-messages": "",
        "__zlcmid": "1Nin0vbbCzKn1Ud",
        "PHPSESSID": "mqjbab3a98jo4kgor561lqjc30",
        "form_key": "7MtDJOzkzcuHmy6c",
        "wp_ga4_customerGroup": "NOT%20LOGGED%20IN",
        "mage-cache-sessid": "true",
        "cf_clearance": "hRKdUJSICMdE72WhFjqvYeI.4e8TAT7y8AQKSAm1tVo-1726138367-1.2.1.1-HKdYZzZyxAxVDZViJimOArngckzybxgJlpBztM7YeOo1RamPj.mVzwSMiLVWSQamT106mDpSR.TJHHy.jIqVtshf7YHxkM5rH1wIL2PUxr6PZf2xHaWoP9_mO0G8Eu7G9gLc5nZeELsF2i.DQMzzCqy4kn_RtP6le8k7FrnLjQT9oMQk8YR4dVobGa07AATfqXHQ1kpneTz.x2f4kVsZmvbP7movvP0.XZgzvo4moIQc6fT5KrMyeY17fg0beZjIsUdWiq3YIjLgdxKJyltqsnhV2snoWXpmZ0dCOALk20AGDYPL1PueYCeddeH9YqRPMTfFmx4YhXVym2cetqMUqBeSvJv.8NVEhOTIYuJaMuKaZe_Hh7WRJKC9U5ud9Ia2gBpIDSxi3Yo7fi7yXaa8hqo8f9wsfJLsg1kPkfRVNx4yas3WPizc7XiL3A8eaDpu",
        "private_content_version": "c841d603e43faa40da7b52b5f2a5e92d",
        "section_data_ids": "{}",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded",
        # 'cookie': 'form_key=7MtDJOzkzcuHmy6c; mage-cache-storage={}; mage-cache-storage-section-invalidation={}; recently_viewed_product={}; recently_viewed_product_previous={}; recently_compared_product={}; recently_compared_product_previous={}; product_data_storage={}; mage-messages=; __zlcmid=1Nin0vbbCzKn1Ud; PHPSESSID=mqjbab3a98jo4kgor561lqjc30; form_key=7MtDJOzkzcuHmy6c; wp_ga4_customerGroup=NOT%20LOGGED%20IN; mage-cache-sessid=true; cf_clearance=hRKdUJSICMdE72WhFjqvYeI.4e8TAT7y8AQKSAm1tVo-1726138367-1.2.1.1-HKdYZzZyxAxVDZViJimOArngckzybxgJlpBztM7YeOo1RamPj.mVzwSMiLVWSQamT106mDpSR.TJHHy.jIqVtshf7YHxkM5rH1wIL2PUxr6PZf2xHaWoP9_mO0G8Eu7G9gLc5nZeELsF2i.DQMzzCqy4kn_RtP6le8k7FrnLjQT9oMQk8YR4dVobGa07AATfqXHQ1kpneTz.x2f4kVsZmvbP7movvP0.XZgzvo4moIQc6fT5KrMyeY17fg0beZjIsUdWiq3YIjLgdxKJyltqsnhV2snoWXpmZ0dCOALk20AGDYPL1PueYCeddeH9YqRPMTfFmx4YhXVym2cetqMUqBeSvJv.8NVEhOTIYuJaMuKaZe_Hh7WRJKC9U5ud9Ia2gBpIDSxi3Yo7fi7yXaa8hqo8f9wsfJLsg1kPkfRVNx4yas3WPizc7XiL3A8eaDpu; private_content_version=c841d603e43faa40da7b52b5f2a5e92d; section_data_ids={}',
        "dnt": "1",
        "origin": "https://www.govets.com",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://www.govets.com/nc-minerals-066514000011-310-52405891.html?__cf_chl_tk=91VnE3wEK.Ly01B3IzNYSi2WaxdC_zs4n8aRZfSS27o-1726138367-0.0.1.1-5460",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-full-version": '"128.0.6613.121"',
        "sec-ch-ua-full-version-list": '"Chromium";v="128.0.6613.121", "Not;A=Brand";v="24.0.0.0", "Google Chrome";v="128.0.6613.121"',
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

    response = requests.post(
        "https://www.govets.com/nc-minerals-066514000011-310-52405891.html",
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
