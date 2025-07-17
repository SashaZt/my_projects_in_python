import asyncio
import xml.etree.ElementTree as ET
from pathlib import Path

import aiohttp
import pandas as pd
from downloader import downloader

from config import Config, logger, paths

config = Config.load()
cookies = {
    "PHPSESSID": "n2uiuqm8e2u1ose7iend6r11l1",
    "astratop": "1",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "max-age=0",
    "dnt": "1",
    "priority": "u=0, i",
    "referer": "https://cci.kg/chlenstvo-v-tpp-kr/chleny-tpp-kr-po-napravlenijam-dejatelnosti/avtotransport-obsluzhivanie-prodazha-i-logistika.html",
    "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "sec-gpc": "1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}


async def download_sitemap(
    url: str, session: aiohttp.ClientSession, save_path: str = "sitemap.xml"
) -> str:
    """
    Асинхронно скачивает sitemap.xml и сохраняет его локально

    Args:
        url: URL для скачивания sitemap
        session: aiohttp сессия
        save_path: путь для сохранения файла

    Returns:
        str: содержимое sitemap.xml
    """

    cookies = {"PHPSESSID": "n2uiuqm8e2u1ose7iend6r11l1", "astratop": "1"}

    try:
        async with session.get(
            url, headers=headers, cookies=cookies, ssl=False
        ) as response:
            response.raise_for_status()
            content = await response.text()

            # Сохраняем файл
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Sitemap успешно скачан и сохранен в {save_path}")
            return content

    except aiohttp.ClientError as e:
        logger.error(f"Ошибка при скачивании sitemap: {e}")
        raise
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        raise


def parse_sitemap_and_filter_urls(
    xml_content: str, filter_pattern: str = "https://cci.kg/chlenstvo-v-tpp-kr"
) -> list:
    """
    Парсит sitemap.xml и извлекает URL, содержащие указанный паттерн

    Args:
        xml_content: содержимое XML файла
        filter_pattern: паттерн для фильтрации URL

    Returns:
        list: список отфильтрованных URL
    """
    try:
        # Парсим XML
        root = ET.fromstring(xml_content)

        # Определяем namespace для sitemap
        namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Извлекаем все URL
        urls = []
        for url_element in root.findall(".//ns:url", namespace):
            loc_element = url_element.find("ns:loc", namespace)
            if loc_element is not None:
                url = loc_element.text
                # Фильтруем URL по паттерну
                if filter_pattern in url:
                    urls.append(url)

        logger.info(f"Найдено {len(urls)} URL с паттерном '{filter_pattern}'")
        return urls

    except ET.ParseError as e:
        logger.error(f"Ошибка парсинга XML: {e}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при извлечении URL: {e}")
        raise


def save_urls_to_csv(urls: list, filename: str = "urls.csv"):
    """
    Сохраняет список URL в CSV файл с помощью pandas

    Args:
        urls: список URL для сохранения
        filename: имя файла для сохранения
    """
    try:
        # Создаем DataFrame
        df = pd.DataFrame(urls, columns=["url"])

        # Сохраняем в CSV
        df.to_csv(filename, index=False, encoding="utf-8")

        logger.info(f"URL успешно сохранены в {filename}")
        logger.info(f"Всего сохранено {len(urls)} URL")

    except Exception as e:
        logger.error(f"Ошибка при сохранении CSV: {e}")
        raise


async def main():
    """
    Основная функция для выполнения всех операций
    """
    sitemap_url = config.client.url_sitemap
    filter_pattern = config.client.filter_pattern

    async with aiohttp.ClientSession() as session:
        # Скачиваем sitemap
        xml_content = await download_sitemap(sitemap_url, session)

        # Парсим и фильтруем URL
        filtered_urls = parse_sitemap_and_filter_urls(xml_content, filter_pattern)

        # Сохраняем в CSV
        if filtered_urls:
            save_urls_to_csv(filtered_urls)
        else:
            logger.warning("Не найдено URL с указанным паттерном")


# Альтернативная функция для парсинга уже сохраненного файла
def parse_saved_sitemap(
    file_path: str = "sitemap.xml",
    filter_pattern: str = "https://cci.kg/chlenstvo-v-tpp-kr",
):
    """
    Парсит уже сохраненный sitemap.xml файл

    Args:
        file_path: путь к XML файлу
        filter_pattern: паттерн для фильтрации URL
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        filtered_urls = parse_sitemap_and_filter_urls(xml_content, filter_pattern)

        if filtered_urls:
            save_urls_to_csv(filtered_urls)
            return filtered_urls
        else:
            logger.warning("Не найдено URL с указанным паттерном")
            return []

    except FileNotFoundError:
        logger.error(f"Файл {file_path} не найден")
        raise
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        raise


# Запуск программы
if __name__ == "__main__":
    # Для запуска основной функции
    # asyncio.run(main())
    asyncio.run(downloader.download_from_csv("urls.csv"))

    # Или для парсинга уже сохраненного файла
    # parse_saved_sitemap()
