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
from queue import Queue


# Лок для синхронизации
lock = threading.Lock()

# Очереди задач
url_queue = Queue()
data_queue = []
cookies = {
    "PHPSESSID": "cukemnicu4770qne45tpcu04k3",
    "temp_uid": "f7d044e3d3e4d85f7b2129d0f5621962",
    "uui_req": "99117107101",
    "lang": "fr",
    "UI": "_",
    "FavStatus": "open_0",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    # 'Cookie': 'PHPSESSID=cukemnicu4770qne45tpcu04k3; temp_uid=f7d044e3d3e4d85f7b2129d0f5621962; uui_req=99117107101; lang=fr; UI=_; FavStatus=open_0',
    "DNT": "1",
    "Pragma": "no-cache",
    "Referer": "https://www.bizcaf.ro/foisor-patrat-cu-masa-si-banci-tip-picnic-rexal-ro_bizcafAd_2321294.dhtml",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "1000 ip.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_total_pages(proxies):
    """Определяет общее количество страниц с объявлениями на сайте."""
    url = "https://www.bizcaf.ro/"
    proxy = random.choice(proxies)
    proxies_dict = {"http": proxy, "https": proxy}
    try:
        if response.status_code == 200:
            response = requests.get(
                url, headers=headers, cookies=cookies, proxies=proxies_dict, timeout=10
            )
        else:
            logger.error(response.status_code)
        response.raise_for_status()
        tree = HTMLParser(response.text)

        # Извлечение количества объявлений
        total_ads_text = tree.css_first(
            "#main_content1 > div > div.links > table > tbody > tr:nth-child(1) > td > table > tbody > tr > td:nth-child(1)"
        ).text()
        total_ads = int(
            total_ads_text.split("din")[1].split("anunturi")[0].strip().replace(".", "")
        )

        # Вычисление количества страниц
        ads_per_page = 24
        total_pages = (total_ads // ads_per_page) + (
            1 if total_ads % ads_per_page > 0 else 0
        )
        logger.info(f"Найдено {total_ads} объявлений на {total_pages} страницах.")
        return total_pages

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении количества страниц: {e}")
        return 0


def fetch_urls(page_num, proxies):
    """Извлекает URL объявлений с указанной страницы."""
    proxy = random.choice(proxies)
    proxies_dict = {"http": proxy, "https": proxy}
    url = f"https://www.bizcaf.ro/anunturi/?pg={page_num}"
    try:
        response = requests.get(
            url, headers=headers, cookies=cookies, proxies=proxies_dict, timeout=10
        )
        response.raise_for_status()
        tree = HTMLParser(response.text)

        # Извлечение URL объявлений
        ad_elements = tree.xpath('//a[@itemprop="url"]')
        urls = [el.attributes["href"] for el in ad_elements]
        with lock:
            data_queue.extend(urls)

        logger.info(f"Собрано {len(urls)} URL с {page_num}-й страницы.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при извлечении URL на странице {page_num}: {e}")


def url_thread_worker(proxies):
    """Потоковая функция для извлечения URL с страниц."""
    while not url_queue.empty():
        page_num = url_queue.get()
        try:
            fetch_urls(page_num, proxies)
        finally:
            url_queue.task_done()


def main():
    """Основная функция для запуска процесса многопоточного сбора URL объявлений."""
    proxies = load_proxies()  # Загружаем список всех прокси
    total_pages = get_total_pages(proxies)  # Получаем общее количество страниц
    if total_pages == 0:
        logger.error("Не удалось определить количество страниц. Завершение работы.")
        return

    # Заполняем очередь номерами страниц
    for page_num in range(1, total_pages + 1):
        url_queue.put(page_num)

    num_threads = 10  # Количество потоков для многопоточности
    threads = []

    logger.info(f"Запуск {num_threads} потоков для сбора URL.")

    # Создаем и запускаем потоки для получения URL
    for _ in range(num_threads):
        thread = threading.Thread(target=url_thread_worker, args=(proxies,))
        thread.start()
        threads.append(thread)

    # Ожидаем завершения всех потоков
    url_queue.join()

    for thread in threads:
        thread.join()

    logger.info(f"Собрано всего {len(data_queue)} URL объявлений.")
    # Вы можете сохранить собранные URL или передать их дальше для обработки


if __name__ == "__main__":
    main()
