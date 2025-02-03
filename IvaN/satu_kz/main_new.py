import json
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_directory = current_directory / "html"
configuration_directory = current_directory / "configuration"

# Создание директорий, если их нет
html_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

# # Пути к файлам
# output_csv_file = data_directory / "output.csv"

# all_ids = data_directory / "all_ids_new.csv"
# all_urls_file = data_directory / "all_urls.csv"
# product_catalog_csv = data_directory / "product_catalog.csv"
# xlsx_result = data_directory / "result.xlsx"
# json_result = data_directory / "result.json"
# file_proxy = configuration_directory / "proxy.txt"
# config_txt_file = configuration_directory / "config.txt"


def get_html():
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 'cid=193259547835127935702545968913233032346; csrf_token_company_site=fb8f51c4a6c34ec8899f290bea9c9478; evoauth=w64e00d4624aa44bdba224dd1d1efd159',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://oil-market.kz/product_list/page_46?product_items_per_page=48",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://oil-market.kz/product_list",
        headers=headers,
        timeout=30,
    )
    html_file = html_directory / "product_list.html"
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком

        with open(html_file, "w", encoding="utf-8") as file:
            file.write(response.text)
    logger.info(response.status_code)


def pars_htmls():
    extracted_data = []

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        # Найти все теги <script> с JSON-данными
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        logger.info
    #     # Сбор данных в список
    #     extracted_data.append(
    #         {
    #             "product_title_text": product_title_text,
    #             "price_text": price_text,
    #             "stock_text": stock_text,
    #             "description_text": description_text,
    #             "sku_text": sku_text,
    #             "category_texts": category_texts,
    #             "images_string": images_string,
    #         }
    #     )

    # # Создание DataFrame и запись в Excel
    # df = pd.DataFrame(extracted_data)
    # df.to_excel("feepyf.xlsx", index=False)

    # print(f"Данные успешно сохранены в файл: {output_file}")


if __name__ == "__main__":
    # get_html()
    pars_htmls()
