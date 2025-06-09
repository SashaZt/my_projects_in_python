# /scrap.py
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

from bs4 import BeautifulSoup

from config import logger, paths

# Блокировка для безопасного логирования
log_lock = Lock()


def safe_logger_info(message):
    """Безопасное логирование в многопоточной среде"""
    with log_lock:
        logger.info(message)


def safe_logger_error(message):
    """Безопасное логирование ошибок в многопоточной среде"""
    with log_lock:
        logger.error(message)


# def pars_htmls():
#     logger.info(f"Собираем данные со страниц {paths.html}")

#     html_files = list(paths.html.glob("*.html"))
#     # Пройтись по каждому HTML файлу в папке
#     for html_file in html_files:
#         # Имя без раширения
#         file_name = html_file.stem
#         with html_file.open(encoding="utf-8") as file:
#             content = file.read()

#         # Парсим HTML с помощью BeautifulSoup
#         soup = BeautifulSoup(content, "lxml")
#         product = soup.find("script", attrs={"id": "pip-range-json-ld"})
#         json_string = product.string
#         all_data = scrap_json(json_string)

#         json_breadcrumblist = soup.find("script", attrs={"type": "application/ld+json"})
#         product_breadcrumblist = json_breadcrumblist.string
#         category_path = extract_category_path(product_breadcrumblist)
#         all_data["category_path"] = category_path
#         file_path = paths.json / f"{file_name}.json"
#         with open(file_path, "w", encoding="utf-8") as json_file:
#             json.dump(all_data, json_file, ensure_ascii=False, indent=4)


def process_single_html(html_file):
    """
    Обрабатывает один HTML файл
    """
    try:
        # Имя без расширения
        file_name = html_file.stem

        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        product = soup.find("script", attrs={"id": "pip-range-json-ld"})

        if not product or not product.string:
            safe_logger_error(f"Не найден JSON в файле {file_name}")
            return False

        json_string = product.string
        all_data = scrap_json(json_string)

        json_breadcrumblist = soup.find("script", attrs={"type": "application/ld+json"})
        if json_breadcrumblist and json_breadcrumblist.string:
            product_breadcrumblist = json_breadcrumblist.string
            category_path = extract_category_path(product_breadcrumblist)
            all_data["category_path"] = category_path

        # Сохраняем JSON файл
        file_path = paths.json / f"{file_name}.json"
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(all_data, json_file, ensure_ascii=False, indent=4)

        safe_logger_info(f"Файл {file_name} обработан успешно")
        return True

    except Exception as e:
        safe_logger_error(f"Ошибка при обработке файла {html_file.name}: {e}")
        return False


def pars_htmls_multithreaded(max_workers=50):
    """
    Многопоточная обработка HTML файлов
    """
    safe_logger_info(f"Запуск многопоточной обработки с {max_workers} потоками")
    safe_logger_info(f"Собираем данные со страниц {paths.html}")

    html_files = list(paths.html.glob("*.html"))

    if not html_files:
        safe_logger_info("HTML файлы не найдены")
        return

    safe_logger_info(f"Найдено {len(html_files)} HTML файлов для обработки")

    # Статистика
    start_time = time.time()
    successful = 0
    failed = 0

    # Запускаем многопоточную обработку
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Отправляем задачи в пул потоков
        future_to_file = {
            executor.submit(process_single_html, html_file): html_file
            for html_file in html_files
        }

        # Обрабатываем результаты по мере завершения
        for future in as_completed(future_to_file):
            html_file = future_to_file[future]
            try:
                result = future.result()
                if result:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                safe_logger_error(f"Исключение при обработке {html_file.name}: {e}")
                failed += 1

    # Финальная статистика
    end_time = time.time()
    processing_time = end_time - start_time

    safe_logger_info("=" * 50)
    safe_logger_info("СТАТИСТИКА ОБРАБОТКИ:")
    safe_logger_info(f"Всего файлов: {len(html_files)}")
    safe_logger_info(f"Успешно обработано: {successful}")
    safe_logger_info(f"Ошибок: {failed}")
    safe_logger_info(f"Время обработки: {processing_time:.2f} секунд")
    safe_logger_info(f"Скорость: {len(html_files)/processing_time:.2f} файлов/сек")
    safe_logger_info("=" * 50)


def scrap_json(json_string):
    json_data = None
    # Убеждаемся, что содержимое не None
    if json_string:
        try:
            # Парсим строку как JSON
            json_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка при парсинге JSON: {e}")
    availability = json_data.get("offers", {}).get("availability", "").split("/")[-1]
    if availability == "InStock":
        active = True
    else:
        active = False
    sku = json_data.get("sku", "")
    id_value = int(sku.replace(".", ""))
    images = json_data.get("image", [])
    transformed_images = transform_images(images)
    descriptions = json_data.get("description", "")
    reviews = json_data.get("review", [])
    transformed_reviews = transform_reviews(reviews)
    reviews_rating = transform_reviews_rating(reviews)
    product = {
        "success": True,
        "id": id_value,  # SKU как уникальный идентификатор
        "title": json_data.get("name", ""),  # Название на польском
        "url": json_data.get("url", ""),  # URL продукта
        "active": active,
        "same_offers_id": None,
        "same_offers_count": 0,
        "buyers": 0,
        "buyers_this_offer": 0,
        "rating": float(
            json_data.get("aggregateRating", {}).get("ratingValue", 0)
        ),  # Средний рейтинг
        "reviews_count": int(
            json_data.get("aggregateRating", {}).get("reviewCount", 0)
        ),  # Количество отзывов
        "reviews_with_text_count": 0,
        "availableQuantity": 0,
        "price": float(json_data.get("offers", {}).get("price", 0)),  # Цена
        "price_with_delivery": 0.0,
        "currency": json_data.get("offers", {}).get("priceCurrency", ""),  # Валюта
        "delivery_price": 0.0,
        "delivery_period": None,
        "delivery_options": [],
        "seller_id": 0,
        "seller_login": None,
        "seller_rating": 0.0,
        "specifications": {
            "Parametry": {
                "Stan": "",
                "Faktura": "",
                "Rodzaj": "",
                "Waga produktu z opakowaniem jednostkowym": "",
                "EAN (GTIN)": "",
                "Marka": json_data.get("brand", {}).get("name", ""),  # Бренд
                "Typ": "",
                "Kod producenta": sku,
            }
        },
        "description": {
            "sections": [{"items": [{"type": "TEXT", "content": descriptions}]}]
        },
        "images": transformed_images,  # Список URL изображений
        "reviews": transformed_reviews,  # Список отзывов
        "reviews_rating": reviews_rating,  # Список отзывов
        "seller_positive_count": 0,
        "seller_negative_count": 0,
    }
    # logger.info(json.dumps(product))
    return product


def transform_images(images):
    """
    Подготовка фото под формат шаблона
    """
    return [
        {"original": url, "thumbnail": "", "embeded": "", "alt": ""} for url in images
    ]


def extract_category_path(json_data):
    """
    Подготовка категорий под формат шаблона
    """
    category_path = []
    json_data = json.loads(json_data)
    items = json_data.get("itemListElement", [])
    for item in items[1:]:  # Пропускаем первый элемент
        url = item.get("item", "")
        # Извлекаем id из последней части URL
        match = re.search(r"/([^/]+)-([^/]+)/?$", url)
        category_id = ""
        if match:
            # Берем последнюю часть после дефиса
            category_id = match.group(2)

        category_path.append(
            {"id": category_id, "name": item.get("name", ""), "url": url}
        )

    return category_path


def transform_reviews(reviews):
    """
    Подготовка отзывов под формат шаблона
    """
    return [
        {
            "text": review.get("reviewBody", ""),
            "score": str(review.get("reviewRating", {}).get("ratingValue", "")),
            "date": "",
        }
        for review in reviews
    ]


def transform_reviews_rating(reviews):
    # Инициализируем словарь для подсчёта оценок
    rating_counts = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

    # Подсчитываем количество отзывов для каждой оценки
    total_ratings = 0
    sum_ratings = 0
    for review in reviews:
        rating = str(review.get("reviewRating", {}).get("ratingValue", 0))
        if rating in rating_counts:
            rating_counts[rating] += 1
            total_ratings += 1
            sum_ratings += int(rating)

    # Вычисляем среднюю оценку
    average_rating = sum_ratings / total_ratings if total_ratings > 0 else 0

    # Добавляем среднюю оценку в результат
    result = rating_counts
    return result


if __name__ == "__main__":
    # pars_htmls()
    # Многопоточный режим (рекомендуется)
    pars_htmls_multithreaded(max_workers=50)
