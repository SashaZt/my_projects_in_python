import csv
import hashlib
import html
import json
import os
import re
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

current_directory = Path.cwd()
config_directory = current_directory / "config"
data_directory = current_directory / "data"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
output_xml_file = data_directory / "output.xml"
output_csv_file = data_directory / "output.csv"
output_json_file = data_directory / "output.json"
config_file = config_directory / "config.json"
service_account_file = config_directory / "credentials.json"

cookies = {
    "sid": "8b38b72f9859d012d7a3c31725a200d7",
    "thomann_settings": "1b949fd4-46c6-44e8-842a-538fdac94f1f",
    "uslk_umm_27718_s": "ewAiAHYAZQByAHMAaQBvAG4AIgA6ACIAMQAiACwAIgBkAGEAdABhACIAOgB7AH0AfQA=",
    "__cf_bm": "szK1gdsrSId8_3cFefMErvPbQSAUMG2d8oJRzHeKpxs-1743707252-1.0.1.1-oVPzr8eK6S3IJQtUIwHwOOF8xeiNYq9ffesRpbWbilQ0vaVXE158wx8vgkBg3zIgwCYT.vbis9ljXAfrq18A8Byqd_T_FmmOq0MX6pc8nDo",
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
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
}


def main_th():
    if not os.path.exists(html_directory):
        html_directory.mkdir(parents=True, exist_ok=True)
    urls = []
    with open(output_csv_file, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            urls.append(row["url"])

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = []
        for url in urls:
            output_html_file = (
                html_directory / f"{hashlib.md5(url.encode()).hexdigest()}.html"
            )

            if not os.path.exists(output_html_file):
                futures.append(executor.submit(get_html, url, output_html_file))
                time.sleep(5)
            else:
                logger.info(f"Файл для {url} уже существует, пропускаем.")

        results = []
        for future in as_completed(futures):
            # Здесь вы можете обрабатывать результаты по мере их завершения
            results.append(future.result())


def fetch(url):
    try:
        response = requests.get(
            url, cookies=cookies, headers=headers, timeout=30, stream=True
        )

        # Проверка статуса ответа
        if response.status_code != 200:
            logger.warning(
                f"Статус не 200 для {url}. Получен статус: {response.status_code}. Пропускаем."
            )
            return None
        # Принудительно устанавливаем кодировку UTF-8
        response.encoding = "utf-8"
        return response.text

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при загрузке {url}: {str(e)}")
        return None


def get_html(url, html_file):
    src = fetch(url)

    if src is None:
        return url, html_file, False

    with open(html_file, "w", encoding="utf-8") as file:
        file.write(src)

    logger.info(f"Успешно загружен и сохранен: {html_file}")
    return url, html_file, True


def pars_htmls():
    logger.info("Собираем данные со страниц html")
    all_data = []

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")

        # Создаём словарь для текущего файла
        result = {}

        # 1. Извлекаем артикул (Numer artykułu)
        labels = soup.find_all("span", class_="keyfeature__label")
        for label in labels:

            if label.text.strip() == "Numer artykułu":
                # Ищем следующий span с классом fx-text--bold
                article_number = label.find_next("span", class_="fx-text--bold")
                if article_number:
                    result["article_number"] = article_number.text.strip()
                    break  # Прерываем цикл, если нашли нужный артикул

        # 2. Извлекаем заголовок (title)
        product_title = soup.find("div", class_="fx-content-product__main")
        if product_title:
            h1 = product_title.find("h1", itemprop="name")
            if h1:
                result["title"] = h1.text.strip()

        # 3. Извлекаем цену
        price_wrapper = soup.find("div", class_="price-wrapper")
        if price_wrapper:
            price_div = price_wrapper.find("div", class_="price")
            if price_div:
                price = price_div.text.strip().replace(
                    " zł", ""
                )  # Убираем символ валюты
                result["price"] = price

        # 4. Извлекаем статус доступности
        availability = soup.find("span", class_="fx-availability--in-stock")
        if availability:
            result["availability"] = availability.text.strip()

        # Добавляем результат в общий список, если словарь не пустой
        if result:
            all_data.append(result)

    logger.info(f"Собрано {len(all_data)} записей")
    # logger.info(all_data)
    with open(output_json_file, "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)

    # Создание DataFrame и запись в Excel
    df = pd.DataFrame(all_data)
    df.to_excel("thomann.xlsx", index=False)


if __name__ == "__main__":
    # main_th()
    pars_htmls()
