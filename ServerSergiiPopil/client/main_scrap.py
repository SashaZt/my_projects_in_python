import requests
import json
import urllib.parse
import math
import time
from pathlib import Path
from logger import logger

base_url = "https://allegro.parser.best/allegro/parser.php"
api_key = "xHt2mU3v6qHtm62XG6cJ"

def make_request(base_url, params, retries=5, retry_delay=10):
    """Делает HTTP запрос и возвращает JSON с повторными попытками"""
    for attempt in range(retries):
        try:
            query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
            url = f"{base_url}?{query_string}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Ошибка запроса (попытка {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                logger.info(f"Пауза {retry_delay} секунд перед следующей попыткой")
                time.sleep(retry_delay)
            else:
                logger.error("Достигнуто максимальное количество попыток")
                return None

def save_json(data, filename):
    """Сохраняет данные в JSON файл"""
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_all_pages(category, brand, model, page_limit, params, processed_items=0, start_page=1):
    """Обрабатывает страницы и возвращает цену последнего товара и последнюю сохраненную страницу"""
    last_saved_page = start_page - 1
    for page in range(start_page, page_limit + 1):
        params["page"] = str(page)
        
        # Формируем путь для файла
        model_dir = model.replace(" ", "_")
        filename = Path(str(category)) / brand.lower() / model_dir / f"{page:02d}.json"
        
        # Пропускаем, если файл уже существует
        if filename.exists():
            logger.info(f"Файл уже существует, пропускаем: {filename}")
            last_saved_page = page
            continue

        response = make_request(base_url, params)
        if not response or not response.get("success"):
            logger.error(f"Ошибка при запросе страницы {page} для модели {model}")
            continue

        # Сохраняем JSON
        save_json(response, filename)
        logger.info(f"Сохранен файл: {filename}")
        last_saved_page = page
        # time.sleep(5)
        # Если это последняя страница, возвращаем цену последнего товара
        if page == page_limit:
            products = response.get("products", [])
            if products:
                last_price = products[-1]["price"]
                processed_items += len(products)
                return last_price, processed_items, last_saved_page
    return None, processed_items, last_saved_page

def main(category, query, price_from):
    total_processed = 0
    total_count = None
    current_price_from = price_from
    current_page = 1  # Начинаем с первой страницы

    # Извлекаем марку и модель из query
    query_parts = query.split(" ", 1)
    brand = query_parts[0]  # Первое слово — марка
    model = query_parts[1] if len(query_parts) > 1 else ""  # Всё остальное — модель

    if not model:
        logger.error(f"Некорректный формат строки: {query}")
        return

    while True:
        # Задаем параметры
        params = {
            "category": category,
            "page": "1",
            "api_key": api_key,
            "method": "search",
            "sort": "p",
            "query": query,
            "price_from": current_price_from,
        }

        # Первый запрос для получения totalCount
        initial_response = make_request(base_url, params)
        if not initial_response or not initial_response.get("success"):
            logger.error(f"Ошибка начального запроса для модели {model}")
            return

        # Получаем totalCount и вычисляем количество страниц
        total_count = initial_response.get("totalCount", 0)
        page_limit = min(math.ceil(total_count / 60), 100)  # Ограничиваем 100 страницами за раз

        # Обрабатываем страницы, начиная с current_page
        last_price, processed_items, last_saved_page = get_all_pages(
            category, brand, model, page_limit, params, total_processed, start_page=current_page
        )
        total_processed += processed_items

        # Если обработали все товары или нет последней цены, выходим
        if total_processed >= total_count or last_price is None:
            # logger.info(f"Обработано {total_processed} из {total_count} товаров для модели {model}")
            break

        # Обновляем price_from и следующую страницу
        current_price_from = math.floor(float(last_price))
        current_page = last_saved_page + 1  # Продолжаем с следующей страницы
        # logger.info(f"Перезапуск с price_from = {current_price_from} для модели {model}, следующая страница: {current_page}")

def read_models(filename="model.txt"):
    """Читает список моделей из файла"""
    try:
        with Path(filename).open("r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error(f"Файл {filename} не найден")
        return []

if __name__ == "__main__":
    id_category = 255099
    price_from = "50"
    models = read_models("model.txt")  # Читаем модели из файла

    for model in models:
        query = model  # Используем строку из файла как query
        logger.info(f"Начало обработки: {model}")
        main(id_category, query, price_from)