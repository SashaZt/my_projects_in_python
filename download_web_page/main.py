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
        "nuka-fp": "e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79",
        "login_2fa": "e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79",
        "__uzma": "8319a3d2-e332-4445-a1ea-7de538d8368d",
        "__uzmb": "1724935081",
        "__uzme": "5674",
        "njuskalo_privacy_policy": "12",
        "didomi_token": "eyJ1c2VyX2lkIjoiMTkxOWUyNDgtZDkwOS02ZTZhLTlmNWQtOTExZDM4YTRjMDQzIiwiY3JlYXRlZCI6IjIwMjQtMDgtMjlUMTI6Mzg6MDEuMzYwWiIsInVwZGF0ZWQiOiIyMDI0LTA4LTI5VDEyOjM4OjAyLjYyMloiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYW1hem9uIiwiYzppbnRvd293aW4tcWF6dDV0R2kiLCJjOmhvdGphciIsImM6bmV3LXJlbGljIiwiYzpjb21tMTAwIiwiYzpsaXZlY2hhdCIsImM6Ym9va2l0c2gtS2I4bmJBRGgiLCJjOmNvbW0xMDB2aS13ZG1NbTRKNiIsImM6Ym9va2l0bGEtTWFSZ2dtUE4iLCJjOmRvdG1ldHJpYy1nYjJmaktDSiIsImM6c3R5cmlhLXFoVWNra1plIiwiYzppc2xvbmxpbmUtRjlHQmdwUWgiLCJjOnhpdGktQjN3Ym5KS1IiLCJjOmV0YXJnZXQtV3dFakFRM0ciLCJjOmdvb2dsZWFuYS0yM2RkY3JEaCIsImM6bnVrYXJlY29tLXdra0JkcU04IiwiYzptaWRhcy1lQm5UR1hMRiIsImM6Z29vZ2xlYW5hLTRUWG5KaWdSIiwiYzpwaWFub2h5YnItUjNWS0MycjQiLCJjOnBpbnRlcmVzdCIsImM6dGVsdW0ta3c0RG1wUGsiLCJjOmdlbWl1c3NhLW1ja2lRYW5LIiwiYzppbnN1cmFkcy1KZ0NGNnBtWCIsImM6aG90amFyLVpMUExleFZiIiwiYzpnb29nbGVhbmEtOGlIR1JDdFUiLCJjOm9wdGltYXhtZS1OSFhlUWNDayIsImM6ZGlkb21pLW5rR2pHZHhqIiwiYzpzbWFydGFkc2UtN1dNOFhnVEYiLCJjOmNyaXRlb3NhLWdqcGNybWdCIiwiYzpnb29nbGVhZHYtWlo5ZTdZZGkiLCJjOm5qdXNrYWxvbi1BWWNOTmFpdyIsImM6Ymlkc3dpdGNoLUV0YjdMYTRSIiwiYzphZGFnaW8tRllnZjR3UkQiLCJjOm5qdXNrYWxvbi1BN2NQVmVFYSIsImM6YW1hem9uYWQtQzJ5bk5VbjkiLCJjOnlhaG9vYWRlLW1SSFFraG1VIiwiYzptZHByaW1pcy1XTVpBUm13NiIsImM6YW1hem9uLUw4NHRKUXg0IiwiYzpkaWRvbWkiXX0sInB1cnBvc2VzIjp7ImVuYWJsZWQiOlsiZGV2aWNlX2NoYXJhY3RlcmlzdGljcyIsImdlb2xvY2F0aW9uX2RhdGEiLCJvZ2xhc2l2YWNrLVE0RDlibVRHIiwiYXVkaWVuY2VtLWhKeGFlR3JSIiwiYW5hbHl0aWNzLXhHSHhHcFRMIl19LCJ2ZW5kb3JzX2xpIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzpib3hub3dkLTN4TmlKamZCIl19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFrdUFFQUZrQkpZQS5Ba3VBRUFGa0JKWUEifQ==",
        "euconsent-v2": "CQEHUQAQEHUQAAHABBENBDFsAP_gAEPgAAAAKYtV_G__bWlr8X73aftkeY1P9_h77sQxBhfJE-4FzLvW_JwXx2ExNA36tqIKmRIAu3bBIQNlGJDUTVCgaogVryDMak2coTNKJ6BkiFMRe2dYCF5vmwtj-QKY5vr991dx2B-t7dr83dzyz4VHn3a5_2a0WJCdA5-tDfv9bROb-9IOd_x8v4v8_F_rE2_eT1l_tevp7D9-cts7_XW-9_fff79Ln_-uB_--Cl4BJhoVEAZYEhIQaBhBAgBUFYQEUCAAAAEgaICAEwYFOwMAl1hIgBACgAGCAEAAKMgAQAAAQAIRABAAUCAACAQKAAMACAYCAAgYAAQASAgEAAIDoEKYEECgWACRmREKYEIQCQQEtlQgkAQIK4QhFngAQCImCgAAAAAKwABAWCwOJJASoSCBLiDaAAAgAQCCACoQScmAAIAzZag8GTaMrSANHzBIhpgGACOgAgJk.f_wACHwAAAAA",
        "nuka-recommender-fp": "e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79",
        "nuka-ppid": "964b08c6-ca4d-491e-8222-42ea7ec74aba",
        "df_uid": "21e6b96a-9ed5-4b80-8dc0-881dc343099d",
        "njuskalo_adblock_detected": "true",
        "PHPSESSID": "7f9e4fd69fda7daa6a902053fa561f69",
        "__uzmc": "2438582369546",
        "__uzmd": "1725281909",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        # 'cookie': 'nuka-fp=e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79; login_2fa=e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79; __uzma=8319a3d2-e332-4445-a1ea-7de538d8368d; __uzmb=1724935081; __uzme=5674; njuskalo_privacy_policy=12; didomi_token=eyJ1c2VyX2lkIjoiMTkxOWUyNDgtZDkwOS02ZTZhLTlmNWQtOTExZDM4YTRjMDQzIiwiY3JlYXRlZCI6IjIwMjQtMDgtMjlUMTI6Mzg6MDEuMzYwWiIsInVwZGF0ZWQiOiIyMDI0LTA4LTI5VDEyOjM4OjAyLjYyMloiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYW1hem9uIiwiYzppbnRvd293aW4tcWF6dDV0R2kiLCJjOmhvdGphciIsImM6bmV3LXJlbGljIiwiYzpjb21tMTAwIiwiYzpsaXZlY2hhdCIsImM6Ym9va2l0c2gtS2I4bmJBRGgiLCJjOmNvbW0xMDB2aS13ZG1NbTRKNiIsImM6Ym9va2l0bGEtTWFSZ2dtUE4iLCJjOmRvdG1ldHJpYy1nYjJmaktDSiIsImM6c3R5cmlhLXFoVWNra1plIiwiYzppc2xvbmxpbmUtRjlHQmdwUWgiLCJjOnhpdGktQjN3Ym5KS1IiLCJjOmV0YXJnZXQtV3dFakFRM0ciLCJjOmdvb2dsZWFuYS0yM2RkY3JEaCIsImM6bnVrYXJlY29tLXdra0JkcU04IiwiYzptaWRhcy1lQm5UR1hMRiIsImM6Z29vZ2xlYW5hLTRUWG5KaWdSIiwiYzpwaWFub2h5YnItUjNWS0MycjQiLCJjOnBpbnRlcmVzdCIsImM6dGVsdW0ta3c0RG1wUGsiLCJjOmdlbWl1c3NhLW1ja2lRYW5LIiwiYzppbnN1cmFkcy1KZ0NGNnBtWCIsImM6aG90amFyLVpMUExleFZiIiwiYzpnb29nbGVhbmEtOGlIR1JDdFUiLCJjOm9wdGltYXhtZS1OSFhlUWNDayIsImM6ZGlkb21pLW5rR2pHZHhqIiwiYzpzbWFydGFkc2UtN1dNOFhnVEYiLCJjOmNyaXRlb3NhLWdqcGNybWdCIiwiYzpnb29nbGVhZHYtWlo5ZTdZZGkiLCJjOm5qdXNrYWxvbi1BWWNOTmFpdyIsImM6Ymlkc3dpdGNoLUV0YjdMYTRSIiwiYzphZGFnaW8tRllnZjR3UkQiLCJjOm5qdXNrYWxvbi1BN2NQVmVFYSIsImM6YW1hem9uYWQtQzJ5bk5VbjkiLCJjOnlhaG9vYWRlLW1SSFFraG1VIiwiYzptZHByaW1pcy1XTVpBUm13NiIsImM6YW1hem9uLUw4NHRKUXg0IiwiYzpkaWRvbWkiXX0sInB1cnBvc2VzIjp7ImVuYWJsZWQiOlsiZGV2aWNlX2NoYXJhY3RlcmlzdGljcyIsImdlb2xvY2F0aW9uX2RhdGEiLCJvZ2xhc2l2YWNrLVE0RDlibVRHIiwiYXVkaWVuY2VtLWhKeGFlR3JSIiwiYW5hbHl0aWNzLXhHSHhHcFRMIl19LCJ2ZW5kb3JzX2xpIjp7ImVuYWJsZWQiOlsiZ29vZ2xlIiwiYzpib3hub3dkLTN4TmlKamZCIl19LCJ2ZXJzaW9uIjoyLCJhYyI6IkFrdUFFQUZrQkpZQS5Ba3VBRUFGa0JKWUEifQ==; euconsent-v2=CQEHUQAQEHUQAAHABBENBDFsAP_gAEPgAAAAKYtV_G__bWlr8X73aftkeY1P9_h77sQxBhfJE-4FzLvW_JwXx2ExNA36tqIKmRIAu3bBIQNlGJDUTVCgaogVryDMak2coTNKJ6BkiFMRe2dYCF5vmwtj-QKY5vr991dx2B-t7dr83dzyz4VHn3a5_2a0WJCdA5-tDfv9bROb-9IOd_x8v4v8_F_rE2_eT1l_tevp7D9-cts7_XW-9_fff79Ln_-uB_--Cl4BJhoVEAZYEhIQaBhBAgBUFYQEUCAAAAEgaICAEwYFOwMAl1hIgBACgAGCAEAAKMgAQAAAQAIRABAAUCAACAQKAAMACAYCAAgYAAQASAgEAAIDoEKYEECgWACRmREKYEIQCQQEtlQgkAQIK4QhFngAQCImCgAAAAAKwABAWCwOJJASoSCBLiDaAAAgAQCCACoQScmAAIAzZag8GTaMrSANHzBIhpgGACOgAgJk.f_wACHwAAAAA; nuka-recommender-fp=e15f95c4-84f6-4b8b-8b4b-8f4ea9505f79; nuka-ppid=964b08c6-ca4d-491e-8222-42ea7ec74aba; df_uid=21e6b96a-9ed5-4b80-8dc0-881dc343099d; njuskalo_adblock_detected=true; PHPSESSID=7f9e4fd69fda7daa6a902053fa561f69; __uzmc=2438582369546; __uzmd=1725281909',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://www.njuskalo.hr/prodaja-kuca",
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
        "https://www.njuskalo.hr/nekretnine/prodaja-demerje-brezovica-3-3-kuce-nizu-useljenje-12-2024-oglas-44016956",
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
