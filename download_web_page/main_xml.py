import random
import xml.etree.ElementTree as ET

import pandas as pd
import requests
from configuration.logger_setup import logger


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
    save_path = "sitemap_0.xml"

    cookies = {
        "euconsent-v2": "CQJAbUAQJAbUAAjABCENBRFgAP_AAEPAACgAIzBV5CpMDWFAMHBRYNMgGYAW10ARIEQAABCBAyABCAGA8IAA0QECMAQAAAACAAIAoBABAAAAAABEAEAAIAAAAABEAAAAAAAIIAAAAAEQQAAAAAgAAAAAEAAIAAABAAQAkAAAAYKABEAAAIAgCAAAAAABAAAAAAMACAAIAAAAAAIAAAAAAAIAAAAAAEEAARAyyAYAAgABQAFwAtgD7AJSAa8A_oC6AGCAMhAZYAMEgQgAIAAWABUADgAIIAZABoAEQAJgAVQA3gB-AEJAIYAiQBLACaAGGAMoAc8A-wD9AIoARoAkQBcwDFAG0ANwAcQBQ4C8wGrgOCAeOBCEdAjAAWABUADgAIIAZABoAEQAJgAVQAuABiADeAH6AQwBEgCWAE0AMMAZQA0QBzwD7AP2AigCLAEiALmAYoA2gBuADiAIvATIAocBeYDLAGmgNXAeOQgGAALACqAFwAMQAbwBzgEUAJSAXMAxQBtAHjkoB4ACAAFgAcACIAEwAKoAXAAxQCGAIkAfgBcwDFAIvAXmBCEpAdAAWABUADgAIIAZABoAEQAJgAUgAqgBiAD9AIYAiQBlADRAHPAPwA_QCLAEiALmAYoA2gBuAEXgKHAXmAywBwQDxwIQlQAQACgAtgAA.YAAAAAAAAAAA",
        "consentUUID": "6cb56b4f-3f34-435d-b1d3-c1977cb47e33_38",
        "consentDate": "2024-12-02T11:46:43.209Z",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "max-age=0",
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
        "https://ramiz.pl/xml?key=94255d59993348493376710e55697842&lang=pl&curr=pln",
        # cookies=cookies,
        headers=headers,
        proxies=proxies_dict,
        timeout=200,
    )

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


def parsin_xml():
    # Чтение файла sitemap.xml
    with open("sitemap_1.xml", "r", encoding="utf-8") as file:
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


if __name__ == "__main__":
    download_xml()
    # parsin_xml()
