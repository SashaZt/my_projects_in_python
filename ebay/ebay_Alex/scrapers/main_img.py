import io
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd
import urllib3
import argparse
from requests.exceptions import (
    ConnectionError,
    HTTPError,
    ProxyError,
    RequestException,
    Timeout,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from urllib3.exceptions import ProtocolError, ReadTimeoutError
from typing import List, Dict, Any
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from config.logger import logger
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

current_directory = Path.cwd()
config_directory = current_directory / "config"
temp_directory = current_directory / "temp"
xlsx_directory = temp_directory / "xlsx"


temp_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)



product_details = xlsx_directory / "product_details.xlsx"
product_details_updated = xlsx_directory / "product_details_updated.xlsx"
config_file = config_directory / "config.json"

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "dnt": "1",
    "priority": "u=0, i",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-full-version": '"135.0.7049.115"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"19.0.0"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
}


def load_proxies():
    """
    Загружает список прокси-серверов из config.json
    """
    global proxy_list
    try:
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)

                # Проверяем формат данных в config.json
                if "proxy_server" in config and isinstance(
                    config["proxy_server"], list
                ):
                    proxy_list = config["proxy_server"]
                    logger.info(
                        f"Загружено {len(proxy_list)} прокси-серверов из config.json"
                    )
                else:
                    logger.warning("В config.json отсутствует список прокси-серверов")
        else:
            logger.warning("Файл config.json не найден")
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации прокси: {str(e)}")


def get_random_proxy():
    """
    Возвращает случайный прокси из списка
    """
    if not proxy_list:
        return None

    proxy_url = random.choice(proxy_list)
    # Удаляем лишние пробелы в URL прокси (если они есть)
    proxy_url = proxy_url.strip()

    return {"http": proxy_url, "https": proxy_url}


@retry(
    stop=stop_after_attempt(10),
    wait=wait_exponential(
        multiplier=1, min=4, max=60
    ),  # Экспоненциальная задержка: 4, 8, 16, 32, 60, 60...
    retry=(
        retry_if_exception_type(HTTPError)
        | retry_if_exception_type(ConnectionError)
        | retry_if_exception_type(Timeout)
        | retry_if_exception_type(ProxyError)
        | retry_if_exception_type(ProtocolError)
        | retry_if_exception_type(ReadTimeoutError)
        | retry_if_exception_type(OSError)
    ),
)
def download_single_image(image_url, file_path, thread_id):
    """
    Скачивает одно изображение с использованием прокси и конвертирует в WebP
    """
    # Проверяем, существует ли файл
    if file_path.exists():
        logger.info(f"Поток {thread_id}: Файл уже существует, пропускаем: {file_path}")
        return True

    # Получаем случайный прокси для этого потока
    proxies = get_random_proxy()
    # logger.info(f"Поток {thread_id}: Используем прокси {proxies}")

    response = requests.get(
        image_url,
        proxies=proxies,
        headers=headers,
        timeout=30,
        verify=False,  # Отключает проверку SSL сертификатов
    )
    response.raise_for_status()  # Вызывает HTTPError, если статус не 200

    try:
        # Открываем изображение из байтов
        image = Image.open(io.BytesIO(response.content))

        # Конвертируем в RGB если необходимо (для WebP с прозрачностью)
        if image.mode in ("RGBA", "LA", "P"):
            # Создаем белый фон
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(
                image, mask=image.split()[-1] if image.mode == "RGBA" else None
            )
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # Сохраняем как JPG
        image.save(file_path, "WEBP", quality=90)

    except Exception as e:
        logger.error(f"Поток {thread_id}: Ошибка при конвертации изображения: {e}")
        # Если конвертация WebP не удалась, пропускаем файл
        raise  # Пробрасываем исключение дальше

    return True


def download_image_task(task_data):
    """
    Задача для скачивания одного изображения
    task_data: словарь с данными о задаче
    """
    image_url = task_data["image_url"]
    file_path = task_data["file_path"]
    product_id = task_data["product_id"]
    image_key = task_data["image_key"]
    thread_id = threading.current_thread().ident

    try:

        # Создаем папку если не существует
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Скачиваем изображение
        download_single_image(image_url, file_path, thread_id)

        return {
            "success": True,
            "product_id": product_id,
            "image_key": image_key,
            "file_path": str(file_path),
            "relative_path": f"images/{product_id}/{file_path.name}",
        }

    except Exception as e:
        logger.error(
            f"Поток {thread_id}: Ошибка при скачивании {image_key} для товара {product_id}: {e}"
        )
        return {
            "success": False,
            "product_id": product_id,
            "image_key": image_key,
            "error": str(e),
        }


def download_images_and_update_json_threaded(json_data, max_workers=5):
    """
    Скачивает изображения из JSON данных используя многопоточность и обновляет пути к изображениям.

    Args:
        json_data: Список словарей с данными о товарах
        max_workers: Максимальное количество потоков

    Returns:
        list: Обновленный список с локальными путями к изображениям
    """
    # Загружаем прокси
    load_proxies()

    if not proxy_list:
        logger.warning("Прокси не загружены, скачивание может работать медленно")

    # Создаем базовую папку для изображений
    base_images_dir = Path("images")
    base_images_dir.mkdir(exist_ok=True)

    # Подготавливаем задачи для скачивания
    download_tasks = []
    product_data_map = {}
    results = {}

    for item in json_data:
        # Копируем исходный элемент
        updated_item = item.copy()

        # Извлекаем product_id
        product_id = item.get("product_id", "")
        if not product_id:
            continue

        # Сохраняем данные о продукте
        product_data_map[product_id] = updated_item

        # Создаем папку для товара
        product_dir = base_images_dir / str(product_id)

        # Инициализируем результаты для этого товара
        if product_id not in results:
            results[product_id] = {}

        # Подготавливаем задачи для каждого изображения
        image_keys = ["url_image_1", "url_image_2", "url_image_3"]

        for i, key in enumerate(image_keys, 1):
            image_url = item.get(key, "")

            if image_url and image_url.strip():
                # Всегда используем .webp расширение, так как конвертируем все изображения
                filename = f"{i:02d}.webp"

                file_path = product_dir / filename

                # Проверяем, существует ли файл
                if file_path.exists():
                    logger.info(f"Файл уже существует, используем: {file_path}")
                    # Добавляем в результаты без скачивания
                    results[product_id][key] = f"images/{product_id}/{filename}"
                    continue

                # Добавляем задачу только если файл не существует
                download_tasks.append(
                    {
                        "image_url": image_url,
                        "file_path": file_path,
                        "product_id": product_id,
                        "image_key": key,
                    }
                )
            else:
                # Если URL пустой, ставим None
                results[product_id][key] = None

    logger.info(f"Подготовлено {len(download_tasks)} задач для скачивания изображений")

    # Выполняем скачивание в многопоточном режиме
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Отправляем задачи на выполнение
        future_to_task = {
            executor.submit(download_image_task, task): task for task in download_tasks
        }

        # Обрабатываем результаты по мере выполнения
        for future in as_completed(future_to_task):
            result = future.result()
            product_id = result["product_id"]
            image_key = result["image_key"]

            if product_id not in results:
                results[product_id] = {}

            if result["success"]:
                results[product_id][image_key] = result["relative_path"]
            else:
                # Если скачивание не удалось, ставим None
                results[product_id][image_key] = None

    # Обновляем данные с результатами скачивания
    updated_data = []
    for product_id, product_data in product_data_map.items():
        # Обновляем пути к изображениям - ИСПРАВЛЯЕМ СОПОСТАВЛЕНИЕ КЛЮЧЕЙ
        image_mapping = {
            "url_image_1": "image_1",
            "url_image_2": "image_2",
            "url_image_3": "image_3",
        }

        for url_key, local_key in image_mapping.items():
            if product_id in results and url_key in results[product_id]:
                product_data[local_key] = results[product_id][url_key]
            else:
                # Если нет результата для этого изображения, ставим None
                product_data[local_key] = None

        updated_data.append(product_data)

    logger.info(f"Скачивание завершено для {len(updated_data)} товаров")
    return updated_data

def extract_product_data_compact(file_path):
    """
    Извлекает данные продуктов с условиями:
    - Если нет product_id - пропускаем строку
    - Если нет url_image - ставим None
    
    Args:
        file_path (str): Путь к Excel файлу
        
    Returns:
        list: Список словарей с данными продуктов (только строки с product_id)
    """
    df = pd.read_excel(file_path)
    
    # Проверяем наличие обязательной колонки product_id
    if 'product_id' not in df.columns:
        raise ValueError("Колонка 'product_id' не найдена в файле")
    
    # Все нужные колонки
    all_columns = ['product_id', 'url_image_1', 'url_image_2', 'url_image_3']
    
    result = []
    
    for index, row in df.iterrows():
        # Проверяем наличие product_id и что он не пустой/None
        product_id = row.get('product_id')
        
        # Пропускаем строку если product_id отсутствует, пустой или NaN
        if pd.isna(product_id) or product_id is None or str(product_id).strip() == '':
            continue
        
        # Создаем словарь для текущей строки
        product_dict = {'product_id': str(product_id).strip()}
        
        # Добавляем url_image колонки (None если отсутствуют)
        for col in ['url_image_1', 'url_image_2', 'url_image_3']:
            if col in df.columns:
                value = row.get(col)
                # Проверяем на NaN или пустое значение
                if pd.isna(value) or (isinstance(value, str) and value.strip() == ''):
                    product_dict[col] = None
                else:
                    product_dict[col] = str(value).strip()
            else:
                product_dict[col] = None
        
        result.append(product_dict)
    
    return result

def process_json_file_threaded(input_file,max_workers):
    """
    Обрабатывает JSON файл: скачивает изображения многопоточно и сохраняет обновленный JSON.

    Args:
        input_file: Путь к входному JSON файлу
        output_file: Путь к выходному JSON файлу
        max_workers: Количество потоков для скачивания
    """
    try:
        # Загружаем JSON данные
        # with open(input_file, "r", encoding="utf-8") as f:
        #     json_data = json.load(f)
        
        xlsx_data = extract_product_data_compact(input_file)

        # logger.info(xlsx_data)
        # exit()

        # Обрабатываем данные
        updated_data = download_images_and_update_json_threaded(xlsx_data, max_workers)
        update_excel_with_images(
            product_details, 
            updated_data, 
            product_details_updated
        )

    except FileNotFoundError:
        logger.error(f"Файл {input_file} не найден")
    except json.JSONDecodeError:
        logger.error(f"Ошибка при чтении JSON из файла {input_file}")
    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {e}")

def update_excel_with_images(file_path: str, products_data: List[Dict[str, Any]], output_path: str = None):
    """
    Обновляет Excel файл, добавляя колонки image_1, image_2, image_3 
    и заполняя данные по product_id
    
    Args:
        file_path (str): Путь к исходному Excel файлу
        products_data (List[Dict]): Список словарей с данными продуктов
        output_path (str, optional): Путь для сохранения. Если None, перезаписывает исходный файл
        
    Returns:
        bool: True если успешно, False если ошибка
    """
    try:
        # Читаем существующий Excel файл
        df = pd.read_excel(file_path)
        
        # Добавляем новые колонки если их нет
        new_columns = ['image_1', 'image_2', 'image_3']
        for col in new_columns:
            if col not in df.columns:
                df[col] = None
        
        # Создаем словарь для быстрого поиска по product_id
        products_dict = {str(item['product_id']): item for item in products_data}
        
        # Обновляем данные
        updated_count = 0
        
        # Используем vectorized операции для лучшей производительности
        for index, row in df.iterrows():
            product_id = str(row['product_id'])
            
            if product_id in products_dict:
                product_data = products_dict[product_id]
                
                # Обновляем колонки image_1, image_2, image_3
                for img_col in ['image_1', 'image_2', 'image_3']:
                    if img_col in product_data and product_data[img_col]:
                        df.at[index, img_col] = product_data[img_col]
                
                updated_count += 1
                logger.info(f"Обновлен продукт с ID: {product_id}")
        
        # Сохраняем файл
        save_path = output_path if output_path else file_path
        df.to_excel(save_path, index=False)
        
        logger.info(f"Файл сохранен: {save_path}")
        logger.info(f"Обновлено записей: {updated_count}")
        logger.info(f"Всего записей в файле: {len(df)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении файла: {e}")
        return False

def add_image_columns_only(file_path: str, output_path: str = None):
    """
    Добавляет только колонки image_1, image_2, image_3 без заполнения данных
    
    Args:
        file_path (str): Путь к Excel файлу
        output_path (str, optional): Путь для сохранения
    """
    try:
        df = pd.read_excel(file_path)
        
        # Добавляем новые колонки
        new_columns = ['image_1', 'image_2', 'image_3']
        for col in new_columns:
            if col not in df.columns:
                df[col] = None
                logger.info(f"Добавлена колонка: {col}")
        
        save_path = output_path if output_path else file_path
        df.to_excel(save_path, index=False)
        
        logger.info(f"Файл сохранен с новыми колонками: {save_path}")
        return True
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False

# Пример использования
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Скрипт для обработки URL eBay")
    parser.add_argument("--max_workers", type=int, default=1, help="Количество потоков")
    parser.add_argument("--count", type=int, default=1, help="Количество попыток (по умолчанию: 10)")

    args = parser.parse_args()

    # Валидация аргументов
    if args.max_workers <= 0:
        parser.error("Количество потоков должно быть положительным числом")
    if args.count <= 0:
        parser.error("Количество попыток должно быть положительным числом")


    
    # Запуск основной функции
    count = 0
    while count < args.count:
        try:
            logger.info(f"Попытка {count + 1} из {args.count}")
            if process_json_file_threaded(product_details, args.max_workers):
                logger.info("✅ Успешное выполнение, завершение работы")
                break
            count += 1
        except Exception as e:
            logger.error(f"❌ Ошибка в основном цикле: {e}")
            logger.info("🔄 Повторная попытка через 10 секунд...")
    else:
        logger.info(f"🛑 Достигнуто максимальное количество попыток ({args.count})")
