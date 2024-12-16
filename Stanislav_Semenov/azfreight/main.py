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
configuration_directory = current_directory / "configuration"
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
html_files_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
input_csv_file = data_directory / "city.csv"
csv_file_successful = data_directory / "identifier_successful.csv"
output_json_file = data_directory / "output.json"
file_proxy = configuration_directory / "roman.txt"
# Путь к файлу HTML
file_path = "01.html"
output_csv = "urls_output.csv"

# # Открываем и парсим HTML
# with open(file_path, "r", encoding="utf-8") as file:
#     soup = BeautifulSoup(file, "html.parser")

# # Пример поиска названий компаний и телефонов
# # Нужно определить, какие именно теги содержат данные
# all_company = soup.find_all("div", attrs={"class": "single-company"})
# urls = []
# for company in all_company:
#     href = company.find("a").get("href")
#     urls.append(href)

# # Логирование количества URL
# logger.info(len(urls))

# # Создаем DataFrame и записываем в CSV
# urls_df = pd.DataFrame(urls, columns=["url"])
# urls_df.to_csv(output_csv, index=False)


# print(f"Результаты сохранены в файл {output_csv}")


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
    urls = read_cities_from_csv(output_csv)
    cookies = {
        "sbjs_migrations": "1418474375998%3D1",
        "sbjs_first_add": "fd%3D2024-12-11%2008%3A07%3A29%7C%7C%7Cep%3Dhttps%3A%2F%2Fazfreight.com%2Fcountry-facility%2Ffreight-forwarders-in-netherlands%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Ffreelancehunt.com%2F",
        "sbjs_current_add": "fd%3D2024-12-11%2008%3A07%3A29%7C%7C%7Cep%3Dhttps%3A%2F%2Fazfreight.com%2Fcountry%2Fgermany%2F%7C%7C%7Crf%3Dhttps%3A%2F%2Ffreelancehunt.com%2F",
        "sbjs_current": "typ%3Dreferral%7C%7C%7Csrc%3Dfreelancehunt.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29",
        "sbjs_first": "typ%3Dreferral%7C%7C%7Csrc%3Dfreelancehunt.com%7C%7C%7Cmdm%3Dreferral%7C%7C%7Ccmp%3D%28none%29%7C%7C%7Ccnt%3D%2F%7C%7C%7Ctrm%3D%28none%29%7C%7C%7Cid%3D%28none%29",
        "woocommerce_multicurrency_forced_currency": "GBP",
        "woocommerce_multicurrency_language": "en",
        "sbjs_udata": "vst%3D2%7C%7C%7Cuip%3D%28none%29%7C%7C%7Cuag%3DMozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%29%20AppleWebKit%2F537.36%20%28KHTML%2C%20like%20Gecko%29%20Chrome%2F131.0.0.0%20Safari%2F537.36",
        "cmplz_consented_services": "",
        "cmplz_policy_id": "31",
        "cmplz_marketing": "allow",
        "cmplz_statistics": "allow",
        "cmplz_preferences": "allow",
        "cmplz_functional": "allow",
        "cmplz_banner-status": "dismissed",
        "mailchimp_landing_site": "https%3A%2F%2Fazfreight.com%2Fwp-content%2Fplugins%2Fazfreight%2Fdirectory.php%3Fdone_id%3D19119%26shown_once%3D0%26limit_updates%3D15%26action%3Dcurrent_updates",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "referer": "https://azfreight.com/country/germany/",
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
    proxies = load_proxies()
    for url in urls:
        proxy = random.choice(proxies)
        proxies_dict = {"http": proxy, "https": proxy}
        name_file_2 = url.split("/")[-2].replace("-", "_")
        name_file_3 = url.split("/")[-3].replace("-", "_")
        name_file = f"{name_file_3}_{name_file_2}"
        html_company = html_files_directory / f"{name_file}.html"
        if html_company.exists():
            continue
        response = requests.get(
            url, proxies=proxies_dict, cookies=cookies, headers=headers, timeout=30
        )
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


def scraping():
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
            all_meta = soup.find("div", id="allMeta")
            if all_meta:
                # Преобразование содержимого в JSON
                data = json.loads(all_meta.text)
                # logger.info(json.dumps(data, indent=4))  # Форматированный вывод
            else:
                logger.error("Тег с id='allMeta' не найден.")
            name = None
            phone = None
            phone_02 = None
            phone_03 = None
            fax = None
            name_raw = soup.find(
                "h1",
                attrs={"class": "entry-title"},
            )
            if name_raw:
                name = name_raw.text.strip()
            # phone_raw = soup.find(
            #     "span",
            #     attrs={"data-field": "wpcf-telephone"},
            # )
            # if phone_raw:
            #     phone = (
            #         phone_raw.text.strip()
            #         .replace(" ", "")
            #         .replace("(", "")
            #         .replace(")", "")
            #     )
            #     phone = format_phone_fax(phone)
            # phone_raw_02 = soup.find(
            #     "span",
            #     attrs={"data-field": "wpcf-co-tel-main"},
            # )
            # if phone_raw_02:
            #     phone_02 = (
            #         phone_raw_02.text.strip()
            #         .replace(" ", "")
            #         .replace("(", "")
            #         .replace(")", "")
            #     )
            #     phone_02 = format_phone_fax(phone)
            # phone_raw_03 = soup.find(
            #     "span",
            #     attrs={"data-field": "wpcf-telno"},
            # )
            # if phone_raw_03:
            #     phone_03 = (
            #         phone_raw_03.text.strip()
                    # .replace(" ", "")
                    # .replace("(", "")
                    # .replace(")", "")
            #     )
            #     phone_03 = format_phone_fax(phone)

            # fax_raw = soup.find(
            #     "span",
            #     attrs={"data-field": "wpcf-company-fax"},
            # )
            # if fax_raw:
            #     fax = (
            #         fax_raw.text.strip()
            #         .replace(" ", "")
            #         .replace("(", "")
            #         .replace(")", "")
            #     )
            #     fax = format_phone_fax(fax)
            all_data = {
                "name": name,
                "data": data,
                # "phone_02": phone_02,
                # "phone_03": phone_03,
                # "fax": fax,
            }
            # Разворачиваем вложенные данные
            flattened_data = {"name": all_data["name"]}
            flattened_data.update(
                {
                    key: value[0] if isinstance(value, list) else value
                    for key, value in all_data["data"].items()
                }
            )
            result.append(flattened_data)
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
    # get_html()
    scraping()
