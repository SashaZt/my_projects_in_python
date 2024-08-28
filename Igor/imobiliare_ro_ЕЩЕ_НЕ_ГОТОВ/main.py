import requests
import random
import csv
from pathlib import Path
from selectolax.parser import HTMLParser
from configuration.logger_setup import logger
import ssl
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from phonenumbers import NumberParseException
from configuration.logger_setup import logger
from selectolax.parser import HTMLParser
from mysql.connector import errorcode
import xml.etree.ElementTree as ET
from pathlib import Path
import mysql.connector
import phonenumbers
import pandas as pd
import threading
import datetime
import requests
import random
import locale
import csv
import re

cookies = {
    "imovzt": "5032940066",
    "cookies_cleared_20230614": "eyJpdiI6InA0emFtQW9kaGJOUlREemRjTmJPNmc9PSIsInZhbHVlIjoiNmljZVdpdXIwemJvdzU5cnJ1bDB0SlExbzBCdkUwd1hjQmRLR3VTTUhJZkpDQXlkSUYxMzBNaHZzNEtGcW5jSyIsIm1hYyI6IjVkODRhOWMyMGE3NTNlYWJmOWUzMjNhYzJmZDFjMGM1MjFmMTAxMTg4NjJlNmVhNzA3YmViNjE4MjFkYzhjZDgiLCJ0YWciOiIifQ%3D%3D",
    "_cq_duid": "1.1724069488.Kgtvi9X73GUfHEWV",
    "_cq_suid": "1.1724069488.ejcpAQtvsHhYcAHI",
    "imo_visitor_id_cookie": "imo_visitor_id_cookie-39f1930a-d7b8-4408-befd-3255430c77fd",
    "OptanonAlertBoxClosed": "2024-08-26T05:19:25.974Z",
    "smcx_457240670_last_shown_at": "1724649746804",
    "exitIntentRecomandate": "eyJpdiI6IjJjeWhNc3lzbFdMVGNCRzJxK2hncFE9PSIsInZhbHVlIjoiRzdtU2NPdUJzdTlQLzZzZ3VKRUcxeWU5WjU4TXc3ZktGckJCcHdPb1B1bnpsUllmaFAxdmVtSVNZM1BkUmh1ZiIsIm1hYyI6IjNjODRjZTdkMzA1YTU5OWJjMzdhZDFmY2EwMzE4ZGRmMmNkNjRlODI0YjQ4MDlhNTc1YzZkMjFiMWEyNGYyZDUiLCJ0YWciOiIifQ%3D%3D",
    "recent_searches": "eyJpdiI6IlQ0YW9jbWdRSWl5cVdGOXg1QWpkUVE9PSIsInZhbHVlIjoiREd2SWVsWDQyczhDUnBZMk1tWkF3bSt5V1VmeGREWEhtMFlUMkRYcEg2OFBuTWFXNFpYdFdVS2lJNllUTE1uRGg3NGZUdmE3bTNCRHBmVnZKUitXREpwbmxmeERwZU9LR3k1RnhKSUk0dHI4em8zLzlpZUZFVEhNT1BRZnpiZWJUdG5EdmhMM1lZR3l5YU15ckYrQzhNalQ4aW1Gb1RLaWlMQjVVR3RtblFsaGsxRmNsTXJrQk1uZjNZVWdiZ0VUMHpsUFRkaG93S2lKMEFqNmxjYklyYktNVTJmTDVPVkhwODFGM1Bpb1QyOVJGbTUzc3RnOVk3VHQvRGxCSGtjZ05aWmR3SjFHSkJkZ2tHVHdxTkZXSnRhcjlud0UxOStkOTFLRG5UM2J3alVFN3FKZGNrN0VQSjlVMmt5clJETWxHcmgyZHI3aVg5SlBGNzUvdEU3SjcvNnNuMmdHSHhLN3VTQ0EvQjFVTzl4S3hGdFlFMk10WEJLcGNQazR3Unh4eXZDeVNFamsrTzBJNTljTmlpUXlsaWhFbFFWczZRMG43UHIwUk96RUR4OWFjVHNJZzBDR1BPZlRZRWZ2bU54VzBaczBuTmYycjZkVWg3eDQ2RHZpNWVIY3pjSHdJN2NRNlNKU3hpUlBEaFROL0JrOUQreXlBL2E5WWQzRjEyYUtiQnNxbFZWVS96ZXhWVjRaeFNyMjNUY1hWNDhTbnFwMFpEKzBJYXlTVmhsQUYzSHRQcFRZY2xIUmFnOHRRbkEzSGcrbHJZaXM3aWVVOWtKU3lZOHlZQT09IiwibWFjIjoiZWRlMzNjOTdkMThkNDg3MzI2Yjg4NTg4ZTkwZDE4MmNkODkzN2FmMTQwYTNhNjY1ZTVlOTE2OWYzY2NiYzdkZCIsInRhZyI6IiJ9",
    "map_projects_first_visit": "eyJpdiI6IkhYQW9lU3ZJZWFURFFFMG9JZTJIY2c9PSIsInZhbHVlIjoiVmJ4dkFLTCszTC9yeVJMYjFrcHRjdzYxN25kMUNsMERPSmY5VVY1Yi9CM1hZN08rVy9CNHZKNnIwSmRCdUdmaiIsIm1hYyI6ImJjMTI3N2VlOWY2NTllMDE0YjM0MWVlYjQwNzdkZjE5NjQ2ZDVhYTNiMzA5YTUwYjA3ZTQ4Zjk2OWJhMTFmNTkiLCJ0YWciOiIifQ%3D%3D",
    "map_listings_first_visit": "eyJpdiI6Ik1PVTJVZ3Fvcmp3YWxUd2ZhNmF4NlE9PSIsInZhbHVlIjoiRkRXUDVCeXN3S0JySkJNcU5CbmpVL29MS0ZXZVYzZDdReUlEMTFUa3hLcWJpVlRUZGd6UmZITU9UUWZtdkJJNSIsIm1hYyI6IjU0Y2M2MTMxZDU3MGNkZTE1NTljMjE5ZDZhMTZlNjM0ZjIzZmI2NjcxNDRhMWQ1YmRiMzA1ZWFlYzE0ZWFlY2UiLCJ0YWciOiIifQ%3D%3D",
    "show_recommendations": "eyJpdiI6IkZ6bW1yQWVOaWVWWE9ZTTZMSEx6dlE9PSIsInZhbHVlIjoidXhjeHpkS2htOXh5VXZGV084SHNpc2lwMUJGOFBGdDNxZXJKOGtCRWtZa3BXVXhqYlNhMEFIRkorVGlFVGY1cyIsIm1hYyI6ImY5OTczM2M5N2YzNDQ0ZjBjOWNiZDZiN2FjM2NiYzE2YmZmODE0MjQzZDk3ZGJlNTczNDAxNGU1ZjJkYTNjNzgiLCJ0YWciOiIifQ%3D%3D",
    "__cf_bm": "h8sMpffsCydWl.c64t37RJcni1Z.wIvdXy96MLorAqs-1724758548-1.0.1.1-gCeWaKXh7Jnz9E2vENPikCwuRLYE666my0NkZT04tPTUkdnNWNtOsX.Mgx37hJKMKjR.NtC1UoxzYDYcZ7a7Ig",
    "OptanonConsent": "isGpcEnabled=0&datestamp=Tue+Aug+27+2024+14%3A35%3A48+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202402.1.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=5c0f0622-d46b-4c50-a3c6-fba52f21ed53&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1%2CC0003%3A1&geolocation=UA%3B18&AwaitingReconsent=false",
    "_cq_pxg": "3|72442310109",
    "datadome": "Vw_3V25lx6A6LS3VPoxHwp4engnUrsqAuWD395rf0vI4hTzSQ_EAx7QVMLvsVRUq_ID2Izm3PvV6sCa7zgU5ZjRxmr2a41IAliW6GMMmldhm_KdM2rurGiYrcK4ByHSx",
    "XSRF-TOKEN": "eyJpdiI6IjlIMlZEM3Z5ZjlSRlQxSmRoQXNZcHc9PSIsInZhbHVlIjoia1RCazR0VVZDOW5yVUltSzMvb1FoWERBUXlUQXBzYkhWUFJyb1VMYnhpM1hJeTUwYmNTTGRDelBQMEF2YXhXT2NNcjN0cThnditCUlQwaVE4VnY5aTJ1L1BmNVNRUURxN0doWHhSRjBWcG5RNEdJaHNRbEx2T0hHSFRSMnIxSGciLCJtYWMiOiIyMWEwNWNiYjU1ZTQ4N2UzZDhjNTAxMjIxYzZmMjgyYjQwMTJjNzQ5N2M3NmZmNTY5ZmY0MDNhZTVhNGY2MTAwIiwidGFnIjoiIn0%3D",
    "imobiliare_session": "eyJpdiI6Ik1CczNWc0YzVVhRV3FpZk9oeUIwL2c9PSIsInZhbHVlIjoiQ1Z5eXNYeVpSNHhuTDJ0dW1yYW9SR1Z4T0QrR0ZqQ3pudjlsU1JrS1doTWZXcC9LQXRIOU5HcXo4TXhZRHRsMmxOdmt5Y0F3UW1GMkxqdncvV3Y5YkR6cjJHdk04Y0ZNaG1qTEorL1RhQlVaSG9hNitYcmpqYVFzeEZ1MFczWWkiLCJtYWMiOiJhZjIyYzA5OWRmMjY3ZDE4MTkyYjAwZGQzZjAyMmVmMTE0NjIwNGZhMTk5ZTU5NzY4ZjE5NjlmMmI0ZDFjNzM0IiwidGFnIjoiIn0%3D",
    "experiments": "eyJpdiI6InNsZVhaNXh6UjhmaG9sWmxqWEVSamc9PSIsInZhbHVlIjoiSk10eDhvSUJORUdaN2tOSVN0M1hMSmE3U2NpTXJYaEtNV0dQRktiN3JEWE1kY0txT1o2VzdNSGNrWUVLMUtmUWppN2gvMjJ3S2JDV3FIOEEzT2ZlN0lLcFpWQ1Q3UEZuWjZsN0hPVGF4RVlmcHVyMkJCNzdhelJSMmNpbDlBNzgiLCJtYWMiOiIzMDAyMTRmNjhjZDM4ODJlMjFkYzYwOTdhNWVkZDAwZmVlZGU4ZDg0NzYxYzZhNjk4NjI1NzkyNWIxZGJhZjRjIiwidGFnIjoiIn0%3D",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "referer": "https://www.imobiliare.ro/oferta/apartament-de-inchiriat-sector-1-pipera-mobilat-2-camere-229194746",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
}
# Параметры подключения к базе данных
config = {"user": "", "password": "", "host": "", "database": ""}

romania_phone_patterns = {
    "full": r"\b((?:00|40)?\d{6,9})\b",  # Номер может начинаться с '00', '40', или без кода страны
    "split": r"(40\d{6,9})",  # Номера, начинающиеся с '40', и за ними от 6 до 9 цифр
    "final": r"\b(\d{6,9})\b",  # Только от 6 до 9 цифр, если код страны отсутствует
    "codes": [40],  # Код страны для Румынии
}
current_directory = Path.cwd()
data_directory = current_directory / "data"
xml_directory = data_directory / "xml"
data_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)

# Файлы для записи и проверки URL
csv_file_path = data_directory / "output.csv"
csv_file_successful = data_directory / "urls_successful.csv"


def load_proxies():
    file_path = "1000 ip.txt"
    # Загрузка списка прокси из файла
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    return proxies


def extract_urls_and_save_to_csv():
    # Установка директорий для логов и данных

    # Шаблон для поиска нужных URL
    url_pattern = re.compile(r"^https://www\.imobiliare\.ro/oferta/.*")

    # Список URL для обработки
    sitemap_urls = [
        "https://www.imobiliare.ro/sitemap-project-listings-ro.xml",
        "https://www.imobiliare.ro/sitemap-international-listings-ro.xml",
        "https://www.imobiliare.ro/sitemap-listings-index-ro.xml",
    ]

    # Список для хранения всех URL
    all_urls = []
    proxies = load_proxies()  # Загружаем список всех прокси
    logger.info("Обработка первых двух ссылок")
    for sitemap_url in sitemap_urls[:2]:
        proxy = random.choice(proxies)  # Выбираем случайный прокси
        proxies_dict = {"http": proxy, "https": proxy}
        response = requests.get(
            sitemap_url,
            proxies=proxies_dict,
            headers=headers,
            cookies=cookies,
        )
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()

        for url in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
            loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
            if url_pattern.match(loc):
                all_urls.append(loc)

    logger.info("Обработка третьей ссылки")
    response = requests.get(sitemap_urls[2])
    tree = ET.ElementTree(ET.fromstring(response.content))
    root = tree.getroot()

    for sitemap in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"):
        loc = sitemap.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
        response = requests.get(loc)
        sub_tree = ET.ElementTree(ET.fromstring(response.content))
        sub_root = sub_tree.getroot()

        for url in sub_root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url"):
            loc = url.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text
            if url_pattern.match(loc):
                all_urls.append(loc)

    logger.info("Сохранение всех URL в основной CSV файл")
    with csv_file_path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["url"])
        for url in all_urls:
            writer.writerow([url])

    # # Сохранение успешных URL в отдельный CSV файл (если требуется)
    # with csv_file_successful.open("w", newline="") as file:
    #     writer = csv.writer(file)
    #     writer.writerow(["url"])
    #     for url in all_urls:
    #         writer.writerow([url])


if __name__ == "__main__":
    extract_urls_and_save_to_csv()
