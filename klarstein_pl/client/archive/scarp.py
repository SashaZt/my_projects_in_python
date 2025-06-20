import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from config.logger import logger


def extract_product_params(html_file_path: str, output_json_path: str = None) -> dict:
    """
    Извлекает параметры товара: размеры и вес в product_specifications

    Args:
        html_file_path: Путь к HTML файлу
        output_json_path: Путь для сохранения JSON (опционально)

    Returns:
        dict: Словарь с извлеченными параметрами
    """
    try:
        # Читаем HTML файл
        with open(html_file_path, "r", encoding="utf-8") as file:
            content = file.read()

        soup = BeautifulSoup(content, "lxml")

        # Инициализируем структуру данных
        product_params = {
            "product": {},
            "breadcrumbs_pl": [],
            "description_pl": [],
            "product_specifications": {},
        }

        # 1. Извлекаем JSON-LD данные
        script_tags = soup.find_all("script", attrs={"type": "application/ld+json"})

        breadcrumb_script = None
        product_script = None

        for script in script_tags:
            try:
                json_data = json.loads(script.string)

                if json_data.get("@type") == "BreadcrumbList" and not breadcrumb_script:
                    breadcrumb_script = json_data
                elif json_data.get("@type") == "Product" and not product_script:
                    product_script = json_data

                if breadcrumb_script and product_script:
                    break
            except (json.JSONDecodeError, TypeError):
                continue

        # 2. Заполняем основную информацию о продукте
        if product_script:
            name = product_script.get("name", "")
            sku = product_script.get("sku", "")
            price = product_script.get("offers", {}).get("price", "")
            images = product_script.get("image", [])

            product_params["product"] = {
                "name_pl": name,
                "sku": f"Kla{sku}" if sku else "",
                "price": price,
                "images": images,
            }

        # 3. Заполняем хлебные крошки
        if breadcrumb_script:
            itemListElement = breadcrumb_script.get("itemListElement", [])
            breadcrumbs = []
            for item in itemListElement[:-1]:  # Исключаем последний элемент
                if isinstance(item, dict):
                    breadcrumbs.append(item.get("name", ""))
            product_params["breadcrumbs_pl"] = breadcrumbs

        # 4. Извлекаем аккордеон-секции
        accordion_items = soup.find_all("div", class_="accordion__item")
        accordion_data = []

        for item in accordion_items[:-2]:  # Исключаем последние два
            title_div = item.find("div", class_="accordion__title")
            title = ""
            if title_div and title_div.find("h2"):
                title = title_div.find("h2").get_text(strip=True)

            content_div = item.find("div", class_="accordion__content")
            content = ""
            if content_div:
                content = "".join(
                    str(child).strip()
                    for child in content_div.children
                    if str(child).strip()
                )

            if title:
                accordion_data.append({"title_pl": title, "description_pl": content})

        product_params["description_pl"] = accordion_data

        # 5. Ищем секцию с размерами и извлекаем в product_specifications
        for section in accordion_data:
            title_lower = section["title_pl"].lower()
            content = section["description_pl"]

            # Ищем секцию с размерами
            if "wymiary" in title_lower or "techniczne" in title_lower:
                specifications = extract_dimensions_and_weight(content)
                product_params["product_specifications"] = specifications
                break  # Нашли нужную секцию, больше не ищем

        # 6. Сохраняем в JSON файл
        if not output_json_path:
            # Создаем имя файла на основе SKU
            sku_clean = (
                product_params["product"].get("sku", "").replace("Kla", "")
            )
            output_json_path = f"Kla{sku_clean}.json"

        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(product_params, f, ensure_ascii=False, indent=4)

        logger.info(f"Параметры извлечены и сохранены в {output_json_path}")

        # Проверяем что нашли
        specs = product_params["product_specifications"]
        if specs:
            found_params = []
            if specs.get("width"):
                found_params.append(f"ширина: {specs['width']}")
            if specs.get("height"):
                found_params.append(f"высота: {specs['height']}")
            if specs.get("length"):
                found_params.append(f"длина: {specs['length']}")
            if specs.get("weight"):
                found_params.append(f"вес: {specs['weight']}")

            if found_params:
                logger.info(f"Найдено: {', '.join(found_params)}")
            else:
                logger.info("Размеры и вес не найдены")
        else:
            logger.info("Секция с размерами не найдена")

        return product_params

    except Exception as e:
        logger.error(f"Ошибка извлечения параметров из {html_file_path}: {e}")
        return {}


def extract_dimensions_and_weight(content: str) -> dict:
    """
    Извлекает размеры и вес для product_specifications

    Returns:
        dict: {"width": "45.0 cm", "height": "45.5 cm", "length": "34.0 cm", "weight": "16.5 kg"}
        Значения как строки с единицами измерения для соответствия spec_value TEXT
    """
    result = {}

    # Убираем HTML теги для чистого текста
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text()

    # Паттерн для размеров: Wymiary: ok. 45 x 45,5 x 34 cm
    dimension_patterns = [
        r"Wymiary[:\s]*ok\.?\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*cm",
        r"Wymiary[:\s]*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*x\s*(\d+(?:,\d+)?)\s*cm",
    ]

    # Ищем размеры
    for pattern in dimension_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Сохраняем как строки с единицами измерения
            result["width"] = match.group(1).replace(",", ".") + " cm"
            result["height"] = match.group(2).replace(",", ".") + " cm"
            result["length"] = match.group(3).replace(",", ".") + " cm"
            break

    # Паттерн для веса: Waga: ok. 16,5 kg
    weight_patterns = [
        r"Waga[:\s]*ok\.?\s*(\d+(?:,\d+)?)\s*kg",
        r"Waga[:\s]*(\d+(?:,\d+)?)\s*kg",
    ]

    # Ищем вес
    for pattern in weight_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Сохраняем как строку с единицей измерения
            result["weight"] = match.group(1).replace(",", ".") + " kg"
            break

    return result


def batch_extract_params(html_files_pattern: str = "*.html") -> dict:
    """
    Пакетная обработка HTML файлов

    Args:
        html_files_pattern: Паттерн для поиска HTML файлов (например: "*.html" или "1003*.html")

    Returns:
        dict: Статистика обработки
    """
    current_dir = Path.cwd()
    html_files = list(current_dir.glob(html_files_pattern))

    if not html_files:
        logger.warning(f"HTML файлы по паттерну '{html_files_pattern}' не найдены")
        return {"total_files": 0, "processed": 0, "errors": 0}

    stats = {"total_files": len(html_files), "processed": 0, "errors": 0, "results": []}

    logger.info(f"Найдено {len(html_files)} HTML файлов для обработки")

    for html_file in html_files:
        try:
            # Создаем имя JSON файла на основе HTML файла
            json_filename = f"Kla{html_file.stem}.json"

            result = extract_product_params(str(html_file), json_filename)

            if result:
                stats["processed"] += 1

                # Ищем извлеченные характеристики для статистики
                specifications_found = bool(result.get("product_specifications"))

                stats["results"].append(
                    {
                        "html_file": str(html_file),
                        "json_file": json_filename,
                        "sku": result.get("product", {}).get("sku", ""),
                        "name": result.get("product", {}).get("name_pl", "")[:50]
                        + "...",
                        "specifications_found": specifications_found,
                    }
                )
            else:
                stats["errors"] += 1

        except Exception as e:
            logger.error(f"Ошибка обработки {html_file}: {e}")
            stats["errors"] += 1

    # Сохраняем сводную статистику
    with open("extraction_stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=4)

    logger.info(f"ИТОГО: {stats['processed']}/{stats['total_files']} файлов обработано")
    logger.info(f"Ошибок: {stats['errors']}")

    # Показываем сколько товаров с найденными размерами
    with_dimensions = sum(
        1 for r in stats["results"] if r.get("dimensions_found", False)
    )
    logger.info(f"Товаров с найденными размерами: {with_dimensions}")

    return stats


# Пример использования
if __name__ == "__main__":
    # Обработка одного файла
    result = extract_product_params("10035233.html")
    print("Извлечение завершено!")
