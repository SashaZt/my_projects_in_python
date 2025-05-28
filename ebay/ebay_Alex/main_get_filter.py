"""
РУКОВОДСТВО ПО ИСПОЛЬЗОВАНИЮ ИЗВЛЕКАТЕЛЯ ФИЛЬТРОВ EBAY

Этот код показывает, как извлечь все фильтры: Brand, Condition, Type, Price и т.д.
"""

import json

import requests
from bs4 import BeautifulSoup
from universal_filter_extractor import (
    extract_all_filters,
    extract_condition_codes,
    extract_filter_options,
    save_filter_data,
)


def extract_all_ebay_filters():
    """
    Загружает страницу eBay и извлекает ВСЕ доступные фильтры
    """
    url = "https://www.ebay.com/b/Car-Truck-ECUs-Computer-Modules/33596/bn_584314"
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    try:
        print("📥 Загружаем страницу eBay...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        print(f"✅ Страница загружена ({len(response.text)} символов)")

        # Сохраняем HTML для анализа
        with open("ebay_filters_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("💾 HTML сохранен в: ebay_filters_page.html")

        # Извлекаем ВСЕ фильтры автоматически
        print("\n🔍 Извлекаем все доступные фильтры...")
        all_filters = extract_all_filters(response.text)

        print(f"\n📊 Найдено {len(all_filters)} фильтров:")
        for filter_name, options in all_filters.items():
            print(f"  • {filter_name}: {len(options)} опций")

        return all_filters, response.text

    except Exception as e:
        print(f"❌ Ошибка при загрузке: {str(e)}")
        return {}, ""


def extract_specific_filters(html_content, filter_names):
    """
    Извлекает только указанные фильтры

    Args:
        html_content (str): HTML содержимое страницы
        filter_names (list): Список названий фильтров для извлечения

    Returns:
        dict: Словарь с извлеченными фильтрами
    """
    filters = {}

    print(f"\n🎯 Извлекаем конкретные фильтры: {filter_names}")

    for filter_name in filter_names:
        print(f"\n--- Фильтр: {filter_name} ---")
        options = extract_filter_options(html_content, filter_name)

        if options:
            filters[filter_name] = options
            print(f"✅ Найдено {len(options)} опций")

            # Показываем первые 3 опции для примера
            for i, (option, value) in enumerate(options.items()):
                if i < 3:
                    print(f"   {option}: {value[:80]}...")
                elif i == 3:
                    print(f"   ... и еще {len(options) - 3} опций")
                    break
        else:
            print(f"❌ Фильтр '{filter_name}' не найден")

    return filters


def extract_condition_mapping(html_content):
    """
    Специальное извлечение кодов состояний для скрапера
    """
    print("\n🏷️ Извлекаем коды состояний товаров...")

    condition_codes = extract_condition_codes(html_content)

    if condition_codes:
        print(f"✅ Найдено {len(condition_codes)} состояний:")
        for condition, code in condition_codes.items():
            print(f"   {condition}: {code}")

        # Создаем удобный маппинг для скрапера
        scraper_conditions = {
            "new": "1000",
            "used": "3000",
            "remanufactured": "2500",
            "parts": "7000",
        }

        print(f"\n📋 Рекомендуемые коды для скрапера:")
        for key, code in scraper_conditions.items():
            # Ищем соответствующее название в извлеченных данных
            condition_name = next(
                (name for name, c in condition_codes.items() if c == code), "Unknown"
            )
            print(f"   '{key}': '{code}',  # {condition_name}")

        return condition_codes
    else:
        print("❌ Состояния не найдены")
        return {}


def demonstrate_usage():
    """
    Демонстрирует различные способы использования
    """
    print("=" * 60)
    print("🚀 ДЕМОНСТРАЦИЯ ИЗВЛЕЧЕНИЯ ФИЛЬТРОВ EBAY")
    print("=" * 60)

    # Способ 1: Извлечение всех фильтров автоматически
    print("\n1️⃣ АВТОМАТИЧЕСКОЕ ИЗВЛЕЧЕНИЕ ВСЕХ ФИЛЬТРОВ")
    all_filters, html_content = extract_all_ebay_filters()

    if html_content:
        # Способ 2: Извлечение конкретных фильтров
        print("\n2️⃣ ИЗВЛЕЧЕНИЕ КОНКРЕТНЫХ ФИЛЬТРОВ")
        target_filters = ["Brand", "Condition", "Type", "Price"]
        specific_filters = extract_specific_filters(html_content, target_filters)

        # Способ 3: Специальное извлечение состояний
        print("\n3️⃣ СПЕЦИАЛЬНОЕ ИЗВЛЕЧЕНИЕ СОСТОЯНИЙ")
        condition_codes = extract_condition_mapping(html_content)

        # Объединяем все результаты
        final_data = {
            "all_filters": all_filters,
            "specific_filters": specific_filters,
            "condition_codes": condition_codes,
        }

        # Сохраняем результаты
        print("\n💾 СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
        save_filter_data(all_filters, "all_ebay_filters.json")
        save_filter_data(specific_filters, "specific_filters.json")

        # Создаем файл для скрапера
        create_scraper_config(specific_filters, condition_codes)

        return final_data

    return {}


def create_scraper_config(filters, condition_codes):
    """
    Создает конфигурационный файл для скрапера
    """
    print("\n⚙️ Создаем конфигурацию для скрапера...")

    config = {
        "base_url": "https://www.ebay.com/b/Car-Truck-ECUs-Computer-Modules/33596/bn_584314",
        "filters": {},
    }

    # Добавляем бренды
    if "Brand" in filters:
        brands = {}
        for brand_name, brand_url in filters["Brand"].items():
            # Извлекаем базовый URL без параметров
            base_url = brand_url.split("?")[0] if "?" in brand_url else brand_url
            brands[brand_name] = base_url
        config["filters"]["brands"] = brands

    # Добавляем состояния
    if condition_codes:
        config["filters"]["conditions"] = condition_codes

    # Добавляем типы (если есть)
    if "Type" in filters:
        config["filters"]["types"] = filters["Type"]

    # Добавляем ценовые диапазоны
    config["filters"]["price_ranges"] = [
        {"name": "low", "params": {"_udhi": "75"}},
        {"name": "medium", "params": {"_udlo": "75", "_udhi": "150"}},
        {"name": "high", "params": {"_udlo": "150"}},
    ]

    # Сохраняем конфигурацию
    with open("scraper_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

    # Создаем Python файл с конфигурацией
    with open("scraper_config.py", "w", encoding="utf-8") as f:
        f.write("# Конфигурация для скрапера eBay\n\n")
        f.write(f"BASE_URL = \"{config['base_url']}\"\n\n")

        if "brands" in config["filters"]:
            f.write("BRAND_URLS = {\n")
            for brand, url in sorted(config["filters"]["brands"].items()):
                f.write(f'    "{brand}": "{url}",\n')
            f.write("}\n\n")

        if "conditions" in config["filters"]:
            f.write("CONDITION_CODES = {\n")
            for condition, code in sorted(config["filters"]["conditions"].items()):
                f.write(f'    "{condition}": "{code}",\n')
            f.write("}\n\n")

        f.write("PRICE_RANGES = [\n")
        for price_range in config["filters"]["price_ranges"]:
            f.write(f"    {price_range},\n")
        f.write("]\n")

    print("✅ Конфигурация сохранена:")
    print("   📄 scraper_config.json")
    print("   🐍 scraper_config.py")


def quick_extract_example():
    """
    Быстрый пример извлечения конкретного фильтра
    """
    print("\n" + "=" * 40)
    print("⚡ БЫСТРЫЙ ПРИМЕР")
    print("=" * 40)

    # Если у вас уже есть сохраненный HTML файл
    try:
        with open("ebay_filters_page.html", "r", encoding="utf-8") as f:
            html_content = f.read()

        print("📂 Используем сохраненный HTML файл")

        # Извлекаем только бренды
        brands = extract_filter_options(html_content, "Brand")
        print(f"🏷️ Найдено брендов: {len(brands)}")

        # Извлекаем только состояния
        conditions = extract_filter_options(html_content, "Condition")
        print(f"📋 Найдено состояний: {len(conditions)}")

        return {"brands": brands, "conditions": conditions}

    except FileNotFoundError:
        print("❌ HTML файл не найден. Запустите сначала demonstrate_usage()")
        return {}


# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
if __name__ == "__main__":
    print("🎉 РУКОВОДСТВО ПО ИСПОЛЬЗОВАНИЮ ИЗВЛЕКАТЕЛЯ ФИЛЬТРОВ")
    print("\nВыберите способ:")
    print("1. demonstrate_usage() - Полная демонстрация")
    print("2. quick_extract_example() - Быстрый пример")

    # Запускаем полную демонстрацию
    result = demonstrate_usage()

    print("\n" + "=" * 60)
    print("✅ ГОТОВО! Все фильтры извлечены и сохранены")
    print("📁 Проверьте созданные файлы:")
    print("   • all_ebay_filters.json - все фильтры")
    print("   • specific_filters.json - конкретные фильтры")
    print("   • scraper_config.json - конфигурация для скрапера")
    print("   • scraper_config.py - Python конфигурация")
    print("=" * 60)
