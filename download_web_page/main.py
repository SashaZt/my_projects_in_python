import asyncio
import csv
import json
import os
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import aiohttp
import pandas as pd
import requests
import urllib3
import usaddress
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from requests.adapters import HTTPAdapter
from tqdm import tqdm
from urllib3.poolmanager import PoolManager

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_html():
    cookies = {
        "piguVisitorWallet": "452518733",
        "TPSN": "UxtQ9Za-soF6xYUsqSogiA1on8rusRPp9d7FqyNq78YgG8dMzzew8V9V75OY0iGPpzZhylpRBsQIh-WWEC0gdOF0TOooGZdebuujlajphmFmoLNDomopUANCzXvTqVJ3",
        "__cf_bm": "VI8tWQxc9g3CLR0og0KRUkfzOhVGH._K.RFbtTzc2z0-1737543806-1.0.1.1-95RMg8csxx0onkJWr3k1GF6Y1zECGIcqcKFotgd8K4GgpsDUfm7Esa9WLoz.2zMbdXwFRf6GmZULkTy_MgKyQpGKcZ3JFQQMYxg62LHmVbE",
        "cf_clearance": "ORS57QQWbDl0TeUd7RCrt6keLxWfs5Ip3Gyxapjjp9o-1737543807-1.2.1.1-HEnGBmSvQ.gshl9lNcRk7FdtssSMu7fHS6IwpPG60CRtslK7hhNqbLfI.s9ioAThZZxpH9qTHhTkyQpnR9LMAWIq85HaPozptUP6fFdy9WlOc4L036QKnbisLO9V0H3pBxF0V1VVQtlR86D7UKYVQqlwpSBu5QuxMQJWCBakViFvQRK5Ld6M7WMWU4o2IvPGOWrI0nrjCsuOo.PH3MtxBjyepCsSfZosdv.cbWn8JNP0ajVfYTyb4NHTyUZxJeleZ5VCJVUPeYmuKMRwHtXwcjNHo5Z7L7fjCaCL99gRI2o",
        "csrf_p_token": "600db.ZGU5M2JkMzIyZmI4YjljMg.AQEBUgRTUgUFAAQJB1wAAgcGXwIHVVULB1ZXAFcMVgI",
        "CA_DT_V3": "1",
        "CA_DT_V2": "1",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 'piguVisitorWallet=452518733; TPSN=UxtQ9Za-soF6xYUsqSogiA1on8rusRPp9d7FqyNq78YgG8dMzzew8V9V75OY0iGPpzZhylpRBsQIh-WWEC0gdOF0TOooGZdebuujlajphmFmoLNDomopUANCzXvTqVJ3; __cf_bm=VI8tWQxc9g3CLR0og0KRUkfzOhVGH._K.RFbtTzc2z0-1737543806-1.0.1.1-95RMg8csxx0onkJWr3k1GF6Y1zECGIcqcKFotgd8K4GgpsDUfm7Esa9WLoz.2zMbdXwFRf6GmZULkTy_MgKyQpGKcZ3JFQQMYxg62LHmVbE; cf_clearance=ORS57QQWbDl0TeUd7RCrt6keLxWfs5Ip3Gyxapjjp9o-1737543807-1.2.1.1-HEnGBmSvQ.gshl9lNcRk7FdtssSMu7fHS6IwpPG60CRtslK7hhNqbLfI.s9ioAThZZxpH9qTHhTkyQpnR9LMAWIq85HaPozptUP6fFdy9WlOc4L036QKnbisLO9V0H3pBxF0V1VVQtlR86D7UKYVQqlwpSBu5QuxMQJWCBakViFvQRK5Ld6M7WMWU4o2IvPGOWrI0nrjCsuOo.PH3MtxBjyepCsSfZosdv.cbWn8JNP0ajVfYTyb4NHTyUZxJeleZ5VCJVUPeYmuKMRwHtXwcjNHo5Z7L7fjCaCL99gRI2o; csrf_p_token=600db.ZGU5M2JkMzIyZmI4YjljMg.AQEBUgRTUgUFAAQJB1wAAgcGXwIHVVULB1ZXAFcMVgI; CA_DT_V3=1; CA_DT_V2=1',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    params = {
        "id": "14862980",
    }

    response = requests.get(
        "https://pigu.lt/lt/technika-ir-elektronika/namu-technika/dulkiu-siurbliai/dulkiu-siurblys-philips-fc933009",
        params=params,
        cookies=cookies,
        headers=headers,
        timeout=30,
    )

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("pigu_lt.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    logger.info(response.status_code)


def get_json():
    timeout = 30
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}
    cookies = {
        "8020f80b5f22684beb6e2f5b559c57a9": "c5a427ee1d20c834b37ecb224ba52d87",
        "1686d7a14f465e6537467e88114cf7e8": "9009d01537a3658e432f2f7d1d1ffc69",
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "content-type": "application/json",
        # 'cookie': '8020f80b5f22684beb6e2f5b559c57a9=c5a427ee1d20c834b37ecb224ba52d87; 1686d7a14f465e6537467e88114cf7e8=9009d01537a3658e432f2f7d1d1ffc69',
        "dnt": "1",
        "origin": "https://purchasing.alberta.ca",
        "priority": "u=1, i",
        "referer": "https://purchasing.alberta.ca/search",
        "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    }
    for offset in range(0, 5):
        json_data = {
            "query": "",
            "filter": {
                "solicitationNumber": "",
                "categories": [
                    {
                        "value": "CNST",
                        "selected": True,
                        "count": 0,
                    },
                ],
                "statuses": [
                    {
                        "value": "AWARD",
                        "selected": True,
                        "count": 0,
                    },
                ],
                "agreementTypes": [],
                "solicitationTypes": [],
                "opportunityTypes": [],
                "deliveryRegions": [],
                "deliveryRegion": "",
                "organizations": [],
                "unspsc": [],
                "postDateRange": "$$custom",
                "closeDateRange": "$$custom",
                "onlyBookmarked": False,
                "onlyInterestExpressed": False,
            },
            "limit": 100,
            "offset": offset,
            "sortOptions": [
                {
                    "field": "PostDateTime",
                    "direction": "desc",
                },
            ],
        }

        response = requests.post(
            "https://purchasing.alberta.ca/api/opportunity/search",
            cookies=cookies,
            headers=headers,
            json=json_data,
            timeout=timeout,
        )

        # Проверка кода ответа
        if response.status_code == 200:
            json_data = response.json()
            # filename = os.path.join(json_path, f"0.json")
            with open(f"proba_{offset}.json", "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
        else:
            print(response.status_code)


def download_xml():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}
    save_path = "sitemap.xml"

    cookies = {
        "euconsent-v2": "CQJAbUAQJAbUAAjABCENBRFgAP_AAEPAACgAIzBV5CpMDWFAMHBRYNMgGYAW10ARIEQAABCBAyABCAGA8IAA0QECMAQAAAACAAIAoBABAAAAAABEAEAAIAAAAABEAAAAAAAIIAAAAAEQQAAAAAgAAAAAEAAIAAABAAQAkAAAAYKABEAAAIAgCAAAAAABAAAAAAMACAAIAAAAAAIAAAAAAAIAAAAAAEEAARAyyAYAAgABQAFwAtgD7AJSAa8A_oC6AGCAMhAZYAMEgQgAIAAWABUADgAIIAZABoAEQAJgAVQA3gB-AEJAIYAiQBLACaAGGAMoAc8A-wD9AIoARoAkQBcwDFAG0ANwAcQBQ4C8wGrgOCAeOBCEdAjAAWABUADgAIIAZABoAEQAJgAVQAuABiADeAH6AQwBEgCWAE0AMMAZQA0QBzwD7AP2AigCLAEiALmAYoA2gBuADiAIvATIAocBeYDLAGmgNXAeOQgGAALACqAFwAMQAbwBzgEUAJSAXMAxQBtAHjkoB4ACAAFgAcACIAEwAKoAXAAxQCGAIkAfgBcwDFAIvAXmBCEpAdAAWABUADgAIIAZABoAEQAJgAUgAqgBiAD9AIYAiQBlADRAHPAPwA_QCLAEiALmAYoA2gBuAEXgKHAXmAywBwQDxwIQlQAQACgAtgAA.YAAAAAAAAAAA",
        "consentUUID": "6cb56b4f-3f34-435d-b1d3-c1977cb47e33_38",
        "consentDate": "2024-12-02T11:46:43.209Z",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "max-age=0",
        # 'cookie': 'euconsent-v2=CQJAbUAQJAbUAAjABCENBRFgAP_AAEPAACgAIzBV5CpMDWFAMHBRYNMgGYAW10ARIEQAABCBAyABCAGA8IAA0QECMAQAAAACAAIAoBABAAAAAABEAEAAIAAAAABEAAAAAAAIIAAAAAEQQAAAAAgAAAAAEAAIAAABAAQAkAAAAYKABEAAAIAgCAAAAAABAAAAAAMACAAIAAAAAAIAAAAAAAIAAAAAAEEAARAyyAYAAgABQAFwAtgD7AJSAa8A_oC6AGCAMhAZYAMEgQgAIAAWABUADgAIIAZABoAEQAJgAVQA3gB-AEJAIYAiQBLACaAGGAMoAc8A-wD9AIoARoAkQBcwDFAG0ANwAcQBQ4C8wGrgOCAeOBCEdAjAAWABUADgAIIAZABoAEQAJgAVQAuABiADeAH6AQwBEgCWAE0AMMAZQA0QBzwD7AP2AigCLAEiALmAYoA2gBuADiAIvATIAocBeYDLAGmgNXAeOQgGAALACqAFwAMQAbwBzgEUAJSAXMAxQBtAHjkoB4ACAAFgAcACIAEwAKoAXAAxQCGAIkAfgBcwDFAIvAXmBCEpAdAAWABUADgAIIAZABoAEQAJgAUgAqgBiAD9AIYAiQBlADRAHPAPwA_QCLAEiALmAYoA2gBuAEXgKHAXmAywBwQDxwIQlQAQACgAtgAA.YAAAAAAAAAAA; consentUUID=6cb56b4f-3f34-435d-b1d3-c1977cb47e33_38; consentDate=2024-12-02T11:46:43.209Z',
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://www.focus-gesundheit.de/sitemap/sitemap.gesundheit.entries.xml",
        cookies=cookies,
        headers=headers,
    )

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


# Функция для очистки данных
def clean_text(text):
    # Убираем лишние пробелы и символы \xa0
    cleaned_text = text.replace("\xa0", " ").strip()
    # Убираем заголовки, если они присутствуют
    cleaned_text = re.sub(
        r"^(Код ЄДРПОУ|Дата реєстрації|Дата оновлення)", "", cleaned_text
    )
    return cleaned_text.strip()


def parsing_page():
    # Папка с HTML файлами
    html_folder = Path("html_files")

    # Множество для хранения уникальных itm_value
    unique_itm_values = set()

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_folder.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            table = soup.find("div", attrs={"data-qaid": "product_gallery"})
            div_element = table.find_all("a")
            logger.info(len(div_element))
            if div_element:
                for href in div_element:
                    url_company = href.get("href")
                    logger.info(url_company)


def get_url():
    # Папка с HTML файлами
    html_folder = Path("html_files")

    # Множество для хранения уникальных itm_value
    unique_itm_values = set()

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_folder.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            # Найти все <div> с классом 'str-quickview-button str-item-card__property-title'
            div_elements = soup.find_all("div", class_="pr-1")

            # Пройтись по каждому найденному элементу и извлечь itm из атрибута data-track
            for div in div_elements:
                data_track = div.find("a", attrs={"data-id": "address-context-cta"})

                if data_track:
                    # Преобразовать значение JSON обратно в словарь
                    href = data_track.get("href")

                    unique_itm_values.add(href)
    logger.info(len(unique_itm_values))
    # Создать список URL на основе уникальных itm_value
    urls = [f"https://www.ebay.com/itm/{itm_value}" for itm_value in unique_itm_values]

    # Создать DataFrame из списка URL
    df = pd.DataFrame(urls, columns=["url"])

    # Записать DataFrame в CSV файл
    df.to_csv("unique_itm_urls.csv", index=False)


def get_responses_from_urls(file_path):
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        "s": "CgAD4ACBnDlQLOGFkMWYyYWQxOTIwYWE3Mjg4YzZkNzg2ZmZjZWU3OTaiWuwe",
        "ak_bmsc": "C5461596E2A7551D119B11B9AC7B4A87~000000000000000000000000000000~YAAQXTYQYBs9gH+SAQAAxPTRihn+AWhsuWoyN3PCEJ+fTJzH0ZnsnOW9aAaAcJhh+dNSOA5b9vqesmudElEdoNe7JQS3USAIlHzsRC2IJWk94b0Bt46s+x0tC+g7T/poR9w2EESsABx19L08PmPOMcsmiCdb3+LZhDbBMxG2U+0lwoQDiWqoWzulDBjHY8nL8BCuYSNCFjjwf48QAv/IRLVTkyf6+eaOPzKv85nA0K0dKq0DVYJO0rptkbqPEncGlMlG28Q4D6Gen8YDK7rlR6N2KBPjZ9GBcRHbMAVQuWDO93Hg1YzT2VVnFpKNTmLoZxbjIcKlu88of3kJQusPXcEUHfiFCOX3A6PZYfMEHEQJ6XWib/GUOSH95Z7EhrEvfFFRHSm8ewc=",
        "__uzma": "a813fe6e-4491-4adc-8972-ae1f29622c57",
        "__uzmb": "1728905869",
        "__uzmc": "339401098533",
        "__uzmd": "1728905869",
        "__uzme": "4418",
        "__uzmf": "7f600059d8118f-fb35-4b9a-b231-c5eec813234417289058693160-ffb7b7e1a4c777b510",
        "__deba": "RClCxlc-RAB_iiOQfM5Gy3iTDLa83ZECddE3KGmIlkqApCS_e_ekH1bHChZhGkiYXR8UW1J2_XMwSXzXGqPFGDSJTUEHeLCqHI7wQDliKL3OHHm_qoCVpJuFHpX8VWFKh28lda3_iYXrpK5b_jSZhA==",
        "nonsession": "BAQAAAZJU03gwAAaAADMABWjuNh4xMDAwNQDKACBqz2meOGFkMWYyYWQxOTIwYWE3Mjg4YzZkNzg2ZmZjZWU3OTYAywABZw0JpjePPj4vOnrhWFHAcV9W4r2LgMGnnA**",
        "bm_sv": "21120F2BFDB1FFC0111D0DA586896449~YAAQXTYQYP9FgH+SAQAARDzSihmyCoZaNGXJaW8p6l6RvK6Uj9LROaFjpq3z31ZcBfRDfmqFZ/a1rNkHdtMgBgq3WJZXhdcox0GRchTikrg4sLJm9G+rtVXU59mknvW66ro5hUj6xaAnIbMYs1Q4xW5ApSCWiyePfi6pJNCgI1YwBS0c/rMqATKTnwqT6ls8+QqcWulrrtpn70tofKz4NadxtjH/sa7AT4LVlgkSYYfVNkonNv/LT4XFLqTcDw==~1",
        "dp1": "bbl/UA6acf699e^pbf/#e0002000000000000000006acf69a5^",
        "ebay": "%5Esbf%3D%23000000%5Ejs%3D1%5E",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 's=CgAD4ACBnDlQLOGFkMWYyYWQxOTIwYWE3Mjg4YzZkNzg2ZmZjZWU3OTaiWuwe; ak_bmsc=C5461596E2A7551D119B11B9AC7B4A87~000000000000000000000000000000~YAAQXTYQYBs9gH+SAQAAxPTRihn+AWhsuWoyN3PCEJ+fTJzH0ZnsnOW9aAaAcJhh+dNSOA5b9vqesmudElEdoNe7JQS3USAIlHzsRC2IJWk94b0Bt46s+x0tC+g7T/poR9w2EESsABx19L08PmPOMcsmiCdb3+LZhDbBMxG2U+0lwoQDiWqoWzulDBjHY8nL8BCuYSNCFjjwf48QAv/IRLVTkyf6+eaOPzKv85nA0K0dKq0DVYJO0rptkbqPEncGlMlG28Q4D6Gen8YDK7rlR6N2KBPjZ9GBcRHbMAVQuWDO93Hg1YzT2VVnFpKNTmLoZxbjIcKlu88of3kJQusPXcEUHfiFCOX3A6PZYfMEHEQJ6XWib/GUOSH95Z7EhrEvfFFRHSm8ewc=; __uzma=a813fe6e-4491-4adc-8972-ae1f29622c57; __uzmb=1728905869; __uzmc=339401098533; __uzmd=1728905869; __uzme=4418; __uzmf=7f600059d8118f-fb35-4b9a-b231-c5eec813234417289058693160-ffb7b7e1a4c777b510; __deba=RClCxlc-RAB_iiOQfM5Gy3iTDLa83ZECddE3KGmIlkqApCS_e_ekH1bHChZhGkiYXR8UW1J2_XMwSXzXGqPFGDSJTUEHeLCqHI7wQDliKL3OHHm_qoCVpJuFHpX8VWFKh28lda3_iYXrpK5b_jSZhA==; nonsession=BAQAAAZJU03gwAAaAADMABWjuNh4xMDAwNQDKACBqz2meOGFkMWYyYWQxOTIwYWE3Mjg4YzZkNzg2ZmZjZWU3OTYAywABZw0JpjePPj4vOnrhWFHAcV9W4r2LgMGnnA**; bm_sv=21120F2BFDB1FFC0111D0DA586896449~YAAQXTYQYP9FgH+SAQAARDzSihmyCoZaNGXJaW8p6l6RvK6Uj9LROaFjpq3z31ZcBfRDfmqFZ/a1rNkHdtMgBgq3WJZXhdcox0GRchTikrg4sLJm9G+rtVXU59mknvW66ro5hUj6xaAnIbMYs1Q4xW5ApSCWiyePfi6pJNCgI1YwBS0c/rMqATKTnwqT6ls8+QqcWulrrtpn70tofKz4NadxtjH/sa7AT4LVlgkSYYfVNkonNv/LT4XFLqTcDw==~1; dp1=bbl/UA6acf699e^pbf/#e0002000000000000000006acf69a5^; ebay=%5Esbf%3D%23000000%5Ejs%3D1%5E',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-full-version": '"129.0.6668.90"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"15.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }
    # Загрузить список URL из CSV файла
    df = pd.read_csv(file_path)

    # Пройтись по каждому URL и выполнить HTTP-запрос
    for url in df["url"]:
        try:
            response = requests.get(
                url, cookies=cookies, headers=headers, proxies=proxies_dict
            )
            if response.status_code == 200:
                id_product = url.split("/")[-1]

                # Сохранение HTML-страницы целиком
                with open(f"{id_product}.html", "w", encoding="utf-8") as file:
                    file.write(response.text)
                logger.info(id_product)

                # Здесь можно добавить код для обработки ответа, если требуется
            else:
                print(
                    f"Ошибка при запросе {url}, код состояния: {response.status_code}"
                )
        except requests.RequestException as e:
            print(f"Ошибка при подключении к {url}: {e}")


def parsing_xml():
    # Путь к файлу XML
    save_path = "sitemap.products.xml"

    # Открываем и парсим XML-файл
    tree = ET.parse(save_path)
    root = tree.getroot()

    # Определение пространства имен
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Извлечение всех тегов <loc>
    locations = root.findall(".//ns:loc", namespace)

    # Регулярное выражение для поиска нужных URL
    pattern = r"https://www\.ua-region\.com\.ua/sitemap/sitemap_\d+\.xml"

    # Генератор списков для получения всех URL, соответствующих регулярному выражению
    matching_urls = [loc.text for loc in locations if re.match(pattern, loc.text)]
    logger.info(matching_urls)


def parsing_csv():
    # Открываем CSV-файл с помощью pandas
    df = pd.read_csv(output_csv_file, nrows=10)

    # Просмотр первых 10 строк
    logger.info(df.head(10))


def download_pdf():
    cookies = {
        "sgat-language": "es_ES",
        "JSESSIONID": "wlp093~s7~0001Q56_J612Gw4GjOHmeUPPEEW:wlp093_wlp031",
    }

    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "multipart/form-data; boundary=----WebKitFormBoundaryAlx9X84SqxkAGTMD",
        # 'Cookie': 'sgat-language=es_ES; JSESSIONID=wlp093~s7~0001Q56_J612Gw4GjOHmeUPPEEW:wlp093_wlp031',
        "DNT": "1",
        "Origin": "https://sede.agenciatributaria.gob.es",
        "Referer": "https://sede.agenciatributaria.gob.es/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    idRCRD = "4d9fd70b2a429810VgnVCM100000dc381e0aRCRD"
    files = {
        "operacion": (None, "GET"),
        "lang": (None, "es_ES"),
        "idRCRD": (None, idRCRD),
    }
    try:
        response = requests.post(
            "https://www2.agenciatributaria.gob.es/wlpl/DGCO-JDIT/PDFactory",
            cookies=cookies,
            headers=headers,
            files=files,
        )

        if response.status_code == 200:
            pdf_path = pdf_files_directory / f"{idRCRD}.pdf"
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            # Записываем успешный URL в файл
            with open(csv_file_successful, "a", encoding="utf-8") as f:
                f.write(f"{idRCRD}\n")
            logger.info(f"PDF успешно скачан для idRCRD: {idRCRD}")
        else:
            logger.warning(
                f"Не удалось скачать PDF для idRCRD {idRCRD}. Статус ответа: {response.status_code}"
            )
    except Exception as e:
        logger.error(f"Ошибка при скачивании PDF для idRCRD {idRCRD}: {e}")


def pr_xml():
    # Чтение файла sitemap.xml
    with open("sitemap.xml", "r", encoding="utf-8") as file:
        xml_content = file.read()

    # Разбор XML содержимого
    root = ET.fromstring(xml_content)

    # Пространство имен XML, используется для правильного извлечения данных
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Извлечение всех URL из тегов <loc>
    urls = [url.text.strip() for url in root.findall(".//ns:loc", namespace)]

    # Создание DataFrame с URL
    url_data = pd.DataFrame(urls, columns=["url"])

    # Запись URL в CSV файл
    url_data.to_csv("urls.csv", index=False)


def url_test():

    url = "https://polanik.shop/en_GB/p/CA19-600-CARBON-PREMIUM-LINE-Competition-javelin/1335"
    # Извлекаем 'zorra' (домен третьего уровня)
    domain = url.split("//")[1].split(".")[0]

    # Извлекаем 'f773b8fe-1006-410e-aaf3-efb1aa377cea' (последний элемент после '/')
    file_id = url.rsplit("/", maxsplit=1)[-1]
    file_id = url.rsplit("/", maxsplit=2)[-2]
    # print(domain)
    print(file_id)


def format_proxies(proxy_list):
    """
    Преобразует список прокси в формат http://логин:пароль@IP:порт.

    :param proxy_list: список прокси в формате IP:port:username:password
    :return: список прокси в формате http://username:password@IP:port
    """
    formatted_list = [
        f"http://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"
        for proxy in proxy_list
    ]
    return formatted_list


def get_session_html():
    import requests

    # Создаем сессию
    session = requests.Session()

    # Делаем POST запрос для авторизации
    login_url = "https://polanik.shop/en_GB/login"
    login_payload = {"mail": "hdsport2006@gmail.com", "pass": "15987532"}
    login_headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://polanik.shop",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "referer": "https://polanik.shop/en_GB/login",
    }

    # Авторизуемся на сайте и сохраняем куки в сессии
    response = session.post(login_url, data=login_payload, headers=login_headers)

    # Проверяем, успешно ли прошел логин (статус код 200 и наличие нужной информации в ответе)
    if response.status_code == 200:
        print("Авторизация прошла успешно")

        # Делаем GET запрос к защищенной странице
        protected_url = "https://polanik.shop/en_GB/p/BL-2-square-block/850"
        protected_headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "referer": "https://polanik.shop/en_GB/",
        }
        response = session.get(protected_url, headers=protected_headers)

        # Проверяем, успешно ли мы получили доступ к защищенной странице
        if response.status_code == 200:
            print("Доступ к защищенной странице получен")

            # Сохраняем HTML содержимое страницы в файл
            filename = "protected_page.html"
            with open(filename, "w", encoding="utf-8") as file:
                file.write(response.text)
            print(f"HTML содержимое страницы сохранено в файл: {filename}")

        else:
            print(
                f"Не удалось получить доступ к защищенной странице. Статус код: {response.status_code}"
            )

    else:
        print(f"Ошибка авторизации. Статус код: {response.status_code}")


def get_contact_prom():
    import requests

    cookies = {
        "cid": "38151285142402004135884277792469422435",
        "evoauth": "we73d6bf140cf439eba971a0483a05c8f",
        "timezone_offset": "120",
        "last_search_term": "",
        "auth": "879752e05b9c2bfa0a928626b3981767a3741e97",
        "user_tracker": "101dfcb70c3124fa578c8a1209895e39f55a10a6|193.24.221.34|2024-11-26",
        "csrf_token": "2c09e87f92be4d98bd481efbd7066117",
        "wasProductCardVisited_120153155": "true",
        "wasProductCardVisited_112024327": "true",
        "wasProductCardVisited_48311559": "true",
        "visited_products": "106553552.48311559.112024327.120153155",
        "wasProductCardVisited_106553552": "true",
    }

    headers = {
        "accept": "*/*",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "content-type": "application/json",
        # 'cookie': 'cid=38151285142402004135884277792469422435; evoauth=we73d6bf140cf439eba971a0483a05c8f; timezone_offset=120; last_search_term=; auth=879752e05b9c2bfa0a928626b3981767a3741e97; user_tracker=101dfcb70c3124fa578c8a1209895e39f55a10a6|193.24.221.34|2024-11-26; csrf_token=2c09e87f92be4d98bd481efbd7066117; wasProductCardVisited_120153155=true; wasProductCardVisited_112024327=true; wasProductCardVisited_48311559=true; visited_products=106553552.48311559.112024327.120153155; wasProductCardVisited_106553552=true',
        "dnt": "1",
        "origin": "https://satu.kz",
        "priority": "u=1, i",
        "referer": "https://satu.kz/c782481-satservice.html",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "x-forwarded-proto": "https",
        "x-language": "ru",
        "x-requested-with": "XMLHttpRequest",
    }

    json_data = {
        "operationName": "CompanyContactsQuery",
        "variables": {
            "withGroupManagerPhones": False,
            "withWorkingHoursWarning": False,
            "getProductDetails": False,
            "company_id": 726240,
            "groupId": -1,
            "productId": -1,
        },
        "query": "query CompanyContactsQuery($company_id: Int!, $groupId: Int!, $productId: Long!, $withGroupManagerPhones: Boolean = false, $withWorkingHoursWarning: Boolean = false, $getProductDetails: Boolean = false) {\n  context {\n    context_meta\n    currentRegionId\n    recaptchaToken\n    __typename\n  }\n  company(id: $company_id) {\n    ...CompanyWorkingHoursFragment @include(if: $withWorkingHoursWarning)\n    ...CompanyRatingFragment\n    id\n    name\n    contactPerson\n    contactEmail\n    phones {\n      id\n      description\n      number\n      __typename\n    }\n    addressText\n    isChatVisible\n    mainLogoUrl(width: 100, height: 50)\n    slug\n    isOneClickOrderAllowed\n    isOrderableInCatalog\n    isPackageCPA\n    addressMapDescription\n    region {\n      id\n      __typename\n    }\n    geoCoordinates {\n      id\n      latitude\n      longtitude\n      __typename\n    }\n    branches {\n      id\n      name\n      phones\n      address {\n        region_id\n        country_id\n        city\n        zipCode\n        street\n        regionText\n        __typename\n      }\n      __typename\n    }\n    webSiteUrl\n    site {\n      id\n      isDisabled\n      __typename\n    }\n    operationType\n    __typename\n  }\n  productGroup(id: $groupId) @include(if: $withGroupManagerPhones) {\n    id\n    managerPhones {\n      id\n      number\n      __typename\n    }\n    __typename\n  }\n  product(id: $productId) @include(if: $getProductDetails) {\n    id\n    name\n    image(width: 60, height: 60)\n    price\n    signed_id\n    discountedPrice\n    priceCurrencyLocalized\n    buyButtonDisplayType\n    regions {\n      id\n      name\n      isCity\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CompanyWorkingHoursFragment on Company {\n  id\n  isWorkingNow\n  isOrderableInCatalog\n  scheduleSettings {\n    id\n    currentDayCaption\n    __typename\n  }\n  scheduleDays {\n    id\n    name\n    dayType\n    hasBreak\n    workTimeRangeStart\n    workTimeRangeEnd\n    breakTimeRangeStart\n    breakTimeRangeEnd\n    __typename\n  }\n  __typename\n}\n\nfragment CompanyRatingFragment on Company {\n  id\n  inTopSegment\n  opinionStats {\n    id\n    opinionPositivePercent\n    opinionTotal\n    __typename\n  }\n  __typename\n}",
    }

    response = requests.post(
        "https://satu.kz/graphql", cookies=cookies, headers=headers, json=json_data
    )
    json_data = response.json()
    with open("kyky.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


def get_category_html():
    # cookies = {
    #     "_cmuid": "2dda2bfa-7c83-4d7a-b8c2-c2b019abfc9c",
    #     "gdpr_permission_given": "1",
    #     "__gfp_64b": "-TURNEDOFF",
    #     "OptOutOnRequest": "groups=googleAnalytics:1,googleAdvertisingProducts:1,tikTok:1,allegroAdsNetwork:1,facebook:1",
    #     "_fbp": "fb.1.1730705513360.2103671403",
    #     "_meta_facebookTag_sync": "1730705513360",
    #     "_meta_googleGtag_ga_library_loaded": "1732617414758",
    #     "_ga": "GA1.1.764773296.1732617054",
    #     "_gcl_au": "1.1.2068937467.1732617415",
    #     "_tt_enable_cookie": "1",
    #     "_ttp": "w0twNdkVuWimw_xIZvxkeal5NyI.tt.1",
    #     "_meta_googleGtag_ga": "GA1.1.764773296.1732617054",
    #     "wdctx": "v5.69gDzY2U7Ol17F4jy_x0a2sImZ8whsNP5CXj29072flaj0pnm-8EX_IN3hwXZXxgn8eGUpZ2mof7mdiTSliTWFXprkFXdif51XJ6_SRQwedBA-UEhpyDZRY-Am54KkDgudLQ874kQps2gmlR1pEBKWmcthGT8B4HCdKDJxb1VmtPLo8CkxWoqWa2kUa4WcQcRWt7LzmPaQ5QoO9VZqOS2JTEN9mV3kIiOrVC7_yIdtBG.RtXzRMINTbaq9hS7Zee1RQ.94i3MVtwceE",
    #     "_meta_googleGtag_session_id": "1732620824",
    #     "_meta_googleGtag_ga_session_count": "2",
    #     "__rtbh.lid": "%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%2256My64JmEnNIiIZYza72%22%2C%22expiryDate%22%3A%222025-11-26T11%3A47%3A36.091Z%22%7D",
    #     "datadome": "E4BUmy3j9MMqlFpLZYHVXlED7~4HOAA2Mtmjf~6i7GaDv8xJZtiYrjGD8bAwdQXeEt_jS_YL2fcGXzj3kH0_kv3gd3yGmdCpcEI0BCbE6RE9y89WNw6iZCCBq9TPKeiY",
    #     "__rtbh.uid": "%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22undefined%22%2C%22expiryDate%22%3A%222025-11-26T11%3A47%3A36.637Z%22%7D",
    #     "_ga_G64531DSC4": "GS1.1.1732620826.2.1.1732621661.53.0.0",
    # }

    # headers = {
    #     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    #     "accept-language": "ru,en;q=0.9,uk;q=0.8",
    #     "cache-control": "no-cache",
    #     # 'cookie': '_cmuid=2dda2bfa-7c83-4d7a-b8c2-c2b019abfc9c; gdpr_permission_given=1; __gfp_64b=-TURNEDOFF; OptOutOnRequest=groups=googleAnalytics:1,googleAdvertisingProducts:1,tikTok:1,allegroAdsNetwork:1,facebook:1; _fbp=fb.1.1730705513360.2103671403; _meta_facebookTag_sync=1730705513360; _meta_googleGtag_ga_library_loaded=1732617414758; _ga=GA1.1.764773296.1732617054; _gcl_au=1.1.2068937467.1732617415; _tt_enable_cookie=1; _ttp=w0twNdkVuWimw_xIZvxkeal5NyI.tt.1; _meta_googleGtag_ga=GA1.1.764773296.1732617054; wdctx=v5.69gDzY2U7Ol17F4jy_x0a2sImZ8whsNP5CXj29072flaj0pnm-8EX_IN3hwXZXxgn8eGUpZ2mof7mdiTSliTWFXprkFXdif51XJ6_SRQwedBA-UEhpyDZRY-Am54KkDgudLQ874kQps2gmlR1pEBKWmcthGT8B4HCdKDJxb1VmtPLo8CkxWoqWa2kUa4WcQcRWt7LzmPaQ5QoO9VZqOS2JTEN9mV3kIiOrVC7_yIdtBG.RtXzRMINTbaq9hS7Zee1RQ.94i3MVtwceE; _meta_googleGtag_session_id=1732620824; _meta_googleGtag_ga_session_count=2; __rtbh.lid=%7B%22eventType%22%3A%22lid%22%2C%22id%22%3A%2256My64JmEnNIiIZYza72%22%2C%22expiryDate%22%3A%222025-11-26T11%3A47%3A36.091Z%22%7D; datadome=E4BUmy3j9MMqlFpLZYHVXlED7~4HOAA2Mtmjf~6i7GaDv8xJZtiYrjGD8bAwdQXeEt_jS_YL2fcGXzj3kH0_kv3gd3yGmdCpcEI0BCbE6RE9y89WNw6iZCCBq9TPKeiY; __rtbh.uid=%7B%22eventType%22%3A%22uid%22%2C%22id%22%3A%22undefined%22%2C%22expiryDate%22%3A%222025-11-26T11%3A47%3A36.637Z%22%7D; _ga_G64531DSC4=GS1.1.1732620826.2.1.1732621661.53.0.0',
    #     "dnt": "1",
    #     "dpr": "1",
    #     "pragma": "no-cache",
    #     "priority": "u=0, i",
    #     "sec-ch-device-memory": "8",
    #     "sec-ch-prefers-color-scheme": "light",
    #     "sec-ch-prefers-reduced-motion": "reduce",
    #     "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    #     "sec-ch-ua-arch": '"x86"',
    #     "sec-ch-ua-full-version-list": '"Google Chrome";v="131.0.6778.86", "Chromium";v="131.0.6778.86", "Not_A Brand";v="24.0.0.0"',
    #     "sec-ch-ua-mobile": "?0",
    #     "sec-ch-ua-model": '""',
    #     "sec-ch-ua-platform": '"Windows"',
    #     "sec-ch-viewport-height": "1031",
    #     "sec-fetch-dest": "document",
    #     "sec-fetch-mode": "navigate",
    #     "sec-fetch-site": "none",
    #     "sec-fetch-user": "?1",
    #     "upgrade-insecure-requests": "1",
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    #     "viewport-width": "1149",
    # }

    # params = {
    #     "order": "qd",
    #     "stan": "nowe",
    #     "price_from": "150",
    #     "price_to": "1500",
    #     "page": "1",
    # }

    # response = requests.get(
    #     "https://allegro.pl/kategoria/silownia-i-fitness-trening-silowy-110145",
    #     params=params,
    #     cookies=cookies,
    #     headers=headers,
    # )
    # # Сохраняем HTML содержимое страницы в файл
    filename = "allegro_category.html"
    # with open(filename, "w", encoding="utf-8") as file:
    #     file.write(response.text)
    with open(filename, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, "lxml")
    pagination_div = soup.find("div", {"aria-label": "paginacja"})


def get_wa_me():
    extracted_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        # Прочитать содержимое файла
        with html_file.open(encoding="utf-8") as file:
            content = file.read()
        soup = BeautifulSoup(content, "lxml")

        # Ищем все <script> теги
        script_tags = soup.find_all("script")

        # Регулярное выражение для поиска всей строки с var url = "https://wa.me/"
        url_pattern = re.compile(r'var url = "https://wa\.me/[^"]+"')

        # Извлекаем строки
        found_urls = []
        for script in script_tags:
            if script.string:  # Проверяем, что содержимое скрипта не пустое
                matches = url_pattern.findall(script.string)
                found_urls.extend(matches)
        logger.info(found_urls)
        # Извлекаем имя
        name = soup.find("h4").get_text(strip=True)
        url_profi = soup.find("link", {"rel": "canonical"}).get("href")
        # Извлекаем ссылки
        buttons = soup.find_all("button", class_="click_red")
        links = {
            button["data-ref"]: button["data-href"].strip()
            for button in buttons
            if "data-href" in button.attrs
        }
        # Извлекаем адрес
        direccion_div = soup.find("div", class_="direccion")
        direccion = None
        if direccion_div:
            direccion_text = direccion_div.find("span")
            if direccion_text:
                direccion = (
                    direccion_text.get_text(strip=True)
                    .replace("Direccion: ", "")
                    .replace(" Comunidad", "")
                )
        # Ищем все элементы с классом "mid-item", содержащие <h3 class="">Tarifas</h3>
        tarifas_data = []
        mid_items = soup.find_all("div", class_="mid-item")

        for mid_item in mid_items:
            # Проверяем наличие заголовка <h3 class="">Tarifas</h3>
            h3_tag = mid_item.find("h3", string="Tarifas")
            if h3_tag:
                # Ищем все тарифы внутри текущего элемента mid-item
                tarifas_section = mid_item.find("div", class_="mid-item-info")
                if tarifas_section:
                    tarifas_items = tarifas_section.find_all(
                        "div", class_="loaction-item"
                    )
                    for item in tarifas_items:
                        # Извлекаем название услуги
                        title_tag = item.find("h5")
                        title = title_tag.get_text(strip=True) if title_tag else None

                        # Извлекаем цену услуги
                        price_tag = item.find("div", class_="tarifas_costo").find(
                            "span"
                        )
                        price = (
                            price_tag.get_text(strip=True).replace("€", "")
                            if price_tag
                            else None
                        )

                        # Формируем данные для текущего тарифа
                        if title and price:
                            tarifas_data.append(f"{title}, {price}")
        # Формируем словарь
        data = {
            "name": name,
            "web": links.get("web", ""),  # Подставляем пустую строку, если ссылки нет
            "facebook": links.get("facebook", ""),
            "instagram": links.get("instagram", ""),
            "wa_urls": found_urls[0],
            "url_profi": url_profi,
            "direccion": direccion,
            "tarifas": tarifas_data,
        }
        extracted_data.append(data)
    # logger.info(extracted_data)
    # Преобразуем данные для записи в Excel
    rows = []
    for data in extracted_data:
        tarifas = " | ".join(data["tarifas"])  # Объединяем тарифы в одну строку
        rows.append(
            {
                "Name": data["name"],
                "Web": data["web"],
                "Facebook": data["facebook"],
                "Instagram": data["instagram"],
                "WhatsApp": data["wa_urls"],
                "Profile URL": data["url_profi"],
                "Address": data["direccion"],
                "Tarifas": tarifas,
            }
        )

    # Создаем DataFrame
    df = pd.DataFrame(rows)

    # Сохраняем в Excel
    output_file = "extracted_data.xlsx"
    df.to_excel(output_file, index=False)


# def get_html():
#     import csv

#     from bs4 import BeautifulSoup

#     # Читаем содержимое HTML файла
#     file_path = "protected_page.html"
#     with open(file_path, "r", encoding="utf-8") as file:
#         html_content = file.read()

#     # Парсим HTML с помощью BeautifulSoup
#     soup = BeautifulSoup(html_content, "html.parser")

#     # Ищем все элементы h3 с классом 'profesional-titulo', внутри которых есть ссылки
#     h3_elements = soup.find_all("h3", class_="profesional-titulo")

#     # Извлекаем href из <a> внутри каждого h3
#     urls = []
#     for h3 in h3_elements:
#         a_tag = h3.find("a", href=True)  # Ищем <a> с атрибутом href
#         if a_tag:
#             urls.append(a_tag["href"])

#     # Сохраняем список URL в CSV файл
#     output_file = "urls.csv"
#     with open(output_file, mode="w", encoding="utf-8", newline="") as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(["url"])  # Заголовок CSV файла
#         for url in urls:
#             writer.writerow([url])

#     print(f"Ссылки успешно сохранены в файл: {output_file}")


def get_htmls():
    # Множество для хранения уникальных ссылок
    unique_urls = set()

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        # Прочитать содержимое файла
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")

        # Ищем все <article> с классом "grid"
        articles = soup.find_all("article", class_="grid")

        # Извлекаем ссылки href из <a>
        for article in articles:
            links = article.find_all("a", href=True)
            for link in links:
                unique_urls.add(
                    link["href"]
                )  # Добавляем в множество (автоматически исключает дубликаты)

    # Преобразуем множество в список словарей для записи в CSV
    extracted_data = [{"url": url} for url in unique_urls]

    # Запись данных в CSV файл
    output_file = "extracted_urls.csv"
    with open(output_file, mode="w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["url"])
        writer.writeheader()
        writer.writerows(extracted_data)

    print(f"Уникальные ссылки успешно сохранены в файл: {output_file}")


def pars_htmls():
    extracted_data = []

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")

        # 1. Извлечь заголовок продукта
        product_title = soup.find(
            "h1", class_="product_title entry-title wd-entities-title"
        )
        product_title_text = product_title.text.strip() if product_title else None

        # 2. Извлечь цену
        price = soup.select_one("p.price span.woocommerce-Price-amount.amount bdi")
        price_text = price.text.strip() if price else None

        # 3. Извлечь информацию о наличии
        stock_info = soup.find("p", class_="stock in-stock wd-style-default")
        stock_text = stock_info.text.strip() if stock_info else None

        # 4. Извлечь описание
        description = soup.find("div", id="tab-description")
        description_text = description.get_text(strip=True) if description else None

        # 5. Извлечь артикул
        sku = soup.select_one("span.sku_wrapper span.sku")
        sku_text = sku.text.strip() if sku else None

        # 6. Извлечь категории (текст в строку через join)
        categories = soup.select('span.posted_in a[rel="tag"]')
        category_texts = (
            ", ".join(category.get_text(strip=True) for category in categories)
            if categories
            else ""
        )

        # 7. Найти все изображения с атрибутом role="presentation" и извлечь src
        script_tag = soup.find(
            "script", {"type": "application/ld+json", "class": "rank-math-schema"}
        )
        images_string = None
        if script_tag:
            # Загрузить JSON из содержимого тега
            data = json.loads(script_tag.string)

            # Инициализировать список для ссылок на изображения
            image_urls = []

            # Проход по массиву @graph
            for item in data.get("@graph", []):
                if "@type" in item and item["@type"] == "Product":
                    images = item.get("image", [])
                    # Если изображения представлены списком
                    if isinstance(images, list):
                        image_urls.extend(img["url"] for img in images if "url" in img)

            # Преобразовать список ссылок в строку, разделенную запятыми
            images_string = ", ".join(image_urls)
        # Сбор данных в список
        extracted_data.append(
            {
                "product_title_text": product_title_text,
                "price_text": price_text,
                "stock_text": stock_text,
                "description_text": description_text,
                "sku_text": sku_text,
                "category_texts": category_texts,
                "images_string": images_string,
            }
        )

    # Создание DataFrame и запись в Excel
    df = pd.DataFrame(extracted_data)
    df.to_excel("feepyf.xlsx", index=False)

    # print(f"Данные успешно сохранены в файл: {output_file}")


if __name__ == "__main__":
    # get_html()
    pars_htmls()
    # get_htmls()
    # get_html()
    # get_contact_prom()
    # get_category_html()
    # get_session_html()
    # # Пример использования
    # proxies = [
    #     "178.253.26.108:46342:BGIG0AAX:8D3PG3F3",
    #     "178.253.26.123:46372:BGIG0AAX:8D3PG3F3",
    #     "178.253.26.133:46392:BGIG0AAX:8D3PG3F3",
    #     "178.253.26.160:46446:BGIG0AAX:8D3PG3F3",
    #     "178.253.26.240:46606:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.117:46866:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.131:46894:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.153:46938:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.155:46942:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.159:46950:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.189:47010:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.237:47106:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.33:46698:BGIG0AAX:8D3PG3F3",
    #     "178.253.27.79:46790:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.102:45198:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.125:45244:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.14:45022:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.168:45454:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.205:45528:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.207:45532:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.23:45040:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.248:45614:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.3:45000:BGIG0AAX:8D3PG3F3",
    #     "185.252.162.39:45072:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.11:45646:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.14:45652:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.143:45910:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.149:45922:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.207:46038:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.222:46068:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.226:46076:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.227:46078:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.231:46086:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.249:46122:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.30:45684:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.57:45738:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.63:45750:BGIG0AAX:8D3PG3F3",
    #     "185.252.163.65:45754:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.112:49024:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.115:49030:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.140:49080:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.142:49084:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.16:48832:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.168:51203:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.179:51236:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.192:51275:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.196:51287:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.212:51335:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.223:51368:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.226:51377:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.241:51422:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.253:51458:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.30:48860:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.6:48812:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.89:48978:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.91:48982:BGIG0AAX:8D3PG3F3",
    #     "31.57.148.95:48990:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.108:51782:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.123:51827:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.127:51839:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.147:51899:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.156:51926:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.157:51929:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.178:51992:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.185:52013:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.216:52106:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.228:52142:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.230:52148:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.234:52160:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.248:52202:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.5:51473:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.63:51647:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.76:51686:BGIG0AAX:8D3PG3F3",
    #     "31.57.149.87:51719:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.102:53843:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.158:54011:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.16:53585:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.164:54029:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.192:54113:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.229:54224:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.232:54233:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.235:54242:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.241:54260:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.242:54263:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.43:53666:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.57:53708:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.6:53555:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.66:53735:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.67:53738:BGIG0AAX:8D3PG3F3",
    #     "37.202.214.79:53774:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.103:54605:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.129:54683:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.138:54710:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.14:54338:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.178:54830:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.192:54872:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.232:54992:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.29:54383:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.40:54416:BGIG0AAX:8D3PG3F3",
    #     "37.202.215.79:54533:BGIG0AAX:8D3PG3F3",
    #     # Добавьте остальные прокси сюда
    # ]

    # # Преобразуем и выводим результат
    # formatted_proxies = format_proxies(proxies)
    # for proxy in formatted_proxies:
    #     print(proxy)
    # url_test()

    # download_pdf()
    # parsing_page()
    # # Вызов функции с файлом unique_itm_urls.csv
    # parsing_product()
    # # get_responses_from_urls("unique_itm_urls.csv")
    # # parsing()
    # # Запуск функции для обхода директории

    # # get_json()
    # download_xml()
    # pr_xml()
    # parsing_xml()
    # # fetch_and_save()
    # # parsing_csv()
