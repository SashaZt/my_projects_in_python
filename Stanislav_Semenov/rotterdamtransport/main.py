import json
import random
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from configuration.logger_setup import logger

current_directory = Path.cwd()
data_directory = current_directory / "data"
html_files_directory = current_directory / "html_files"
html_page_directory = current_directory / "html_page"
configuration_directory = current_directory / "configuration"

data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(parents=True, exist_ok=True)
html_page_directory.mkdir(parents=True, exist_ok=True)


output_csv_file = data_directory / "output.csv"
file_proxy = configuration_directory / "roman.txt"


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


def load_proxies():
    """Загружает список прокси-серверов из файла."""
    file_path = "roman.txt"
    with open(file_path, "r", encoding="utf-8") as file:
        proxies = [line.strip() for line in file]
    logger.info(f"Загружено {len(proxies)} прокси.")
    return proxies


def get_html():
    urls = read_cities_from_csv(output_csv_file)
    cookies = {
        "ecn_permission": '{"analytics":true,"marketing":true}',
        "cf_clearance": "hSkqpi2rBvS0PgDCkgWdGRScBWht3uLyb1H2zG19yPU-1734375382-1.2.1.1-OZAGoizEwW71D3PRPxYANv_DqgqohpZgfpbJIYbdDBe44_t6iPEWzyxTgy939oK.jiF8n99i_wtIuEoL4p7xINrRTQRq9lZkkeuX0FF.EzYHzQEAqGnTGkpPZdBEoy4NLhl90Y7MpjHV32TLkTwytKFx440s7Xe86ojHAFESCMdw4qgx54.x19gc26B4FjC0ch5Vpyre1WPbvHxllJggUA0PXTEpbufbQ2Zq49t48kRrwl8uLkAnUVVMyBkwf_N3aDjVlrlvZm17VnTNSCIEnj4mp6uBRt9LDVid9nPC_7WzMpgDZmvDO77m.25LJoMxM4EOHs7Ot9pe_EEG0v3sCHf6GCBiDMHids6S0a34hEMNvFKxj6G4AjSSsk9NMivt7HU7ZFraQZ0AlLJCU3xr4w",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 'ecn_permission={"analytics":true,"marketing":true}; cf_clearance=hSkqpi2rBvS0PgDCkgWdGRScBWht3uLyb1H2zG19yPU-1734375382-1.2.1.1-OZAGoizEwW71D3PRPxYANv_DqgqohpZgfpbJIYbdDBe44_t6iPEWzyxTgy939oK.jiF8n99i_wtIuEoL4p7xINrRTQRq9lZkkeuX0FF.EzYHzQEAqGnTGkpPZdBEoy4NLhl90Y7MpjHV32TLkTwytKFx440s7Xe86ojHAFESCMdw4qgx54.x19gc26B4FjC0ch5Vpyre1WPbvHxllJggUA0PXTEpbufbQ2Zq49t48kRrwl8uLkAnUVVMyBkwf_N3aDjVlrlvZm17VnTNSCIEnj4mp6uBRt9LDVid9nPC_7WzMpgDZmvDO77m.25LJoMxM4EOHs7Ot9pe_EEG0v3sCHf6GCBiDMHids6S0a34hEMNvFKxj6G4AjSSsk9NMivt7HU7ZFraQZ0AlLJCU3xr4w',
        "dnt": "1",
        "pragma": "no-cache",
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
    # proxies = load_proxies()
    for url in urls:
        # proxy = random.choice(proxies)
        # proxies_dict = {"http": proxy, "https": proxy}
        name_file_2 = url.split("/")[-2].replace("-", "_")
        name_file_3 = url.split("/")[-3].replace("-", "_")
        name_file = f"{name_file_3}_{name_file_2}"
        html_company = html_files_directory / f"{name_file}.html"
        if html_company.exists():
            continue
        # , proxies=proxies_dict,
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        if response.status_code == 200:
            src = response.text
            with open(html_company, "w", encoding="utf-8") as file:
                file.write(src)
        else:
            logger.error(response.status_code)


def format_phone_fax(number):
    if number and not number.startswith("+49"):
        return f"+49{number}"
    return number


def scraping_page():
    result = []
    for html_file in html_page_directory.glob("*.html"):
        try:
            # Открываем файл и читаем содержимое
            with open(html_file, "r", encoding="utf-8") as file:
                content = file.read()

            # Парсим содержимое с BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            companys = soup.find_all(
                "div",
                attrs={"class": "dynamic-cell__name"},
            )
            for company in companys:
                url = company.find("a").get("href")
                result.append(url)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")
    # Создаем DataFrame и записываем в CSV
    urls_df = pd.DataFrame(result, columns=["url"])
    urls_df.to_csv(output_csv_file, index=False)


def scraping_company():
    # Проходим по всем HTML-файлам в директории
    result = []
    for html_file in html_files_directory.glob("*.html"):
        try:
            # Открываем файл и читаем содержимое
            with open(html_file, "r", encoding="utf-8") as file:
                content = file.read()

            # Парсим содержимое с BeautifulSoup
            soup = BeautifulSoup(content, "lxml")
            # Извлечение JSON-структуры из <div id="allMeta">
            # all_meta = soup.find("div", id="allMeta")
            # if all_meta:
            #     # Преобразование содержимого в JSON
            #     data = json.loads(all_meta.text)
            # else:
            #     logger.error("Тег с id='allMeta' не найден.")
            name = None
            phone = None
            name_raw = soup.find(
                "h1",
                attrs={"class": "company-title__item company-title__item--name"},
            )
            if name_raw:
                name = name_raw.text.strip()

            phone_raw = soup.find(
                "span",
                attrs={"class": "company-title__meta"},
            )
            if phone_raw:
                phone = phone_raw.find("a").text.strip()
            all_data = {
                "name": name,
                "phone": phone,
            }
            result.append(all_data)
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")
    # Запись в Excel
    if result:
        df = pd.DataFrame(result)
        output_file = current_directory / "scraped_data.xlsx"
        df.to_excel(output_file, index=False)
        logger.info(f"Данные успешно сохранены в файл {output_file}")
    else:
        logger.warning("Нет данных для сохранения.")


if __name__ == "__main__":
    # scraping_page()
    # get_html()
    scraping_company()
