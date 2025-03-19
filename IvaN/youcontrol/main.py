import sys
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_directory = current_directory / "html"
json_directory = current_directory / "json"
log_directory = current_directory / "log"
configuration_directory = current_directory / "configuration"
log_directory.mkdir(parents=True, exist_ok=True)
# Пути к файлам
output_csv_file = current_directory / "urls.csv"
txt_file_proxies = configuration_directory / "proxies.txt"
log_file_path = log_directory / "log_message.log"
# Создание директорий, если их нет
html_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
logger.remove()
# 🔹 Логирование в файл
logger.add(
    log_file_path,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {line} | {message}",
    level="DEBUG",
    encoding="utf-8",
    rotation="10 MB",
    retention="7 days",
)

# 🔹 Логирование в консоль (цветной вывод)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{line}</cyan> | <cyan>{message}</cyan>",
    level="DEBUG",
    enqueue=True,
)


# def download_xml(url, filename):
#     response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
#     if response.status_code == 200:
#         with open(filename, "wb") as f:
#             f.write(response.content)
#         return response.content
#     else:
#         print(f"Ошибка при скачивании {url}: {response.status_code}")
#         return None


# def extract_urls(xml_content):
#     urls = []
#     root = ET.fromstring(xml_content)
#     for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
#         urls.append(loc.text)
#     return urls


# def save_to_csv(urls, filename):
#     df = pd.DataFrame({"url": urls})
#     df.to_csv(filename, index=False)


# def main_xml():
#     sitemap_url = "https://youcontrol.com.ua/sitemap.xml"
#     sitemap_content = download_xml(sitemap_url, "sitemap.xml")
#     print("Скачал основной sitemap.xml")

#     company_sitemaps = []
#     root = ET.fromstring(sitemap_content)
#     for loc in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
#         if "company" in loc.text:
#             company_sitemaps.append(loc.text)

#     all_urls = []
#     for i, sitemap in enumerate(company_sitemaps, start=1):
#         sitemap_filename = f"company_sitemap_{i}.xml"
#         sitemap_content = download_xml(sitemap, sitemap_filename)
#         if sitemap_content:
#             print(f"Скачал {sitemap} и сохранил как {sitemap_filename}")
#             urls = extract_urls(sitemap_content)
#             all_urls.extend(urls)

#     save_to_csv(all_urls, "urls.csv")
#     print(f"Всего URL-адресов: {len(all_urls)}")


# def work_csv():
#     # Загрузка файлов CSV
#     urls_df = pd.read_csv("urls.csv", names=["url"])
#     edrpo_df = pd.read_csv("edrpo.csv", names=["edrpo"])

#     # Создание нового столбца 'edrpo' в urls_df
#     urls_df["edrpo"] = urls_df["url"].str.extract(r"/(\d+)/$", expand=False)

#     # Объединение DataFrame по столбцу 'edrpo'
#     matched_df = pd.merge(urls_df, edrpo_df, on="edrpo", how="inner")

#     # Выбор только столбца 'url' и запись в новый файл
#     matched_df[["url"]].to_csv("matched_urls.csv", index=False, header=["url"])


def download_html(edrpo):
    cookies = {
        "spm1": "15428347eb67782ad3b82c8169bfcb4d",
        "_csrf-frontend": "e07ae2dd14dee4b90a01d0eb50a1f88adbb8152e8fcd2cb9aa635cda9cfb86f5a%3A2%3A%7Bi%3A0%3Bs%3A14%3A%22_csrf-frontend%22%3Bi%3A1%3Bs%3A32%3A%22MnsoZcYJ406sUTU8UZ8M7yAfpLEGYXVy%22%3B%7D",
        "hide-ios-homescreen": "2",
        "fref": "798b5c74a0a2037d4f302cd8c2e13fddcb04b838b491a8f25907a4e24e644effa%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22fref%22%3Bi%3A1%3Bs%3A23%3A%22https%3A%2F%2Fwww.google.com%2F%22%3B%7D",
        "utrt": "cb535bea40564d52a76ace7a75adedc29f38b6ab660941cbdf2250e6b7528f3da%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22utrt%22%3Bi%3A1%3Bi%3A5326095%3B%7D",
        "catalog-register-banner": "1",
        "lurl": "dc7aa60bdb42353a4d9e97c4510519848b0b6e305aba003dc34b3769be458c84a%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22lurl%22%3Bi%3A1%3Bs%3A25%3A%22http%3A%2F%2Fyoucontrol.com.ua%2F%22%3B%7D",
        "_gid": "GA1.3.1203388815.1742322293",
        "_gat": "1",
        "_ga_3WKESSJGT2": "GS1.3.1742322293.1.0.1742322293.60.0.1810157129",
        "_gcl_au": "1.1.1203853335.1742322295",
        "_fbp": "fb.2.1742322294725.29787048639901783",
        "_ga_RZYBEYF60J": "GS1.1.1742322294.1.0.1742322294.60.0.0",
        "_ga": "GA1.1.1332084316.1742322293",
        "_hjSessionUser_257557": "eyJpZCI6IjAzM2RlZTZlLTI5ODMtNTBiNy1iNDhjLTIyYmE4MzFjYTVhMiIsImNyZWF0ZWQiOjE3NDIzMjIyOTQ5MDUsImV4aXN0aW5nIjpmYWxzZX0=",
        "_hjSession_257557": "eyJpZCI6IjMxYmNjNjA0LTQxMjgtNDViNy04OGIxLTBlOTYzZjE5OTdkMSIsImMiOjE3NDIzMjIyOTQ5MDYsInMiOjEsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjoxfQ==",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 'lurl=05b5670e5ccc4a601610ac92419f7c5ca460797a6fdb78922f7d5d16475c50a8a%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22lurl%22%3Bi%3A1%3Bs%3A36%3A%22http%3A%2F%2Fyoucontrol.com.ua%2Fsitemap.xml%22%3B%7D',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-full-version": '"131.0.6778.265"',
        "sec-ch-ua-full-version-list": '"Google Chrome";v="131.0.6778.265", "Chromium";v="131.0.6778.265", "Not_A Brand";v="24.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }
    try:
        url = f"https://youcontrol.com.ua/catalog/company_details/{edrpo}/"
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.warning(f"Ошибка при скачивании {url}: {e}")
        return None


def download_and_save(edrpo):
    file_name = f"{edrpo}.html"
    file_path = html_directory / file_name
    if file_path.exists():
        return None
    html_content = download_html(edrpo)
    if html_content:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)
        time.sleep(5)


def main_html():
    # Чтение файла matched_urls.csv
    urls_df = pd.read_csv("matched_urls.csv")
    urls = urls_df["url"].tolist()

    # Создание директории для сохранения HTML-файлов
    # Многопоточное скачивание HTML-файлов
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(download_and_save, url) for url in urls]
        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    # main_xml()
    # work_csv()
    main_html()
