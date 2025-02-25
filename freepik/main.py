import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests
from loguru import logger
from PIL import Image
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

current_directory = Path.cwd()
json_original_directory = current_directory / "json_original"
json_product_directory = current_directory / "json_product"
log_directory = current_directory / "log"
img_directory = current_directory / "img"

img_directory.mkdir(parents=True, exist_ok=True)
json_original_directory.mkdir(parents=True, exist_ok=True)
json_product_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"

BASE_URL = "https://www.freepik.com"
FILE_NAME_JSON = "logos"



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
        "_gcl_au": "1.1.1807574848.1740066140",
        "_ga": "GA1.1.1183695763.1740066140",
        "OptanonAlertBoxClosed": "2025-02-20T15:42:20.666Z",
        "ak_bmsc": "1F57AFBE824F7896CE9DC5B69D36B18A~000000000000000000000000000000~YAAQhq0VAqhx4SCVAQAApgSbORp6LsaIN8M8OVU1m+fHrXB4YAi/yx//PU2UZprSnHsbBheSKJPgSRTi5bNLRpTGbSCmkbY4iHtiNUh8KMHjmbhtpe/jt+FMhNmGoIPxMJENtlly3IKXuilbccgwSFDOIxSAS3TqdURwCEp54iN6mCCqUez9syz234PND/Rf0EwaD3LQlAQA17b9vRU31icguV7Ll/7ioqix7vyMq/NdXQQlcRTCE8ipeNExsdpNNMDdQAn3mZET2+g1C9VM+b0dmSeRRf8c8PW50jy+pSaxGssyb7NH3GLMbadAd9x535ZkM6xwmUq0F17XaJH+6nKz3pfOFMCCUrVGefqQkRKU9wUAiUgontzVQY+1xJR6rnn/K5CAvwpe8G8=",
        "OptanonConsent": "isGpcEnabled=0&datestamp=Mon+Feb+24+2025+22%3A16%3A54+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202411.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=bbb48d07-470d-42a4-96c9-2509b56c2bbf&interactionCount=2&isAnonUser=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CC0005%3A1&intType=1&geolocation=UA%3B18&AwaitingReconsent=false",
        "_ga_QWX66025LC": "GS1.1.1740427268.10.1.1740428229.45.0.0",
    }

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=1, i",
    "referer": "https://www.freepik.com/templates/price-lists/2",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "x-nextjs-data": "1",
}

def get_json():
    for page in range(1, 11):
        if page == 1:
            params = {
            'param': FILE_NAME_JSON,
        }
            url = f'https://www.freepik.com/_next/data/dbTWBGYytMf6qZVClARjW/en/templates/{FILE_NAME_JSON}.json'
        else:
            params = {
            'param': [
                FILE_NAME_JSON,
                page,
            ],
            }
            url = f'https://www.freepik.com/_next/data/dbTWBGYytMf6qZVClARjW/en/templates/{FILE_NAME_JSON}/{page}.json'

        output_file = json_original_directory / FILE_NAME_JSON / f"{FILE_NAME_JSON}_{page}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if output_file.exists():
            continue
        response = requests.get(
            url,
            params=params,
            cookies=cookies,
            headers=headers,
            timeout=30,
        )

        
        # Если сервер вернул корректный JSON, то выводим его:
        try:
            data = response.json()
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)  # Записываем в файл
            logger.info(f"Сохранил {output_file}")
        except ValueError:
            logger.error("Ошибка: ответ не содержит JSON")



def process_data():
    all_data = []
    output_directory = json_original_directory / FILE_NAME_JSON
    for json_file in output_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        json_datas = data["pageProps"]["results"]["items"]
        for json_data in json_datas:
            id_product = json_data.get("id", None)
            name = json_data.get("name", None)
            slug = json_data.get("slug", None).replace("-","_")
            url = f'{BASE_URL}{json_data.get("url", None)}'
            premium = json_data.get("pixel", "Free")
            author_name = json_data.get("author", {}).get("name", None)
            preview_url = json_data.get("preview", {}).get("url", None)
            data_product = {
                "id":id_product,
                "name":name,
                "slug":slug,
                "url":url,
                "premium":premium,
                "author_name":author_name,
                "preview_url":preview_url
            }
            all_data.append(data_product)
    # Запись всех данных в один JSON файл
    output_file = json_product_directory / FILE_NAME_JSON / f"{FILE_NAME_JSON}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as outfile:
        json.dump(all_data, outfile, ensure_ascii=False, indent=4)
    # Запись всех данных в Excel файл
    df = pd.DataFrame(all_data)
    output_excel_file = json_product_directory / FILE_NAME_JSON / f"{FILE_NAME_JSON}.xlsx"
    output_excel_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_excel_file, index=False)

# def save_img(url, name):
#     response = requests.get(url,cookies=cookies,
#         headers=headers,
#         timeout=30,)
#     file_name = img_directory / FILE_NAME_JSON / f"{name}.jpg"
#     file_name.parent.mkdir(parents=True, exist_ok=True)
#     if file_name.exists():
#         return
#     if response.status_code == 200:
#         image = Image.open(BytesIO(response.content))
#         # Сохраняем изображение в формате JPEG
#         image.save(file_name, "JPEG")
#         logger.info(f"Изображение сохранено как {file_name}")
#     else:
#         logger.error("Ошибка при загрузке изображения:", response.status_code)


# def get_imgs():
#     output_directory = json_product_directory / FILE_NAME_JSON
#     for json_file in output_directory.glob("*.json"):
#         with open(json_file, "r", encoding="utf-8") as file:
#             datas = json.load(file)
#         for data in datas:
#             url = data["preview_url"]
#             slug = data["slug"]
#             save_img(url, slug)
def save_img(url, name):
    """Функция загружает и сохраняет изображение."""
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        file_name = img_directory / FILE_NAME_JSON / f"{name}.jpg"
        file_name.parent.mkdir(parents=True, exist_ok=True)

        if file_name.exists():
            logger.error(file_name)
            return

        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            image.save(file_name, "JPEG")
            logger.info(f"Изображение сохранено как {file_name}")
        else:
            logger.error(f"Ошибка при загрузке {url}: {response.status_code}")

    except Exception as e:
        logger.error(f"Ошибка при загрузке {url}: {e}")

def get_imgs(num_threads=5):
    """Функция парсит JSON и многопоточно скачивает изображения."""
    output_directory = json_product_directory / FILE_NAME_JSON
    image_tasks = []

    # Собираем все данные для загрузки
    for json_file in output_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            datas = json.load(file)

        for data in datas:
            url = data.get("preview_url")
            slug = data.get("slug")
            id_product = data.get("id")
            file_name = f"{id_product}_{slug}"
            if url and slug:
                image_tasks.append((url, file_name))
            else:
                logger.error(f"Отсутствуют данные в файле {json_file}")

    # Многопоточная загрузка изображений
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_url = {executor.submit(save_img, url, slug): url for url, slug in image_tasks}

        for future in as_completed(future_to_url):
            try:
                future.result()  # Вызываем result() для обработки исключений внутри потоков
            except Exception as e:
                logger.error(f"Ошибка в потоке: {e}")

if __name__ == "__main__":
    get_json()
    process_data()
    get_imgs(num_threads=10)  # Укажи нужное количество потоков