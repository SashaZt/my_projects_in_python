import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from logger import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_xml_file = data_directory / "output.xml"
output_csv_file = data_directory / "output.csv"


def download_xml():

    cookies = {
        "PHPSESSID": "34p6gltkfskqsq7g1nacpf4ele",
        "cookieconsent": '{"g":{"personal":true,"statistics":true,"marketing":true},"v":1,"s":1}',
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "max-age=0",
        "dnt": "1",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        # 'cookie': 'PHPSESSID=34p6gltkfskqsq7g1nacpf4ele; cookieconsent={"g":{"personal":true,"statistics":true,"marketing":true},"v":1,"s":1}',
    }

    response = requests.get(
        "https://www.insportline.eu/sitemap.xml",
        cookies=cookies,
        headers=headers,
        timeout=30,
    )

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(output_xml_file, "wb") as file:
            file.write(response.content)
        logger.info(f"Файл успешно сохранен в: {output_xml_file}")
    else:
        logger.error(f"Ошибка при скачивании файла: {response.status_code}")


def parse_sitemap():
    try:
        # Чтение XML файла
        with open(output_xml_file, "r", encoding="utf-8") as file:
            xml_content = file.read()

        # Парсинг XML
        root = ET.fromstring(xml_content)

        # Указание правильного пространства имен
        namespace = {"ns": "http://www.google.com/schemas/sitemap/0.84"}

        # Шаблон для фильтрации URL'ов: https://www.insportline.eu/число/что-угодно
        pattern = r"^https://www\.insportline\.eu/\d+/.*$"

        # Извлечение URL, соответствующих шаблону
        urls = []
        for url_elem in root.findall(".//ns:url", namespace):
            loc_elem = url_elem.find("ns:loc", namespace)
            if loc_elem is not None and loc_elem.text:
                url = loc_elem.text.strip()
                if re.match(pattern, url):
                    urls.append(url)

        # Вывод количества найденных URL
        logger.info(f"Найдено {len(urls)} URL, соответствующих шаблону")

        # Сохранение в CSV
        url_data = pd.DataFrame(urls, columns=["url"])
        url_data.to_csv(output_csv_file, index=False)
        logger.info(f"URL адреса сохранены в {output_csv_file}")

        return urls

    except FileNotFoundError:
        logger.error(f"Ошибка: Файл {output_xml_file} не найден")
        return []
    except ET.ParseError as e:
        logger.error(f"Ошибка при парсинге XML: {e}")
        return []
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
        return []


if __name__ == "__main__":
    # download_xml()
    parse_sitemap()
