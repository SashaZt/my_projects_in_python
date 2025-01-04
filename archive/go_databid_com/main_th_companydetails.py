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
json_companydetails_diretory = current_directory / "json_companydetails"
json_page_diretory = current_directory / "json_page"
data_diretory = current_directory / "data"
configuration_directory = current_directory / "configuration"

json_page_diretory.mkdir(exist_ok=True, parents=True)
json_companydetails_diretory.mkdir(exist_ok=True, parents=True)
json_tenders_diretory.mkdir(exist_ok=True, parents=True)
data_diretory.mkdir(exist_ok=True, parents=True)
configuration_directory.mkdir(parents=True, exist_ok=True)
file_proxy = configuration_directory / "roman.txt"
output_csv_file = data_diretory / "output.csv"


# Функция для чтения городов из CSV файла
def read_cities_from_csv(input_csv_file):
    df = pd.read_csv(input_csv_file)
    return df["id"].tolist()


# Основная функция для работы с ID
def get_json_detail(pr_id):
    cookies = {
        "messagesUtk": "a24cb7b40f42455191b94f513aa4b2c6",
        "ASP.NET_SessionId": "bal1jnkkkrw3c4oae45yxxs3",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Pragma": "no-cache",
        "Referer": "https://go.databid.com/NewDashboard/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    file_name = json_companydetails_diretory / f"{pr_id}_CompanyDetails.json"
    if file_name.exists():
        logger.info(f"Файл для ID {pr_id} уже существует, пропускаем.")
        return

    try:
        response = requests.get(
            "https://go.databid.com/newdashboard/api/api/CompanyDetails/GetCompanyDetails",
            params={"UserId": "106640", "CompanyID": pr_id},
            cookies=cookies,
            headers=headers,
            timeout=30,
        )
        if response.status_code == 200:
            json_data = response.json()
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
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
