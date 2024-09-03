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
        "imovzt": "5032940066",
        "cookies_cleared_20230614": "eyJpdiI6InA0emFtQW9kaGJOUlREemRjTmJPNmc9PSIsInZhbHVlIjoiNmljZVdpdXIwemJvdzU5cnJ1bDB0SlExbzBCdkUwd1hjQmRLR3VTTUhJZkpDQXlkSUYxMzBNaHZzNEtGcW5jSyIsIm1hYyI6IjVkODRhOWMyMGE3NTNlYWJmOWUzMjNhYzJmZDFjMGM1MjFmMTAxMTg4NjJlNmVhNzA3YmViNjE4MjFkYzhjZDgiLCJ0YWciOiIifQ%3D%3D",
        "_cq_duid": "1.1724069488.Kgtvi9X73GUfHEWV",
        "_cq_suid": "1.1724069488.ejcpAQtvsHhYcAHI",
        "imo_visitor_id_cookie": "imo_visitor_id_cookie-39f1930a-d7b8-4408-befd-3255430c77fd",
        "OptanonAlertBoxClosed": "2024-08-26T05:19:25.974Z",
        "smcx_457240670_last_shown_at": "1724649746804",
        "map_projects_first_visit": "eyJpdiI6IkhYQW9lU3ZJZWFURFFFMG9JZTJIY2c9PSIsInZhbHVlIjoiVmJ4dkFLTCszTC9yeVJMYjFrcHRjdzYxN25kMUNsMERPSmY5VVY1Yi9CM1hZN08rVy9CNHZKNnIwSmRCdUdmaiIsIm1hYyI6ImJjMTI3N2VlOWY2NTllMDE0YjM0MWVlYjQwNzdkZjE5NjQ2ZDVhYTNiMzA5YTUwYjA3ZTQ4Zjk2OWJhMTFmNTkiLCJ0YWciOiIifQ%3D%3D",
        "__cf_bm": "faeqVhwNkd6hg7iKSEq1wsxTUAKBxoHsO0jk1SS43Pc-1725384558-1.0.1.1-lexbjl7rvhi7bInaOnVM0B4GqiJ46Tggb1bY2hyOmZLa6eRiVO5kASeaR69Z2zoiDJmff4g46A5jZTCOlJxUFg",
        "recent_searches": "eyJpdiI6ImZOdHpXSzE1R09BbzB0YWcvTGpFamc9PSIsInZhbHVlIjoicGJ5b0FVUXM4OFNoampjMHRSYUtiVThBbVJUSEE2UiswaDNSS0duWXFmK1ZybS82dXE5OG9ueWVKaTJRSjFwOWlZdnZES0tKTDVFVW8wMW9XcUtSYTFkSVpqbzNTODl1cnRrSDdNQjgvTWtHaXFINXNMWng0Q3BSdUN4RVVoOWRRTFlONjU1T25qS0lCZ0lwYzFsdENrSDJjWFE5ZDBQMkhiRXloek9aUnNYVkVGME9yYXUrMEFsSmxham1oN3BPZVJmUm5hUmVKU1A5QkpJN0Y1alplRjY0dFcxTU5GK0hncHBRT004S2dCbWhiUkJVbjdkc3FPTU5aZS9jVjliT3RTdVNXQnFHa2JoOWc1NWZpNWxaVlZ2cEhnV0J5R3d4akFjNVgraHo4N211cU5TRm5ucks4dE94UzBGNUxkWFg4Um5ZQko3M1k0ODNuOGxRc1QvQ1JPeDdWWS92K3N0VG5BWHJxdnIvUDQrZEVOMndzb01YZnBGN016TjNLNTI3SEV5a3UwM1lja3JIVmlpa0tDLzB6NjNSMFBjOEhVRTNBNWJmRitycDB1ZThSbDk5bkdxV1dMRDlWeCtqSWxPR1IxY28ybVVlUFQwM0RmK2FnMVM5K0hhZWozeEZLanYvemVEODl5M0VPQXFZQUh5YXlpeGZGNjBjZlcvdXRub0h1d3VaMUdHd3I1b2F4U3ljOWI2Y0hnPT0iLCJtYWMiOiIyNzBkMDk2M2RlNzg5MjEzZWI4NWRiNjlmNmZiNmJmYzU0ZTc0ZWFiYTM2ZmIyMzQzMGM3Mjc3ZmRiODIyNmRiIiwidGFnIjoiIn0%3D",
        "map_listings_first_visit": "eyJpdiI6IlowclhUZnNYQk9VMVFKN2hQNkFEUVE9PSIsInZhbHVlIjoiZjJiOW9XWXFxOUpXSkJ1ZFN5cGRBNjhtbWZQL3RyOEtOZVhNWDlhUERzUTVNa2l2bGJOWHJCME5ETXR5R0NndCIsIm1hYyI6IjI3ZmFlMjU5OTU5NDAzYjIzZGUxYTVmMWM0MTg0OTg4NWY0YmY1Zjc4ZGVjMjE3MWNlMzE5MzBhM2FjZWY2YzkiLCJ0YWciOiIifQ%3D%3D",
        "exitIntentRecomandate": "eyJpdiI6IllDK2pjc05ia1NyWTRQWkVTWlVrTHc9PSIsInZhbHVlIjoiakdwMDN0TVBLaDVjejM5TThzbXUxYkZCWG0zbm9mZEswOHJsbDZzQjJJQ3hQNU9XZE1mbjRPcWdHcHNjNld1SSIsIm1hYyI6IjNjN2Q3ZTdhZDk5YWJiYzdlOTEwMjhjOTljNjE3MGU1NGI2YzBhYjk5YzM2N2ZlNDcxYzAzYTdiZTBjOGVjMjciLCJ0YWciOiIifQ%3D%3D",
        "datadome": "EwKJOaaGvGn5G6QXqRbMeYwP40eN_ZRs~YTXNCrc9tVt2lN4aGSN5g3xSoJiAQS1046c5qNt3vq1t8t3ReQO8sAE2bKOstzjDDg~pbcP6DXI6EYrufhCh1j8Uqx67uS8",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Tue+Sep+03+2024+20%3A34%3A03+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=5c0f0622-d46b-4c50-a3c6-fba52f21ed53&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1%2CC0003%3A1&geolocation=UA%3B18&AwaitingReconsent=false",
        "_cq_pxg": "3|e99814036566831188",
        "XSRF-TOKEN": "eyJpdiI6IlRkeE1zWkdkUU0vVlNyM3RYUE55eFE9PSIsInZhbHVlIjoicUN3clV0NjhvR1BHMkdUb1dkRklaYVgrWHdwMHp4VVFIcTRWZ0RPMXM4cjgrMExwa29oL0xUeXJGUUN0bVh2SUVLa3Jmb1IvNXRZQ1FUUTJ2c3VmN0hyL0h5WnZTNG1ETXBDaG5MYkd1aWEwOFROa2RZekVLR1BMMFlubE1QaUsiLCJtYWMiOiI3ODc5ODJhY2UzYWMwY2MwOGY2MzQxZTJjMTQyMDdhMThhMGNjMmNmOGI1ZjhjMDE2ZWQ0YzRmY2QyNTI5MDY2IiwidGFnIjoiIn0%3D",
        "imobiliare_session": "eyJpdiI6IllVV2lrMGNocmtPRk9xNjBiWHo0Y2c9PSIsInZhbHVlIjoiQnEzRFBiaW1kWnJlelJ4ellmRm1rb01Dc2ZKaUlhUW5WTkR2cWtxMVp3UlVUN2FSbEpBcGkrTDh2NncwUGNDMUIvcFF5WE5Kcmx0MGlIL0NGeitxbUc5dUREV0NpOUxLT0djLzVvNWcvMngrV1Y0azZyNklNaVV5OWNRbmlmYUsiLCJtYWMiOiJkZjc5MDRjNjcxMTJmNGUwZjZjZGE5NmM0ODI3Mzk1ZTRjZWZlODFmZjdkYjc5OTc0YmMyZTQ5M2Q1OTdmMTBkIiwidGFnIjoiIn0%3D",
        "show_recommendations": "eyJpdiI6InhQSld2ZjZOSGR5VEFBSkRkTnRSR2c9PSIsInZhbHVlIjoiUk5zeGJ0bGE5MVNMM2xxV2hHQ2JIVEJ4emhSa04yV20xVDdNOHhiVFhwejJMcEprelB5U3pQNnRrMHZWZGVrayIsIm1hYyI6IjU0YmE2NWIxMDRlN2U5MDlkOGZjY2I2YzZiODU3YjdjYmZjMGEwMmU4MWE5ZDYxMWY0YTdiNjJkNjIyOTg2ZjciLCJ0YWciOiIifQ%3D%3D",
        "experiments": "eyJpdiI6IlhhRElWcE9odU9Qd0IzQlVCVFNoNWc9PSIsInZhbHVlIjoiSDJ5RVhudndNYkVoTEt6d3dUU1dpbmVWcng1QTFDRDZCYVVLWmhJeTZHTWN5UEVYZERxZEF1WEVvbkZud1BOLyIsIm1hYyI6IjM0ZDllMDYzYmRkYmEzMDJiMDExYzVjOTM4NzcwNmRiNTMyNjQxZDVlMDUyYTRhZDcyMTQxNTcwNDZlNjU1OTkiLCJ0YWciOiIifQ%3D%3D",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://www.imobiliare.ro/vanzare-apartamente",
        "sec-ch-device-memory": "8",
        "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-full-version-list": '"Chromium";v="128.0.6613.114", "Not;A=Brand";v="24.0.0.0", "Google Chrome";v="128.0.6613.114"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://www.imobiliare.ro/oferta/apartament-de-vanzare-sector-3-mihai-bravu-2-camere-236076586",
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
