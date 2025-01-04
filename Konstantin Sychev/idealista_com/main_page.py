import json
import os
import re
import shutil
from math import log
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger
from dotenv import dotenv_values, load_dotenv
from tqdm import tqdm

current_directory = Path.cwd()
html_page_directory = current_directory / "html_page"
html_page_directory.mkdir(parents=True, exist_ok=True)


# Загружаем переменные окружения из файла .env
def load_environment():
    env_path = os.path.join(os.getcwd(), "configuration", ".env")
    load_dotenv(env_path)


# Генерация всех возможных URL
def generate_all_urls():
    base_url = os.getenv("base_url", "").strip()
    extra = os.getenv("extra", "").strip()
    provinces = os.getenv("Provincia", "").split(",")

    # Проверяем наличие базовых параметров
    if not base_url or not provinces:
        raise ValueError("Параметры 'base_url' или 'Provincia' отсутствуют или пусты.")

    # Загружаем переменные из файла .env
    env_path = os.path.join(os.getcwd(), "configuration", ".env")
    env_vars = dotenv_values(env_path)

    # Получаем все ключи для категорий "Buy" и "Rent"
    categories = [
        key
        for key in env_vars.keys()
        if key.startswith("Buy_") or key.startswith("Rent_")
    ]

    # Генерируем все комбинации URL
    urls = []
    for category in categories:
        action = os.getenv(category, "").strip()
        for province in provinces:
            url = f"{base_url}{action}/{province}/{extra}"
            urls.append({"url": url})  # Добавляем только URL

    return pd.DataFrame(urls)  # Возвращаем DataFrame с одним столбцом


# Запись URL в CSV файл
def write_urls_to_csv(df, filename="urls.csv"):
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"URLs успешно записаны в '{filename}'. Всего URL: {len(df)}")


def parsing_html_page():

    extracted_data = []
    # Пройтись по каждому HTML файлу в папке
    for html_file in html_page_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            # Прочитать содержимое файла
            content = file.read()
        soup = BeautifulSoup(content, "lxml")
        # Извлечение данных
        urls_raw = soup.find("nav", class_="locations-list").find_all(
            "a", {"class": "subregion"}
        )
        urls = [f'https://www.idealista.com{url.get("href")}' for url in urls_raw]
        for i in urls:
            print(i)


if __name__ == "__main__":
    load_environment()
    # parsing_html_page()
    # Получаем переменные окружения
    # provinces, buy, rent, share, base_url, extra = get_env()

    # Базовый URL

    # # Генерация URL для покупки
    # buy_urls = generate_urls(base_url, buy, provinces, extra)
    # print("Buy URLs:")
    # print("\n".join(buy_urls))

    # # Генерация URL для аренды
    # rent_urls = generate_urls(base_url, rent, provinces, extra)
    # print("\nRent URLs:")
    # print("\n".join(rent_urls))

    # Генерация URL для совместного проживания
    # share_urls = generate_urls(base_url, share, provinces, extra)
    # print("\nShare URLs:")
    # print("\n".join(share_urls))

    # Генерация URL
    df_urls = generate_all_urls()

    # Запись URL в файл
    if not df_urls.empty:
        write_urls_to_csv(df_urls)
    else:
        print("URL не были сгенерированы. Проверьте содержимое .env.")
