import json
import re

from bs4 import BeautifulSoup

from config import logger, paths


def extract_product_data(product_json):
    """
    Извлекает данные продукта из JSON структуры

    Args:
        product_json (dict): JSON структура продукта

    Returns:
        dict: Извлеченные данные продукта
    """
    try:

        product_name = product_json.get("name")
        product_url = product_json.get("url")
        sku = product_json.get("sku")
        description = product_json.get("description")
        brand = product_json.get("brand", {}).get("name", None)
        aggregateRating = product_json.get("aggregateRating", {})

        rating = parse_price(aggregateRating.get("ratingValue", None))
        reviews_count = parse_price(aggregateRating.get("reviewCount", None))
        # Создаем итоговый словарь с данными продукта
        data_json = {
            "success": True,
            "id": int(sku),
            "title": product_name,
            "url": product_url,
            "active": True,
            "same_offers_id": None,
            "same_offers_count": 0,
            "buyers": 0,
            "buyers_this_offer": 0,
            "rating": rating,
            "reviews_count": reviews_count,
            "reviews_with_text_count": 0,
            "availableQuantity": 0,
            "price": 0,
            "price_with_delivery": 0.0,
            "currency": "",
            "delivery_price": 0.0,
            "delivery_period": None,
            "delivery_options": [],
            "seller_id": 0,
            "seller_login": None,
            "seller_rating": 0.0,
            "category_path": [{"id": "", "name": "", "url": ""}],
            "specifications": {
                "Parametry": {
                    "Stan": "",
                    "Faktura": "",
                    "Rodzaj": "",
                    "Waga produktu z opakowaniem jednostkowym": "",
                    "EAN (GTIN)": "",
                    "Marka": brand,
                    "Typ": "",
                    "Kod producenta": sku,
                }
            },
            "images": [{"original": "", "thumbnail": "", "embeded": "", "alt": ""}],
            "description": {
                "sections": [{"items": [{"type": "TEXT", "content": description}]}]
            },
            "reviews_rating": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            "reviews": [{"text": "", "score": "", "date": ""}],
            "seller_positive_count": 0,
            "seller_negative_count": 0,
        }

        return data_json
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных продукта: {e}")
        return None


def extract_reviews(soup):
    """
    Альтернативная версия для случая, когда у вас уже есть объект BeautifulSoup
    """
    reviews = []

    # Находим все контейнеры отзывов
    review_containers = soup.find_all(
        "div", class_="col-12 col-container-inner m-review"
    )

    for container in review_containers:
        review_data = {"text": "", "score": "", "date": ""}

        # Извлекаем дату
        date_element = container.find("p", class_="m-review__dates")
        if date_element:
            date_bold = date_element.find("b")
            if date_bold:
                review_data["date"] = date_bold.get_text(strip=True)

        # Извлекаем оценку
        rating_element = container.find("span", class_="m-review__rating__text")
        if rating_element:
            rating_text = rating_element.get_text(strip=True)
            score_match = re.search(r"(\d+)\s*/\s*\d+", rating_text)
            if score_match:
                review_data["score"] = score_match.group(1)

        # Извлекаем текст отзыва
        text_element = container.find("p", class_="m-review__message js-review-text")
        if text_element:
            review_data["text"] = text_element.get_text(strip=True)

        # Добавляем отзыв только если есть хотя бы текст
        if review_data["text"]:
            reviews.append(review_data)

    return reviews


def extract_images(soup):

    # Find all picture elements with the specified class
    pictures = soup.find_all("picture", class_="m-carousel-main__picture lazy")

    # Initialize result list
    result = []

    for picture in pictures:
        # Get the img tag within picture
        alt_text = picture.get("data-alt", "")
        default_url = picture.get("data-default", "")
        clean_url = default_url.split("?")[0] if default_url else ""
        # Формируем словарь
        image_data = {
            "original": clean_url,
            "thumbnail": "",
            "embeded": "",
            "alt": alt_text,
        }

        result.append(image_data)

    return result


def extract_offers(product_json):
    """
    Извлекает данные продукта из JSON структуры

    Args:
        product_json (dict): JSON структура продукта

    Returns:
        dict: Извлеченные данные продукта
    """
    try:
        # logger.info(json.dumps(product_json))
        currency = product_json.get("priceCurrency", None)
        price = parse_price(product_json.get("price"))

        # Создаем итоговый словарь с данными продукта

        return currency, price
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных продукта: {e}")
        return None


def find_json_ld_objects(data, target_type):
    """Рекурсивно ищет объекты с определенным @type"""
    results = []

    if isinstance(data, dict):
        if data.get("@type") == target_type:
            results.append(data)

        for value in data.values():
            results.extend(find_json_ld_objects(value, target_type))

    elif isinstance(data, list):
        for item in data:
            results.extend(find_json_ld_objects(item, target_type))

    return results


def parse_price(price_value):
    """
    Универсальный парсер цен с поддержкой различных форматов:
    "999", "999.99", "1,234.56", "1 234,56", "$999", "999 PLN", etc.
    """
    if price_value is None:
        return None

    # Если уже число
    if isinstance(price_value, (int, float)):
        return price_value  # Возвращаем как есть

    # Если строка
    if isinstance(price_value, str):
        # Убираем валютные символы и буквы
        price_str = re.sub(r"[^\d\s,.-]", "", price_value.strip())

        if not price_str:
            return None

        # Определяем формат числа
        # Если есть точка и запятая, точка - десятичный разделитель
        if "." in price_str and "," in price_str:
            if price_str.rindex(".") > price_str.rindex(","):
                # Формат: 1,234.56
                price_str = price_str.replace(",", "")
            else:
                # Формат: 1.234,56
                price_str = price_str.replace(".", "").replace(",", ".")

        # Если только запятая - может быть десятичным разделителем
        elif "," in price_str and price_str.count(",") == 1:
            # Проверяем, сколько цифр после запятой
            parts = price_str.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Скорее всего десятичный разделитель
                price_str = price_str.replace(",", ".")
            else:
                # Скорее всего разделитель тысяч
                price_str = price_str.replace(",", "")

        # Убираем все пробелы
        price_str = price_str.replace(" ", "")

        try:
            # Проверяем, есть ли десятичная часть
            if "." in price_str:
                result = float(price_str)
                # Если десятичная часть равна 0, возвращаем int
                if result == int(result):
                    return int(result)
                return result
            else:
                return int(price_str)
        except ValueError:
            return None

    return None


def parse_tms_data(script_content):
    """Парсит данные из dataTms скрипта"""
    try:
        json_data = json.loads(script_content)

        if isinstance(json_data, list):
            # Преобразуем массив name-value в словарь
            result = {}
            for item in json_data:
                if isinstance(item, dict) and "name" in item and "value" in item:
                    result[item["name"]] = item["value"]
            return result

        return {}
    except json.JSONDecodeError:
        return {}


def extract_categories_from_tms(tms_data):
    """Извлекает все категории из TMS данных"""
    categories = []

    # Собираем все номера категорий
    category_nums = set()
    for key in tms_data.keys():
        if key.startswith("cdl_page_category") and key not in [
            "cdl_page_level",
            "cdl_page_name",
        ]:
            # Извлекаем номер из ключа
            if "_id" in key:
                num = key.replace("cdl_page_category", "").replace("_id", "")
            else:
                num = key.replace("cdl_page_category", "")

            if num.isdigit():
                category_nums.add(num)

    # Создаем список категорий в порядке номеров
    for num in sorted(category_nums, key=int):
        name_key = f"cdl_page_category{num}"
        id_key = f"cdl_page_category{num}_id"

        name = tms_data.get(name_key, "")
        category_id = tms_data.get(id_key, "")

        if name:  # Добавляем только если есть название
            categories.append({"id": category_id, "name": name, "url": ""})

    return categories


def extract_rating_statistics(soup):
    """
    Извлекает статистику рейтингов из soup объекта

    Args:
        soup: BeautifulSoup объект

    Returns:
        dict: Словарь с количеством отзывов для каждой оценки
        {
            "1": 5,
            "2": 5,
            "3": 15,
            "4": 57,
            "5": 129
        }
    """
    rating_stats = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

    # Находим контейнер с рейтингами
    rating_container = soup.find("div", class_="m-review__rating-container")

    if not rating_container:
        return rating_stats

    # Находим все элементы с рейтингами
    rating_items = rating_container.find_all(
        "div", class_="m-review__rating m-review__rating-clickable"
    )

    for item in rating_items:
        # Извлекаем количество звезд из onclick атрибута
        onclick_attr = item.get("onclick", "")
        stars_match = re.search(r"nbOfStars=(\d+)", onclick_attr)

        if stars_match:
            stars = stars_match.group(1)

            # Находим количество отзывов (последний <p> элемент в этом блоке)
            count_element = item.find("p")
            if count_element:
                try:
                    count = int(count_element.get_text(strip=True))
                    rating_stats[stars] = count
                except ValueError:
                    # Если не удается конвертировать в число, оставляем 0
                    rating_stats[stars] = 0

    return rating_stats


def scrap_htmls():
    # Список для хранения данных
    # Проверяем наличие HTML-файлов
    html_files = list(paths.html.glob("*.html"))
    # Проходим по всем HTML-файлам в папке
    for html_file in html_files:
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        try:
            # Инициализируем как список, а не словарь
            product_data = {}

            soup = BeautifulSoup(content, "lxml")
            # Находим все скрипты с типом application/json
            scripts = soup.find_all("script", type="application/json")

            if not scripts:
                logger.warning(
                    f"В файле {html_file.name} не найдено скриптов с типом application/json"
                )
                continue
            category_path = None
            for script in scripts:
                script_text = script.string
                if not script_text or not script_text.strip():
                    continue

                try:

                    json_data = json.loads(script_text)

                    # Ищем все Product объекты
                    products = find_json_ld_objects(json_data, "Product")
                    for product in products:
                        main_product = extract_product_data(product)
                        if main_product:
                            product_data.update(main_product)

                    # Ищем все Offer объекты
                    offers = find_json_ld_objects(json_data, "Offer")
                    for offer in offers:
                        currency, price = extract_offers(offer)
                        product_data["currency"] = currency
                        product_data["price"] = price
                    # Для TMS данных (массив name-value)
                    if isinstance(json_data, list) and all(
                        isinstance(item, dict) and "name" in item and "value" in item
                        for item in json_data
                        if isinstance(item, dict)
                    ):
                        tms_data = parse_tms_data(script_text)
                        if tms_data is not None:
                            # logger.info(tms_data)
                            categories = extract_categories_from_tms(tms_data)

                            if categories:
                                category_path = categories

                except json.JSONDecodeError:
                    continue
            product_data["category_path"] = category_path
            images = extract_images(soup)
            product_data["images"] = images
            reviews = extract_reviews(soup)
            product_data["reviews"] = reviews
            reviews_rating = extract_rating_statistics(soup)
            product_data["reviews_rating"] = reviews_rating
            file_path = paths.json / "file_name.json"
            with open(file_path, "w", encoding="utf-8") as json_file:
                json.dump(product_data, json_file, ensure_ascii=False, indent=4)

        except Exception as e:
            logger.error(f"Ошибка при обработке {html_file.name}: {str(e)}")


if __name__ == "__main__":
    scrap_htmls()
