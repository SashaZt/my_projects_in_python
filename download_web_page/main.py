import csv
import json
import random
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)







def get_html():
    timeout = 60
    max_attempts = 10
    delay_seconds = 5

    for page in range(1, 194):
        output_html_file = data_directory / f"auburnmaine_0{page}.csv"

        for attempt in range(max_attempts):
            try:
                if page == 1:
                    data = {
                        "SearchParcel": "%",
                        "SearchBuildingType": "",
                        "SearchLotSize": "",
                        "SearchLotSizeThru": "",
                        "SearchTotalValue": "",
                        "SearchTotalValueThru": "",
                        "SearchOwner": "",
                        "SearchYearBuilt": "",
                        "SearchYearBuiltThru": "",
                        "SearchFinSize": "",
                        "SearchFinSizeThru": "",
                        "SearchSalePrice": "",
                        "SearchSalePriceThru": "",
                        "SearchStreetName": "",
                        "SearchBedrooms": "",
                        "SearchBedroomsThru": "",
                        "SearchNeighborhood": "",
                        "SearchNBHDescription": "",
                        "SearchSaleDate": "",
                        "SearchSaleDateThru": "",
                        "SearchStreetNumber": "",
                        "SearchBathrooms": "",
                        "SearchBathroomsThru": "",
                        "SearchLUC": "",
                        "SearchLUCDescription": "",
                        "SearchBook": "",
                        "SearchPage": "",
                        "SearchSubmitted": "yes",
                        "cmdGo": "Go",
                    }

                    response = requests.post(
                        "https://auburnmaine.patriotproperties.com/SearchResults.asp",
                        cookies=cookies,
                        headers=headers,
                        data=data,
                        timeout=timeout,
                    )
                else:
                    params = {
                        "page": page,
                    }
                    response = requests.get(
                        "https://auburnmaine.patriotproperties.com/SearchResults.asp",
                        params=params,
                        cookies=cookies,
                        headers=headers,
                        timeout=timeout,
                    )

                # Проверка кода ответа
                if response.status_code == 200:
                    # Сохранение HTML-страницы целиком
                    with open(output_html_file, "w", encoding="utf-8") as file:
                        file.write(response.text)
                    logger.info(f"Successfully saved {output_html_file}")
                    break  # Выходим из цикла попыток при успехе
                else:
                    logger.warning(
                        f"Attempt {attempt + 1} failed for page {page} with status {response.status_code}"
                    )
                    if attempt < max_attempts - 1:  # Если не последняя попытка
                        time.sleep(delay_seconds)
                    continue

            except requests.RequestException as e:
                logger.error(
                    f"Error on attempt {attempt + 1} for page {page}: {str(e)}"
                )
                if attempt < max_attempts - 1:  # Если не последняя попытка
                    time.sleep(delay_seconds)
                continue

        else:  # Выполняется, если цикл попыток завершился без break
            logger.error(f"Failed to get page {page} after {max_attempts} attempts")


def scrap_html():
    with open("freepik.html", "r", encoding="utf-8") as file:
        content = file.read()
    soup = BeautifulSoup(content, "lxml")
    # Находим все элементы <figure> с классом "$relative"
    figures = soup.find_all("figure", class_="$relative")

    # Список для хранения результатов
    results = []

    # Проходим по всем найденным <figure>
    for figure in figures:
        # Ищем <img> внутри каждого <figure>
        img = figure.find("img")
        if img:
            # Извлекаем атрибуты alt и src
            alt_text = img.get("alt", "")  # Если alt отсутствует, вернем пустую строку
            src_url = img.get("src", "")  # Если src отсутствует, вернем пустую строку
            results.append({"alt": alt_text, "src": src_url})

    # Выводим результаты
    for result in results:
        print(f"Alt: {result['alt']}")
        print(f"Src: {result['src']}")
        print("---")

    # Если нужно сохранить в список словарей или файл, вот пример:
    import json

    with open("image_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    scrap_html()
    # main_realoem()
    # get_htmls()
    get_html()
