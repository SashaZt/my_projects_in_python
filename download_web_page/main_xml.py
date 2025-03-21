import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

current_directory = Path.cwd()
xml_directory = current_directory / "xml"
log_directory = current_directory / "log"

log_directory.mkdir(parents=True, exist_ok=True)
xml_directory.mkdir(parents=True, exist_ok=True)
log_file_path = log_directory / "log_message.log"

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


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def download_xml():
    proxies = load_proxies()  # Загружаем список всех прокси
    proxy = random.choice(proxies)  # Выбираем случайный прокси
    proxies_dict = {"http": proxy, "https": proxy}

    cookies = {
        "ikexp_id": "4ae34af6-60c6-4801-89ff-8080a441f26d",
        "ak_bmsc": "63624010FCFAF059993FE3731D18C012~000000000000000000000000000000~YAAQHwxAF05yZa6VAQAAwuC2uBuQuyxHPgi1ZcY9osMYW4hOPNAGPNItdPFFUdZpszT5rKClPsrSTa0HqJjPfjhu1UojeTVNeKoURT/ikcmmsPuXe0q5H8Gv0uCwJGejK/lVzT4B+xy+K1blRrGsPeHHRkAVkJgugqOv+s3bbHPFjy27pZTpk3t3AJ4dql2S6a21EiqxpFlgPYy1N4bYFZ7xLZuO84Now434qDfC3pduUHjOEvBPay/B4h5BQXe/1irzAfnrg1bbkvgFFC8eM8jsG++HjYNtxF/AZkRXLznopx+XweMCP4a+2yndvEzUA1IZloP9dn8Bq/e/WzEt2PV02REAwPoXEV6x85Tgb74u4cXGTopG1NwhKssreNRcuhfm1vavRY8=",
        "ikea_cookieconsent_pl": "%7B%221%22%3Atrue%2C%222%22%3Atrue%2C%223%22%3Atrue%2C%224%22%3Atrue%7D",
        "_fbp": "fb.1.1742560761431.444801568",
        "rtbhouse-split": "1",
        "episod_id": "1742560761504.f4ee1238",
        "BehtarIKEA": "7336e9bf-c5be-4abc-8ce1-f3c50fa4c270",
        "PIM-SESSION-ID": "pzixFKEDlO0aNhE0",
        "weDareSessionId": "5oebr-hrmlk-5jy",
        "_cs_mk_ga": "0.5746547625992453_1742562698666",
        "_abck": "F62F3894666D693DDA831F7A6E61F6B9~0~YAAQHAxAF//qHqmVAQAALavVuA2q8WFMQRBWH43KGH+5Ba1poiVvUoznX3tDuWZ0kWkjiRi6g1TnnlFMB4/tZ5MXLBnYa3nia5XJ/2CvQrXR/EKL0X61gTC03nghSnphF5QCC2rlwPmVpcvQk8UcG/fVJ9oH2QhSfUIOAwKH9xpb8+QJOMeYVlM9/zreuprbdO0vgS4dOLzhfOrFzSVyUrMXMRiwgSVP9NqbYQlCp2ai52qdwXH9e5ten/twYS9TKTePiUh251nFfcO22w0r/8jzIYGFCDuRtLdq3kImjHgtNkUwF0NteElo746WQhTJEI4mlm839ciKRXDp2tD58GreyT6eIwcpPxE4tmLp/Waqzypf2ek2mAZh7HnwtRZ+GnU1Q+iEYeWEOnBNW9h5T/EpCQbxq8+U8mJ2SeetwZN9ua4HS6aAr/XBWOxkOHKC10eNaGudMj0Ap/Ph4XfhXCDVxpRqqypKiI6VFN38Y2RCiML4Wg48hTY=~-1~-1~1742564350",
        "episod_session_id": "1742560761504.bd3bd789.1.1742563088177",
        "bm_sv": "34073B5BB713B0BE4B9D321DCB820AE8~YAAQFwxAF/d/lqiVAQAAxIPduBt4QfzIbqtpFjIX5nJXPN1vx4bSUsqKdhHw34Bn556sW/wDVkhfY0p3pm7nDsmWgMZu5DAAoPiYqKftTfHsuxCKIrqz5oQ2lN04Y9OWLuAD1Kh4vAhN/g0jA8mvDLu+gaASszOqDZSZZgyWEcw1YFcrWiK3cz5zm97yk8tVRq/gD/yZ17zVvmFFZZctWrBHkJP0th75fgI6i5n87mDsaLQDgM1L6jahwALTXmLD~1",
        "bm_sz": "6C0ED6E38C0ECA35FB70C981F1ADAE5D~YAAQFwxAF/h/lqiVAQAAxIPduBscyVdbfLzmjiN6zjXpG/5VYksQLL3n8CrhyDp0CdoOsVGkUePS671Ge54HHfjq401ZbIwBpPb4EOUQ8lwMuZNBMqJC0Z+nINR1AAo5rmKnkkCx0Z1uNg1RX6sMYI8PzXzBo+v3wzplsOEAfyrRvuW9u/um96ogFa6VR7GhreNOovjW/DF03CaxmS3tusAQzQ4bdpo5tognIeMMDsZ+XlnuXe2LQk2brAEqs7TxtXYhqQ3Rqi7rxiD36NsJ8JVdU7QXTjCO/AwMyZQVK9hVoCVgX+qqVByN3H5Rlup8SPvCKV9MiHeq8EatVT8Pw9wj1ZutDYyvIj/3gWzjOV8NdSTPX4EpDgP4l5oUPvIPBtXhpyLWr/Y8HFdLHv+TWbMYvUfs3Ka3wIHxzQ4AH/j0EKEYtcu57Lww/imSo4jVhHZiuec8SQzeSiCUBJUcOzBXC+ofofKINZ8gk8a0OFX/OCafh1xuoQG/lgRTYESBtw==~4273222~4342841",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://www.ikea.com/sitemaps/prod-pl-PL_6.xml",
        cookies=cookies,
        headers=headers,
        timeout=30,
    )
    save_path = "prod-pl-PL_6.xml"
    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


def parse_sitemap_urls():
    """
    Парсит XML sitemap и возвращает список URL из тегов <url><loc>

    Args:
        file_path (str): путь к XML файлу

    Returns:
        list: список URL-ов
    """
    urls = []
    for xml_file in xml_directory.glob("*.xml"):
        try:
            # Парсим XML файл
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Определяем пространство имен (namespace), если оно есть
            namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}

            # Ищем все теги <url> и извлекаем <loc>
            for url in root.findall(".//sitemap:url", namespace):
                loc = url.find("sitemap:loc", namespace)

                if loc is not None and loc.text:
                    urls.append(loc.text)

            # return urls

        except ET.ParseError as e:
            print(f"Ошибка парсинга XML: {e}")
            return []
        except FileNotFoundError:
            print(f"Файл {xml_file} не найден")
            return []
    logger.info(f"Найдено {len(urls)} URL-ов")


def parsin_xml():
    with open("sitemap_0.xml", "r", encoding="utf-8") as file:
        xml_content = file.read()

    root = ET.fromstring(xml_content)
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    urls = [
        url.text.strip()
        for url in root.findall(".//ns:loc", namespace)
        if not url.text.strip().startswith("https://bsspart.com/ru/")
    ]

    url_data = pd.DataFrame(urls, columns=["url"])
    url_data.to_csv("urls.csv", index=False)


def xml_temp():
    import xml.etree.ElementTree as ET

    import pandas as pd

    # Загрузка XML-файла
    xml_file = "index.xml"  # Укажите путь к вашему XML-файлу

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Найти секцию offers
    offers_section = root.find(".//offers")

    # Проверяем, что offers_section найден
    if offers_section is not None:
        # Извлекаем URL-адреса
        urls = [
            offer.find("url").text
            for offer in offers_section.findall("offer")
            if offer.find("url") is not None
        ]

        # Создаем DataFrame
        df = pd.DataFrame(urls, columns=["url"])

        # Сохраняем в CSV-файл
        csv_filename = "urls.csv"
        df.to_csv(csv_filename, index=False)

        print(f"Сохранено в {csv_filename}")
    else:
        print("Ошибка: Секция <offers> не найдена в XML.")


if __name__ == "__main__":
    # download_xml()
    parse_sitemap_urls()
    # parsin_xml()
    # xml_temp()
