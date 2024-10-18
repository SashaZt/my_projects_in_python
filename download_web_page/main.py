import requests
import json
import aiohttp
import asyncio
import re
import requests
import urllib3
import ssl
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from configuration.logger_setup import logger
import random
from bs4 import BeautifulSoup
import pandas as pd
from pathlib import Path
import xml.etree.ElementTree as ET
import os
from tqdm import tqdm

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_html():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        ".Nop.RecentlyViewedProducts": "178610",
        ".Nop.Culture": "c%3Dru-RU%7Cuic%3Dru-RU",
        ".Nop.Antiforgery": "CfDJ8Fe-XiX5m9tJs4SLBj0Ue5tdYndtOrCzDO1X4DwI__BybUMXsKBxYo2Kb3wyd0wruYg1cSKGvDp87JJpptTMiFulvk8IlZOeI2qD5eA4_hEIdY-Bh0_v3F36ZxcDVmi1xalh79DmUh-SycnznTZgMKY",
        ".Nop.Customer": "21a4bb11-fef9-4bba-bb6c-7b316a6ce753",
        "_ms": "fbc661d6-8922-4e09-ad64-df1810d767f7",
        "biatv-cookie": "{%22firstVisitAt%22:1729074594%2C%22visitsCount%22:1%2C%22currentVisitStartedAt%22:1729074594%2C%22currentVisitLandingPage%22:%22https://home-club.com.ua/ru/ua%25C2%25A0%22%2C%22currentVisitUpdatedAt%22:1729088324%2C%22currentVisitOpenPages%22:15%2C%22campaignTime%22:1729074594%2C%22campaignCount%22:1%2C%22utmDataCurrent%22:{%22utm_source%22:%22(direct)%22%2C%22utm_medium%22:%22(none)%22%2C%22utm_campaign%22:%22(direct)%22%2C%22utm_content%22:%22(not%20set)%22%2C%22utm_term%22:%22(not%20set)%22%2C%22beginning_at%22:1729074594}%2C%22utmDataFirst%22:{%22utm_source%22:%22(direct)%22%2C%22utm_medium%22:%22(none)%22%2C%22utm_campaign%22:%22(direct)%22%2C%22utm_content%22:%22(not%20set)%22%2C%22utm_term%22:%22(not%20set)%22%2C%22beginning_at%22:1729074594}}",
        "bingc-activity-data": "{%22numberOfImpressions%22:2%2C%22activeFormSinceLastDisplayed%22:789%2C%22pageviews%22:8%2C%22callWasMade%22:0%2C%22updatedAt%22:1729089124}",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': '.Nop.RecentlyViewedProducts=178610; .Nop.Culture=c%3Dru-RU%7Cuic%3Dru-RU; .Nop.Antiforgery=CfDJ8Fe-XiX5m9tJs4SLBj0Ue5tdYndtOrCzDO1X4DwI__BybUMXsKBxYo2Kb3wyd0wruYg1cSKGvDp87JJpptTMiFulvk8IlZOeI2qD5eA4_hEIdY-Bh0_v3F36ZxcDVmi1xalh79DmUh-SycnznTZgMKY; .Nop.Customer=21a4bb11-fef9-4bba-bb6c-7b316a6ce753; _ms=fbc661d6-8922-4e09-ad64-df1810d767f7; biatv-cookie={%22firstVisitAt%22:1729074594%2C%22visitsCount%22:1%2C%22currentVisitStartedAt%22:1729074594%2C%22currentVisitLandingPage%22:%22https://home-club.com.ua/ru/ua%25C2%25A0%22%2C%22currentVisitUpdatedAt%22:1729088324%2C%22currentVisitOpenPages%22:15%2C%22campaignTime%22:1729074594%2C%22campaignCount%22:1%2C%22utmDataCurrent%22:{%22utm_source%22:%22(direct)%22%2C%22utm_medium%22:%22(none)%22%2C%22utm_campaign%22:%22(direct)%22%2C%22utm_content%22:%22(not%20set)%22%2C%22utm_term%22:%22(not%20set)%22%2C%22beginning_at%22:1729074594}%2C%22utmDataFirst%22:{%22utm_source%22:%22(direct)%22%2C%22utm_medium%22:%22(none)%22%2C%22utm_campaign%22:%22(direct)%22%2C%22utm_content%22:%22(not%20set)%22%2C%22utm_term%22:%22(not%20set)%22%2C%22beginning_at%22:1729074594}}; bingc-activity-data={%22numberOfImpressions%22:2%2C%22activeFormSinceLastDisplayed%22:789%2C%22pageviews%22:8%2C%22callWasMade%22:0%2C%22updatedAt%22:1729089124}',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://home-club.com.ua/ru/novynky",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://home-club.com.ua/ru/sku-s89918634",
        cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba_0.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    logger.info(response.status_code)


def get_json():

    response = requests.post(
        "https://prom.ua/graphql", cookies=cookies, headers=headers, json=json_data
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
    save_path = "sitemap.products.xml"
    url = "https://www.ua-region.com.ua/sitemap.xml"
    cookies = {
        "G_ENABLED_IDPS": "google",
        "PHPSESSID": "d7tptvp0pdt9s2n4eo585c7tp1",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 'Cookie': 'G_ENABLED_IDPS=google; PHPSESSID=d7tptvp0pdt9s2n4eo585c7tp1',
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    # Отправка GET-запроса на указанный URL
    response = requests.get(url, cookies=cookies, headers=headers)

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
    html_folder = Path("html")

    # Множество для хранения уникальных itm_value
    unique_itm_values = set()

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_folder.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
            # Создать объект BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            # Найти все <div> с классом 'str-quickview-button str-item-card__property-title'
            div_elements = soup.find_all(
                "div", class_="str-quickview-button str-item-card__property-title"
            )
            # Пройтись по каждому найденному элементу и извлечь itm из атрибута data-track
            for div in div_elements:
                data_track = div.get("data-track")
                if data_track:
                    # Преобразовать значение JSON обратно в словарь
                    data = json.loads(data_track.replace("&quot;", '"'))
                    itm_value = data.get("eventProperty", {}).get("itm")
                    if itm_value:
                        unique_itm_values.add(itm_value)

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


if __name__ == "__main__":
    get_html()
    # parsing_page()
    # Вызов функции с файлом unique_itm_urls.csv
    # parsing_product()
    # get_responses_from_urls("unique_itm_urls.csv")
    # parsing()
    # Запуск функции для обхода директории

    # get_json()
    # download_xml()
    # parsing_xml()
    # fetch_and_save()
    # parsing_csv()
