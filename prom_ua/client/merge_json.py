import json
import os

from config.logger import logger


def merge_json_files(companies_file, products_file, reviews_file, output_file):
    """
    Объединяет данные из трех JSON-файлов в один.

    Args:
        companies_file (str): Путь к файлу с данными компаний.
        products_file (str): Путь к файлу с данными о продуктах.
        reviews_file (str): Путь к файлу с данными об отзывах.
        output_file (str): Путь к выходному файлу.
    """
    try:
        # Загружаем данные о компаниях
        with open(companies_file, "r", encoding="utf-8") as f:
            companies_data = json.load(f)

        # Загружаем данные о количестве товаров
        with open(products_file, "r", encoding="utf-8") as f:
            products_data = json.load(f)

        # Загружаем данные об отзывах
        with open(reviews_file, "r", encoding="utf-8") as f:
            reviews_data = json.load(f)

        # Создаем словарь для быстрого поиска данных о количестве товаров по ID компании
        products_dict = {
            item["companyId"]: item["totalProducts"] for item in products_data
        }

        # Создаем словарь для быстрого поиска данных об отзывах по ID компании
        reviews_dict = {}
        for review in reviews_data:
            company_id = review["companyid"]
            reviews_dict[company_id] = {
                "rating_company": review.get("rating_company", None),
                "review_2023": review.get("review_2023", 0),
                "review_2024": review.get("review_2024", 0),
                "review_2025": review.get("review_2025", 0),
            }

        # Объединяем данные
        for company in companies_data:
            company_id = str(company["companyId"])

            # Добавляем информацию о количестве товаров, если она есть
            if company_id in products_dict:
                company["totalProducts"] = products_dict[company_id]
            else:
                company["totalProducts"] = 0  # По умолчанию 0, если информации нет

            # Добавляем информацию об отзывах, если она есть
            if company_id in reviews_dict:
                review_info = reviews_dict[company_id]
                company["rating_company"] = review_info["rating_company"]
                company["review_2023"] = review_info["review_2023"]
                company["review_2024"] = review_info["review_2024"]
                company["review_2025"] = review_info["review_2025"]
            else:
                # По умолчанию, если данных об отзывах нет
                company["rating_company"] = None
                company["review_2023"] = 0
                company["review_2024"] = 0
                company["review_2025"] = 0

        # Сохраняем результат в новый файл
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(companies_data, f, ensure_ascii=False, indent=4)

        logger.info(f"Данные успешно объединены и сохранены в {output_file}")
        logger.info(
            f"Обработано {len(companies_data)} компаний, {len(products_data)} записей о товарах "
            f"и {len(reviews_data)} записей об отзывах"
        )

        return True

    except Exception as e:
        logger.error(f"Ошибка при объединении данных: {str(e)}")
        return False


def main():
    """Основная функция"""
    # Пути к файлам
    companies_file = "result.json"
    products_file = "result_products.json"
    reviews_file = "result_review.json"
    output_file = "merged_data.json"

    # Объединяем данные
    if merge_json_files(companies_file, products_file, reviews_file, output_file):
        logger.info("Операция успешно завершена")
    else:
        logger.error("Операция завершена с ошибками")


if __name__ == "__main__":
    main()
