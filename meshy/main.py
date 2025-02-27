import json
import sys
import time
from pathlib import Path
from PIL import Image
from io import BytesIO
import pandas as pd
import requests
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import wget


current_directory = Path.cwd()
json_original_directory = current_directory / "json_original"
json_product_directory = current_directory / "json_product"
log_directory = current_directory / "log"
img_directory = current_directory / "img"
thumbnailUrl_directory = current_directory / "thumbnailUrl"

img_directory.mkdir(parents=True, exist_ok=True)
json_original_directory.mkdir(parents=True, exist_ok=True)
json_original_directory.mkdir(parents=True, exist_ok=True)
thumbnailUrl_directory.mkdir(parents=True, exist_ok=True)

log_file_path = log_directory / "log_message.log"

BASE_URL = "https://static-cos.mureka.ai/"
FILE_NAME_JSON = "3d"



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
    'sajssdk_2015_cross_new_user': '1',
    'sensorsdata2015jssdkcross': '%7B%22distinct_id%22%3A%221953e188ce71aee-0850c4a727ae878-26011a51-2304000-1953e188ce81b82%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk1M2UxODhjZTcxYWVlLTA4NTBjNGE3MjdhZTg3OC0yNjAxMWE1MS0yMzA0MDAwLTE5NTNlMTg4Y2U4MWI4MiJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%7D',
    '__stripe_mid': 'f338a4a2-d0ce-4827-ab76-a73a4d4b950cb113e2',
    '__stripe_sid': '739b6d27-e30c-4f66-8d63-34d46d472839560169',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'ru,en;q=0.9,uk;q=0.8',
    'dnt': '1',
    'priority': 'u=1, i',
    'referer': 'https://www.mureka.ai/genre-detail?id=6&name=afrobeat',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'x-app-name': 'Mureka',
    'x-auth-timestamp': '1740505056227',
    'x-firebase-id': '',
    'x-source': 'IntcIiRsYXRlc3RfdHJhZmZpY19zb3VyY2VfdHlwZVwiOlwi55u05o6l5rWB6YePXCIsXCIkbGF0ZXN0X3NlYXJjaF9rZXl3b3JkXCI6XCLmnKrlj5bliLDlgLxf55u05o6l5omT5byAXCIsXCIkbGF0ZXN0X3JlZmVycmVyXCI6XCJcIn0i',
    'x-user-agent': 'en/1.0.1/web/android/web/1953e188ce71aee-0850c4a727ae878-26011a51-2304000-1953e188ce81b82/unknown//3x',
    # 'cookie': 'sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221953e188ce71aee-0850c4a727ae878-26011a51-2304000-1953e188ce81b82%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E7%9B%B4%E6%8E%A5%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC_%E7%9B%B4%E6%8E%A5%E6%89%93%E5%BC%80%22%2C%22%24latest_referrer%22%3A%22%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTk1M2UxODhjZTcxYWVlLTA4NTBjNGE3MjdhZTg3OC0yNjAxMWE1MS0yMzA0MDAwLTE5NTNlMTg4Y2U4MWI4MiJ9%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%7D; __stripe_mid=f338a4a2-d0ce-4827-ab76-a73a4d4b950cb113e2; __stripe_sid=739b6d27-e30c-4f66-8d63-34d46d472839560169',
}

# def get_json():
#     for page in range(1, 11):
#         if page == 1:
#             params = {
#             'param': FILE_NAME_JSON,
#         }
#             url = f'https://www.freepik.com/_next/data/dbTWBGYytMf6qZVClARjW/en/templates/{FILE_NAME_JSON}.json'
#         else:
#             params = {
#             'param': [
#                 FILE_NAME_JSON,
#                 page,
#             ],
#             }
#             url = f'https://www.freepik.com/_next/data/dbTWBGYytMf6qZVClARjW/en/templates/{FILE_NAME_JSON}/{page}.json'

#         output_file = json_original_directory / FILE_NAME_JSON / f"{FILE_NAME_JSON}_{page}.json"
#         output_file.parent.mkdir(parents=True, exist_ok=True)
#         if output_file.exists():
#             continue
#         response = requests.get(
#             url,
#             params=params,
#             cookies=cookies,
#             headers=headers,
#             timeout=30,
#         )

        
#         # Если сервер вернул корректный JSON, то выводим его:
#         try:
#             data = response.json()
#             with open(output_file, "w", encoding="utf-8") as f:
#                 json.dump(data, f, ensure_ascii=False, indent=4)  # Записываем в файл
#             logger.info(f"Сохранил {output_file}")
#         except ValueError:
#             logger.error("Ошибка: ответ не содержит JSON")

def get_meshy_showcases(start_page=1, end_page=51, page_size=20):
    """
    Получает данные витрины (showcases) с API Meshy.ai с указанной страницы по указанную
    и сохраняет их в JSON файлы.
    
    Args:
        start_page (int): Начальная страница
        end_page (int): Конечная страница
        page_size (int): Размер страницы (количество элементов на странице)
    """
    # Создаем директорию для сохранения JSON файлов
    output_dir = Path("meshy_showcases")
    output_dir.mkdir(exist_ok=True)
    
    # Заголовки запроса, как в примере curl
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru,en;q=0.9,uk;q=0.8',
        'dnt': '1',
        'origin': 'https://www.meshy.ai',
        'referer': 'https://www.meshy.ai/',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
    }
    
    # Базовый URL API
    base_url = 'https://api.meshy.ai/web/public/showcases'
    
    total_items = 0
    
    for page_num in range(start_page, end_page + 1):
        logger.info(page_num)
        # Параметры запроса
        params = {
            'sortBy': '-created_at',
            'pageSize': page_size,
            'pageNum': page_num,
            'includeNSFW': 'false',
            'isFeatured': 'true',
            'search': '',
            'artStyle': ''
        }
        
        try:
            # Отправляем запрос к API
            response = requests.get(base_url, params=params, headers=headers,timeout=30)
            
            # Проверяем успешность запроса
            if response.status_code == 200:
                # Парсим JSON-ответ
                data = response.json()
                
                # # Получаем количество элементов в ответе
                # items_count = len(data.get('data', []))
                # total_items += items_count
                
                # Формируем имя файла
                file_name = json_original_directory / f"meshy_showcases_page_{page_num}.json"
                if file_name.exists():
                    continue
                # Сохраняем ответ в JSON файл
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                # logger.info(f"Страница {page_num}: Сохранено {items_count} элементов в {file_name}")
                
                # # Если в ответе нет элементов, значит мы достигли конца
                # if items_count == 0:
                #     logger.error(f"Достигнут конец данных на странице {page_num}")
                #     break
                    
            else:
                logger.error(f"Ошибка запроса для страницы {page_num}: {response.status_code}")
                logger.error(response.text)
            
            # Добавляем паузу между запросами, чтобы не перегрузить сервер
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Ошибка при запросе страницы {page_num}: {e}")
    

def process_data():
    all_data = []
    for json_file in json_original_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        json_datas = data["result"]
        for json_data in json_datas:
            id_product = json_data.get("id", None)
            objectPrompt = json_data.get("objectPrompt", None)
            modelUrl = json_data.get("modelUrl", None)
            thumbnailUrl = json_data.get("thumbnailUrl", None)
            solidThumbnailUrl = json_data.get("solidThumbnailUrl", None)
            categories = ", ".join(json_data.get("categories", []))
            tags = ", ".join(json_data.get("tags", []))
            data_product = {
                "id_product":id_product,
                "objectPrompt":objectPrompt,
                "modelUrl":modelUrl,
                "thumbnailUrl":thumbnailUrl,
                "solidThumbnailUrl":solidThumbnailUrl,
                "categories":categories,
                "tags":tags,
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

def save_glbs(url, name):
    """Функция загружает и сохраняет изображение."""
    try:
        
        file_name = img_directory / FILE_NAME_JSON / f"{name}.glb"
        file_name.parent.mkdir(parents=True, exist_ok=True)

        if file_name.exists():
            logger.error(file_name)
            return
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        if response.status_code == 200:
            # Используем режим потоковой записи для больших файлов
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192): 
                    f.write(chunk)
            logger.info(f"3D модель сохранена как {file_name}")
        else:
            logger.error(f"Ошибка при загрузке {url}: {response.status_code}")

    except Exception as e:
        logger.error(f"Ошибка при загрузке {url}: {e}")

def get_glbs(num_threads=5):
    """Функция парсит JSON и многопоточно скачивает изображения."""
    output_directory = json_product_directory / FILE_NAME_JSON
    image_tasks = []

    # Собираем все данные для загрузки
    for json_file in output_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            datas = json.load(file)

        for data in datas:
            id_product = data.get("id_product")
            modelUrl = data.get("modelUrl")
            if id_product and modelUrl:
                image_tasks.append((modelUrl, id_product))
            else:
                logger.error(f"Отсутствуют данные в файле {json_file}")

    # Многопоточная загрузка изображений
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_url = {executor.submit(save_glbs, url, slug): url for url, slug in image_tasks}

        for future in as_completed(future_to_url):
            try:
                future.result()  # Вызываем result() для обработки исключений внутри потоков
            except Exception as e:
                logger.error(f"Ошибка в потоке: {e}")
def save_thumbnai(url, name):
    """Функция загружает и сохраняет MP3 файл."""
    try:
        # Создаем путь безопасным способом
        save_dir = thumbnailUrl_directory / FILE_NAME_JSON
        save_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = save_dir / f"{name}.jpg"
        
        if file_name.exists():
            logger.error(f"Файл уже существует: {file_name}")
            return
        
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        if response.status_code == 200:
            try:
                # Для AVIF и других проблемных форматов используем альтернативные подходы
                if '.avif' in url.lower():
                    # Сохраняем как есть, а затем попробуем открыть с помощью PIL
                    temp_path = str(file_name).replace('.jpg', '.temp')
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                        
                    try:
                        # Пробуем открыть через PIL для конвертации
                        image = Image.open(temp_path)
                        image.save(file_name, "JPEG")
                        os.remove(temp_path)  # Удаляем временный файл
                    except Exception as img_error:
                        logger.warning(f"Не удалось конвертировать AVIF, сохраняем как есть: {img_error}")
                        # Если не удалось конвертировать, просто переименуем
                        os.rename(temp_path, str(file_name))
                else:
                    # Обычный путь для стандартных форматов
                    image = Image.open(BytesIO(response.content))
                    image.save(file_name, "JPEG")
                
                logger.info(f"Изображение сохранено как {file_name}")
            except Exception as img_error:
                # Если не удалось обработать изображение, сохраняем файл как есть
                logger.warning(f"Не удалось обработать изображение, сохраняем как есть: {img_error}")
                with open(file_name, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Файл сохранен без обработки: {file_name}")
        else:
            logger.error(f"Ошибка при загрузке {url}: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке {url}: {e}")

def get_thumbnais(num_threads=10):
    """Функция парсит JSON и многопоточно скачивает изображения."""
    output_directory = json_product_directory / FILE_NAME_JSON
    image_tasks = []

    # Собираем все данные для загрузки
    for json_file in output_directory.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as file:
            datas = json.load(file)

        for data in datas:
            id_product = data.get("id_product")
            thumbnailUrl = data.get("thumbnailUrl")
            if id_product and thumbnailUrl:
                image_tasks.append((thumbnailUrl, id_product))
            else:
                logger.error(f"Отсутствуют данные в файле {json_file}")

    # Многопоточная загрузка изображений
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_url = {executor.submit(save_thumbnai, url, slug): url for url, slug in image_tasks}

        for future in as_completed(future_to_url):
            try:
                future.result()  # Вызываем result() для обработки исключений внутри потоков
            except Exception as e:
                logger.error(f"Ошибка в потоке: {e}")

if __name__ == "__main__":
    # get_meshy_showcases()
    # get_json()
    # process_data()
    get_glbs(num_threads=10)  # Укажи нужное количество потоков
    get_thumbnais(num_threads=10)  # Укажи нужное количество потоков