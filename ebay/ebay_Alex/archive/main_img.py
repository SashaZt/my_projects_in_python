import io
import json
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import urllib3
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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
from logger import logger
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

current_directory = Path.cwd()
data_directory = current_directory / "data"
config_directory = current_directory / "config"
data_directory.mkdir(parents=True, exist_ok=True)
config_directory.mkdir(parents=True, exist_ok=True)
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)

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


def process_json_file_threaded(input_file, output_file, max_workers=5):
    """
    Обрабатывает JSON файл: скачивает изображения многопоточно и сохраняет обновленный JSON.

    Args:
        input_file: Путь к входному JSON файлу
        output_file: Путь к выходному JSON файлу
        max_workers: Количество потоков для скачивания
    """
    try:
        # Загружаем JSON данные
        with open(input_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)

        logger.info(f"Загружено {len(json_data)} товаров из {input_file}")

        # Обрабатываем данные
        updated_data = download_images_and_update_json_threaded(json_data, max_workers)

        # Сохраняем обновленные данные
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)

        logger.info(
            f"Обработка завершена. Обновленные данные сохранены в {output_file}"
        )

    except FileNotFoundError:
        logger.error(f"Файл {input_file} не найден")
    except json.JSONDecodeError:
        logger.error(f"Ошибка при чтении JSON из файла {input_file}")
    except Exception as e:
        logger.error(f"Ошибка при обработке файла: {e}")


# Пример использования
if __name__ == "__main__":
    # Обрабатываем файл с 10 потоками
    process_json_file_threaded("product_details.json", "result.json", max_workers=40)
