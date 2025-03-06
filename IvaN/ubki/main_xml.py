import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests
from loguru import logger

current_directory = Path.cwd()
sitemaps_directory = current_directory / "sitemaps"
urls_directory = current_directory / "urls"
log_directory = current_directory / "log"
log_directory.mkdir(parents=True, exist_ok=True)
urls_directory.mkdir(parents=True, exist_ok=True)
sitemaps_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"
all_urls_file = urls_directory / "all_urls.txt"
legal_file = current_directory / "legal.csv"
fop_file = current_directory / "fop.csv"


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
cookies = {
    "_csrf": "c1e6328d4d1a00430f580954cd699bfcb582e349d7cdb35b0fc25fc69f79504fa%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22sPIghgsE62pvjuIdspysobQGcw1EBt3j%22%3B%7D",
    "device-referrer": "https://edrpou.ubki.ua/ua/FO12726884",
    "LNG": "UA",
    "device-source": "https://edrpou.ubki.ua/ua/01056190",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=0, i",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "cross-site",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
}


# Функция для скачивания XML файла
def download_xml(url, save_path=None, force_download=False):
    try:
        # Проверяем существование файла, если это не основной sitemap и force_download=False
        if save_path and Path(save_path).exists() and not force_download:
            logger.info(f"Файл уже существует, пропускаем скачивание: {save_path}")
            with open(save_path, "rb") as f:
                return f.read()

        logger.info(f"Скачивание файла: {url}")
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()

        if save_path:
            with open(save_path, "wb") as f:
                f.write(response.content)
            logger.info(f"XML файл сохранен: {save_path}")

        return response.content
    except Exception as e:
        logger.warning(f"Ошибка при скачивании {url}: {e}")
        return None


# Функция для парсинга основного sitemap.xml и получения ссылок на дочерние sitemaps
def parse_sitemap_index(xml_content):
    sitemap_urls = []
    try:
        root = ET.fromstring(xml_content)
        # Определяем пространство имен
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Находим все элементы <sitemap>
        for sitemap in root.findall(".//sm:sitemap", namespace):
            loc = sitemap.find("sm:loc", namespace)
            if loc is not None and loc.text:
                sitemap_urls.append(loc.text)

        return sitemap_urls
    except Exception as e:
        logger.warning(f"Ошибка при парсинге sitemap index: {e}")
        return []


# Функция для парсинга отдельного sitemap файла и извлечения URL страниц
def parse_sitemap(xml_content):
    page_urls = []
    try:
        root = ET.fromstring(xml_content)
        # Определяем пространство имен
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        # Находим все элементы <url>
        for url in root.findall(".//sm:url", namespace):
            loc = url.find("sm:loc", namespace)
            if loc is not None and loc.text:
                page_urls.append(loc.text)

        return page_urls
    except Exception as e:
        logger.warning(f"Ошибка при парсинге sitemap: {e}")
        return []


def split_urls_by_type():
    """
    Функция для разделения URL-адресов из all_urls.txt на два отдельных файла:
    - legal.csv для URL вида https://edrpou.ubki.ua/ua/24391608
    - fop.csv для URL вида https://edrpou.ubki.ua/ua/FO1171076

    Фильтрует только URL с префиксом /ua/, игнорируя URL с /en/
    """
    all_urls_file = urls_directory / "all_urls.txt"
    legal_file = current_directory / "legal.csv"
    fop_file = current_directory / "fop.csv"

    # Проверяем, существует ли исходный файл
    if not all_urls_file.exists():
        logger.error(f"Файл {all_urls_file} не найден!")
        return

    # Счетчики для статистики
    legal_count = 0
    fop_count = 0
    other_count = 0
    filtered_out_count = 0

    # Регулярные выражения для проверки типов URL
    # Только украинская версия (ua) для юридических лиц
    legal_pattern = re.compile(r"https://edrpou\.ubki\.ua/ua/\d+$")
    # Только украинская версия (ua) для ФОП
    fop_pattern = re.compile(r"https://edrpou\.ubki\.ua/ua/FO\d+$")

    # Регулярное выражение для обнаружения английских версий (для статистики)
    en_pattern = re.compile(r"https://edrpou\.ubki\.ua/en/")

    # Открываем файлы для записи
    with open(legal_file, "w", encoding="utf-8") as legal_out, open(
        fop_file, "w", encoding="utf-8"
    ) as fop_out, open(all_urls_file, "r", encoding="utf-8") as urls_in:

        # Записываем заголовки CSV
        legal_out.write("url\n")
        fop_out.write("url\n")

        # Обрабатываем каждый URL
        for line in urls_in:
            url = line.strip()
            if not url:
                continue

            # Проверяем, является ли URL английской версией
            if en_pattern.match(url):
                filtered_out_count += 1
                continue

            if legal_pattern.match(url):
                # Это юридическое лицо (украинская версия)
                legal_out.write(f"{url}\n")
                legal_count += 1

            elif fop_pattern.match(url):
                # Это ФОП (украинская версия)
                fop_out.write(f"{url}\n")
                fop_count += 1

            else:
                # Другой тип URL
                other_count += 1

    # Выводим статистику
    logger.info(f"Обработка завершена!")
    logger.info(f"Юридические лица (legal.csv): {legal_count}")
    logger.info(f"ФОП (fop.csv): {fop_count}")
    logger.info(f"Отфильтровано английских версий: {filtered_out_count}")
    logger.info(f"Другие URL: {other_count}")
    logger.info(
        f"Всего обработано URL: {legal_count + fop_count + other_count + filtered_out_count}"
    )

    return {
        "legal_count": legal_count,
        "fop_count": fop_count,
        "filtered_en_count": filtered_out_count,
        "other_count": other_count,
        "total": legal_count + fop_count + other_count + filtered_out_count,
    }


# Основная функция
def main():
    sitemap_url = "https://edrpou.ubki.ua/sitemap.xml"

    # Скачиваем основной sitemap.xml (всегда обновляем)
    logger.info(f"Скачивание главного sitemap: {sitemap_url}")
    main_sitemap = sitemaps_directory / "main_sitemap.xml"

    # Для основного sitemap всегда делаем запрос (force_download=True)
    main_sitemap_content = download_xml(sitemap_url, main_sitemap, force_download=True)

    if not main_sitemap_content:
        logger.warning("Не удалось скачать основной sitemap.xml. Завершение программы.")
        return

    # Парсим основной sitemap.xml и получаем ссылки на дочерние sitemaps
    sitemap_urls = parse_sitemap_index(main_sitemap_content)
    logger.info(f"Найдено {len(sitemap_urls)} дочерних sitemap-файлов")

    child_sitemaps = sitemaps_directory / "child_sitemaps.txt"
    # Сохраняем ссылки на дочерние sitemaps
    with open(child_sitemaps, "w", encoding="utf-8") as f:
        for url in sitemap_urls:
            f.write(f"{url}\n")

    # Скачиваем все дочерние sitemaps и парсим URL страниц
    all_page_urls = []

    for i, sitemap_url in enumerate(sitemap_urls):
        # Извлекаем имя файла из URL
        filename = os.path.basename(urlparse(sitemap_url).path)
        save_path = sitemaps_directory / filename
        output_file = urls_directory / f"urls_from_{filename}.txt"

        # Проверяем, существует ли уже файл с URL-ами
        if output_file.exists():
            logger.info(
                f"Файл с URL-ами уже существует, пропускаем обработку: {output_file}"
            )

            # Добавляем существующие URL в общий список
            with open(output_file, "r", encoding="utf-8") as f:
                existing_urls = [line.strip() for line in f if line.strip()]
                all_page_urls.extend(existing_urls)
                logger.info(
                    f"  - Загружено {len(existing_urls)} URL страниц из существующего файла"
                )

            continue

        logger.info(
            f"Обработка дочернего sitemap [{i+1}/{len(sitemap_urls)}]: {sitemap_url}"
        )

        # Скачиваем sitemap только если его еще нет (force_download=False)
        sitemap_content = download_xml(sitemap_url, save_path, force_download=False)

        if sitemap_content:
            # Парсим дочерний sitemap и получаем URL страниц
            page_urls = parse_sitemap(sitemap_content)
            logger.info(f"  - Найдено {len(page_urls)} URL страниц")

            # Сохраняем URL страниц в отдельный файл
            with open(output_file, "w", encoding="utf-8") as f:
                for url in page_urls:
                    f.write(f"{url}\n")

            all_page_urls.extend(page_urls)

    all_url = urls_directory / "all_urls.txt"

    # Проверяем, изменилось ли количество URL
    should_update_all_urls = True
    if all_url.exists():
        with open(all_url, "r", encoding="utf-8") as f:
            existing_count = sum(1 for _ in f)

        if existing_count == len(all_page_urls):
            logger.info(
                f"Общий файл с URL не изменился ({existing_count} URLs), пропускаем обновление"
            )
            should_update_all_urls = False

    # Сохраняем все найденные URL страниц в общий файл если нужно
    if should_update_all_urls:
        with open(all_url, "w", encoding="utf-8") as f:
            for url in all_page_urls:
                f.write(f"{url}\n")
        logger.info(f"Обновлен общий файл с URL: {all_url}")

    logger.info(f"\nВсего найдено {len(all_page_urls)} URL страниц")
    logger.info("Результаты сохранены в директориях 'sitemaps' и 'urls'")
    split_urls_by_type()


if __name__ == "__main__":
    main()
