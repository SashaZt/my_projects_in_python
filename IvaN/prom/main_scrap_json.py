import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from config.logger import logger

# Настройка директорий
current_directory = Path.cwd()
json_id_directory = current_directory / "json_id"
json_products_directory = current_directory / "json_products"
json_review_directory = current_directory / "json_review"
config_directory = current_directory / "config"
config_directory.mkdir(parents=True, exist_ok=True)
json_id_directory.mkdir(parents=True, exist_ok=True)
json_products_directory.mkdir(parents=True, exist_ok=True)
json_review_directory.mkdir(parents=True, exist_ok=True)


def scrap_json_company():
    all_data = []
    files = list(json_id_directory.glob("*.json"))
    # Пройтись по каждому HTML файлу в папке
    for json_file in files:
        with open(json_file, "r", encoding="utf-8") as file:
            input_data = json.load(file)
        logger.info(json_file)
        try:
            # Проверка 1: Убедимся, что input_data — словарь
            if not isinstance(input_data, dict):
                print("Ошибка: input_data не является словарем")
                return {}

            # Проверка 2: Безопасно извлекаем 'data' и 'company'
            data = input_data.get("data", {})
            if not isinstance(data, dict):
                print("Ошибка: 'data' не является словарем")
                return {}

            company_data = data.get("company", {})
            if not isinstance(company_data, dict):
                print("Ошибка: 'company' не является словарем")
                return {}

            # Извлекаем необходимые поля с безопасной обработкой

            result = {
                # Проверка 3: Извлечение 'id'
                "companyId": company_data.get("id"),
                # Проверка 4: Извлечение 'name' с очисткой от лишних символов
                "companyName": (
                    company_data.get("name").replace('"', "").replace("\\", "")
                    if company_data.get("name")
                    and isinstance(company_data.get("name"), str)
                    else None
                ),
                # Проверка 5: Извлечение простых полей
                "companyPerson": company_data.get("contactPerson"),
                "companyEmail": company_data.get("contactEmail"),
                "companyAddress": company_data.get("addressText"),
                "companySlug": company_data.get("slug"),
                "companyWebsite": company_data.get("webSiteUrl"),
                # Проверка 6: Извлечение 'phones' с очисткой номеров
                "companyPhones": (
                    [
                        phone.get("number")
                        .replace(" ", "")
                        .replace("(", "")
                        .replace(")", "")
                        .replace("-", "")
                        .replace('"', "")
                        for phone in company_data.get("phones", [])
                        if isinstance(phone, dict)
                        and phone.get("number")
                        and isinstance(phone.get("number"), str)
                    ]
                    if company_data.get("phones")
                    and isinstance(company_data.get("phones"), list)
                    else []
                ),
                # Проверка 7: Извлечение 'geoCoordinates' с вложенными полями
                "companyGeoCoordinates": (
                    {
                        "latitude": company_data.get("geoCoordinates", {}).get(
                            "latitude"
                        ),
                        "longtitude": company_data.get("geoCoordinates", {}).get(
                            "longtitude"
                        ),
                    }
                    if company_data.get("geoCoordinates")
                    and isinstance(company_data.get("geoCoordinates"), dict)
                    else None
                ),
            }

            all_data.append(result)
        except Exception as e:
            # Проверка 8: Перехват любых непредвиденных ошибок
            print(f"Ошибка при извлечении данных: {e}")
            return {}
    with open("result_id.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)


def scrap_json_products():
    all_data = []
    files = list(json_products_directory.glob("*.json"))
    # Пройтись по каждому HTML файлу в папке
    count = 0
    for json_file in files:
        with open(json_file, "r", encoding="utf-8") as file:
            input_data = json.load(file)
        import re

        companyid = None
        match = re.search(r"products_(\d+)", json_file.name)
        if match:
            companyid = match.group(1)
        result = {}
        try:
            # Проверка 1: Убедимся, что input_data — словарь
            if not isinstance(input_data, dict):
                logger.error("Ошибка: input_data не является словарем")
                return {}

            # Проверка 2: Безопасно извлекаем 'data' и 'company'
            data = input_data.get("data", {})
            if not isinstance(data, dict):
                logger.error(f"Ошибка: 'data' не является словарем {json_file}")
                continue

            listing_data = data.get("listing", {})
            if not isinstance(listing_data, dict):
                logger.error(f"Ошибка: 'listing' не является словарем {json_file}")
                return {}
            page = listing_data.get("page", {})
            if not isinstance(page, dict):
                logger.error(f"Ошибка: 'page' не является словарем {json_file}")
                return {}
            total_products = page.get("total", None)
            result["totalProducts"] = total_products
            result["companyId"] = companyid
            all_data.append(result)
            count += 1
            print(f"Обработано {count} файлов", end="\r")
        except Exception as e:
            # Проверка 8: Перехват любых непредвиденных ошибок
            logger.error(f"Ошибка при извлечении данных: {e}")
            return {}
    with open("result_products.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)


def scrap_json_review():
    all_data = []
    files = list(json_review_directory.glob("*.json"))

    # Группируем файлы по companyid
    company_files = defaultdict(list)

    for json_file in files:
        companyid = None
        match = re.search(r"company_review_(\d+)", json_file.name)
        if match:
            companyid = match.group(1)
            if companyid:
                company_files[companyid].append(json_file)
    # Обрабатываем каждую группу файлов
    results = {}
    for companyid, file_list in company_files.items():
        logger.info(f"Обработка {len(file_list)} файлов для компании {companyid}")
        # Передаем группу файлов в функцию scrap_review
        company_data = scrap_review(file_list, companyid)
        results[companyid] = company_data
        all_data.append(company_data)

    with open("result_review.json", "w", encoding="utf-8") as json_file:
        json.dump(all_data, json_file, ensure_ascii=False, indent=4)


def scrap_review(file_list, companyid):
    result = {
        "companyid": companyid,
        "review_2023": 0,
        "review_2024": 0,
        "review_2025": 0,
    }

    # Счетчик для отзывов по годам
    reviews_by_year = defaultdict(int)

    # Проходим по каждому файлу
    for json_file in file_list:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                input_data = json.load(f)

            # Проверка структуры JSON
            if not isinstance(input_data, dict):
                logger.error(
                    f"Ошибка: input_data не является словарем в файле {json_file}"
                )
                continue

            data = input_data.get("data", {})
            if not isinstance(data, dict):
                logger.error(f"Ошибка: 'data' не является словарем в файле {json_file}")
                continue

            opinion_listing = data.get("opinionListing", {})
            if not isinstance(opinion_listing, dict):
                logger.error(
                    f"Ошибка: 'opinionListing' не является словарем в файле {json_file}"
                )
                continue

            opinions = opinion_listing.get("opinions", [])
            if not isinstance(opinions, list):
                logger.error(
                    f"Ошибка: 'opinions' не является списком в файле {json_file}"
                )
                continue

            # Обрабатываем каждый отзыв
            for opinion in opinions:
                if not isinstance(opinion, dict):
                    continue

                # Получаем дату создания отзыва
                date_created = opinion.get("dateCreated", "")
                if not date_created:
                    continue

                try:
                    # Преобразуем строку даты в объект datetime
                    date_obj = datetime.fromisoformat(
                        date_created.replace("Z", "+00:00")
                    )
                    # Получаем год
                    year = date_obj.year
                    # Увеличиваем счетчик для соответствующего года
                    reviews_by_year[year] += 1
                except ValueError as e:
                    logger.error(f"Ошибка парсинга даты '{date_created}': {e}")
                    continue

        except Exception as e:
            logger.error(f"Ошибка обработки файла {json_file}: {e}")
            continue

    # Заполняем результат
    result["review_2023"] = reviews_by_year.get(2023, 0)
    result["review_2024"] = reviews_by_year.get(2024, 0)
    result["review_2025"] = reviews_by_year.get(2025, 0)

    return result


if __name__ == "__main__":
    # scrap_json_company()
    # scrap_json_products()
    scrap_json_review()
