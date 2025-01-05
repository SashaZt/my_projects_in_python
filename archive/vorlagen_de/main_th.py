# МНОГОПОТОЧНОСТЬ И ОЧЕРЕДЬ
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests
from configuration.logger_setup import logger

# Путь к папкам
current_directory = Path.cwd()
json_tenders_diretory = current_directory / "json_tenders"
json_page_diretory = current_directory / "json_page"
data_diretory = current_directory / "data"
html_directory = current_directory / "html"
configuration_directory = current_directory / "configuration"

json_page_diretory.mkdir(exist_ok=True, parents=True)
html_directory.mkdir(exist_ok=True, parents=True)
json_tenders_diretory.mkdir(exist_ok=True, parents=True)
data_diretory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
file_proxy = configuration_directory / "roman.txt"
output_csv_file = data_diretory / "output.csv"


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["url"].tolist()


# Основная функция для работы с ID
def get_json_detail(url):
    cookies = {
        "PHPSESSID": "rc24jkodfmn9eh93aa8pdauaca",
        "SERVERID": "s1",
        "OptanonAlertBoxClosed": "2024-12-02T06:56:42.204Z",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Wed+Dec+04+2024+22%3A41%3A58+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.32.0&isIABGlobal=false&consentId=a958fe43-04b3-41e4-9a14-ffbbe3f2baa2&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0004%3A1%2CC0005%3A1&hosts=H446%3A1%2CH724%3A1%2CH568%3A1%2CH9%3A1%2CH648%3A1%2CH571%3A1%2CH49%3A1%2CH65%3A1%2CH626%3A1%2CH13%3A1%2CH14%3A1%2CH15%3A1%2CH717%3A1%2CH45%3A1%2CH2%3A1%2CH695%3A1%2CH584%3A1%2CH494%3A1%2CH46%3A1%2CH589%3A1%2CH497%3A1%2CH498%3A1%2CH627%3A1%2CH35%3A1%2CH725%3A1%2CH20%3A1%2CH646%3A1%2CH445%3A1%2CH539%3A1%2CH540%3A1%2CH729%3A1%2CH39%3A1%2CH541%3A1%2CH506%3A1%2CH17%3A1&genVendors=&geolocation=UA%3B18&AwaitingReconsent=false",
    }

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    name = "_".join(url.rsplit("/", 2)[-2:]).replace("-", "_")
    file_name = html_directory / f"{name}.html"
    if file_name.exists():
        return

    try:
        response = requests.get(
            url,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )
        if response.status_code == 200:
            # Сохранение HTML-страницы целиком
            with open(file_name, "w", encoding="utf-8") as file:
                file.write(response.text)
            logger.info(f"Сохранён файл: {file_name}")
        else:
            logger.warning(f"Ошибка ответа: {response.status_code} для ID {pr_id}")
    except requests.exceptions.ReadTimeout:
        logger.error(f"Тайм-аут при обработке ID {pr_id}")
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL ошибка для ID {pr_id}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса для ID {pr_id}: {e}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка для ID {pr_id}: {e}")


# Основной запуск с очередями и ThreadPoolExecutor
if __name__ == "__main__":
    all_ids = read_cities_from_csv(output_csv_file)
    max_workers = 5  # Количество одновременно работающих потоков

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(get_json_detail, pr_id): pr_id for pr_id in all_ids
        }

        for future in as_completed(future_to_id):
            pr_id = future_to_id[future]
            try:
                future.result()  # Проверяем исключения в выполнении задач
            except Exception as e:
                logger.error(f"Ошибка при обработке ID {pr_id}: {e}")

    logger.info("Все задачи завершены.")
