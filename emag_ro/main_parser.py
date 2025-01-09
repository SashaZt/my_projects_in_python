import json
import re

import pandas as pd
from bs4 import BeautifulSoup
from configuration.logger_setup import logger


def write_json():
    # Загрузка содержимого HTML файла
    with open("pd_D603G9MBM.html", "r", encoding="utf-8") as file:
        content = file.read()

    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(content, "lxml")

    # Ищем теги <script> с type="text/javascript"
    script_tags = soup.find_all("script", {"type": "text/javascript"})

    # Перебираем найденные теги
    for script in script_tags:
        script_content = script.string

        if script_content and "dataLayer.push" in script_content:
            # Извлекаем содержимое вызова dataLayer.push({...})
            json_match = re.search(
                r"dataLayer\.push\((\{.*?\})\);", script_content, re.DOTALL
            )

            if json_match:
                json_data = json_match.group(1)

                try:
                    # Исправляем одинарные кавычки и ключи
                    cleaned_data = re.sub(
                        r"'", '"', json_data
                    )  # Одинарные кавычки -> двойные
                    cleaned_data = re.sub(
                        r",\s*([\}\]])", r"\1", cleaned_data
                    )  # Убираем запятые перед закрывающими скобками
                    cleaned_data = re.sub(
                        r"(?<!\")([a-zA-Z_]+)(?=\s*:)", r'"\1"', cleaned_data
                    )  # Ключи без кавычек

                    # Парсим JSON
                    data = json.loads(cleaned_data)

                    print("Извлеченный JSON:")
                    print(json.dumps(data, indent=4, ensure_ascii=False))
                    with open("output.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)

                except json.JSONDecodeError as e:
                    print(f"Ошибка при парсинге JSON: {e}")
                    print("Содержимое вызова dataLayer.push:")
                    print(cleaned_data)


def write_js():
    # Загрузка содержимого HTML файла
    with open("Masina.html", "r", encoding="utf-8") as file:
        content = file.read()

    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(content, "lxml")
    # Поиск тега <script>, содержащего "var dataLayer=dataLayer||[];"
    script_tag = soup.find(
        "script", string=lambda text: text and "var dataLayer=dataLayer||[]" in text
    )

    # Проверяем, найден ли тег <script>
    if script_tag:
        # Сохраняем содержимое тега в файл
        with open("dataLayer_script_content.js", "w", encoding="utf-8") as output_file:
            output_file.write(script_tag.string)
        print("Содержимое тега сохранено в файл 'dataLayer_script_content.js'.")
    else:
        print("Тег <script> с 'var dataLayer=dataLayer||[];' не найден.")


def clean_general(raw_value):
    """
    Общая функция для очистки данных большинства ключей.
    """
    try:
        # Одинарные кавычки -> двойные
        cleaned_value = re.sub(r"'", '"', raw_value)
        # Удаление комментариев
        cleaned_value = re.sub(r"//.*?\n", "", cleaned_value)
        # Замена функций на заглушки
        cleaned_value = re.sub(
            r"\b(function|new)\b.*?\{.*?\}",
            '"placeholder_function"',
            cleaned_value,
            flags=re.DOTALL,
        )
        # Удаление методов, таких как getById
        cleaned_value = re.sub(
            r"\bgetById\s*:\s*function\(.*?\}\,", "", cleaned_value, flags=re.DOTALL
        )
        # Удаление запятых перед закрывающими скобками
        cleaned_value = re.sub(r",\s*([}\]])", r"\1", cleaned_value)
        return cleaned_value
    except Exception as e:
        logger.error(f"Ошибка в общей очистке: {e}")
        return raw_value


def clean_feedback(raw_value):
    """
    Специальная функция для очистки EM.feedback.
    """
    try:
        # Оборачивание ключей в кавычки
        cleaned_value = re.sub(
            r"(?<!\w)([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*:)", r'"\1"', raw_value
        )
        # Удаление комментариев
        cleaned_value = re.sub(r"//.*?\n", "", cleaned_value)
        # Удаление запятых перед закрывающими скобками
        cleaned_value = re.sub(r",\s*([}\]])", r"\1", cleaned_value)
        return cleaned_value
    except Exception as e:
        logger.error(f"Ошибка в очистке EM.feedback: {e}")
        return raw_value


def clean_product(raw_value):
    """
    Специальная функция для очистки EM.product.
    """
    try:
        # Оборачивание ключей в кавычки
        cleaned_value = re.sub(
            r"(?<!\w)([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*:)", r'"\1"', raw_value
        )
        # Удаление комментариев
        cleaned_value = re.sub(r"//.*?\n", "", cleaned_value)
        # Удаление запятых перед закрывающими скобками
        cleaned_value = re.sub(r",\s*([}\]])", r"\1", cleaned_value)
        return cleaned_value
    except Exception as e:
        logger.error(f"Ошибка в очистке EM.product: {e}")
        return raw_value


def read_js():
    # Чтение содержимого файла
    # with open("dataLayer_script_content.js", "r", encoding="utf-8") as file:
    #     content = file.read()
    # Загрузка содержимого HTML файла
    with open("Masina.html", "r", encoding="utf-8") as file:
        content = file.read()

    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(content, "lxml")
    # Поиск тега <script>, содержащего "var dataLayer=dataLayer||[];"
    script_tag = soup.find(
        "script", string=lambda text: text and "var dataLayer=dataLayer||[]" in text
    )

    # Проверяем, найден ли тег <script>
    if script_tag:
        # Регулярное выражение для поиска объектов вида EM.key = value;
        pattern = re.compile(r"(EM\.[a-zA-Z0-9_]+)\s*=\s*(\{.*?\});", re.DOTALL)

        # Словарь для хранения извлеченных данных
        extracted_data = {}
        excluded_keys = {
            "EM.brand",
            "EM.used_offer",
            "EM.abTestsAuto",
            "EM.flags",
            "EM.GLOBAL_OPTIONS",
            "EM.google_recaptcha_keys",
            "EM.product",
            "EM.general_product_safety_regulation",
            "EM.cookie_group_policy",
            "EM.siteModules",
        }

        # Проходим по всем совпадениям
        for match in pattern.finditer(content):
            key = match.group(1)  # Название ключа, например EM.page_type
            raw_value = match.group(2)  # Содержимое объекта

            # Исключаем обработку определенных ключей
            if key in excluded_keys:
                continue

            try:
                # Специальная обработка для EM.feedback
                if key == "EM.feedback":
                    cleaned_value = clean_feedback(raw_value)
                elif key == "EM.product":
                    cleaned_value = clean_product(raw_value)
                else:
                    cleaned_value = clean_general(raw_value)

                # Преобразуем строку в валидный JSON
                value = json.loads(cleaned_value)
                extracted_data[key] = value
            except json.JSONDecodeError:
                logger.error(f"Не удалось распарсить значение для ключа: {key}")
                logger.error(f"Сырые данные: {raw_value}")
                logger.error(f"Очищенные данные: {cleaned_value}")

        # Сохраняем данные в файл JSON
        with open("extracted_data.json", "w", encoding="utf-8") as output_file:
            json.dump(extracted_data, output_file, indent=4, ensure_ascii=False)

        logger.info("Данные извлечены и сохранены в 'extracted_data.json'.")


def clean_json(raw_value):
    """
    Преобразует текстовую строку с объектом в формат JSON.
    """
    try:
        # Оборачивание ключей в кавычки
        cleaned = re.sub(r"(?<!\w)([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*:)", r'"\1"', raw_value)

        # Удаление комментариев (если есть)
        cleaned = re.sub(r"//.*?\n", "", cleaned)

        # Удаление лишних запятых перед закрывающими скобками
        cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)

        return cleaned
    except Exception as e:
        print(f"Ошибка обработки JSON: {e}")
        return raw_value


def extract_feedback_from_file(file_path, object_name="EM.feedback"):
    """
    Извлечение и обработка объекта из файла.
    """
    try:
        # Чтение содержимого файла
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Поиск объекта по имени
        pattern = re.compile(rf"{object_name}\s*=\s*(\{{.*?\}});", re.DOTALL)
        match = pattern.search(content)

        if match:
            raw_value = match.group(1)  # Извлекаем содержимое объекта

            # Очистка данных
            cleaned_value = clean_json(raw_value)

            try:
                # Преобразование в JSON
                feedback_data = json.loads(cleaned_value)
                print("Обработанные данные:")
                print(json.dumps(feedback_data, indent=4, ensure_ascii=False))
            except json.JSONDecodeError as e:
                print("Ошибка при преобразовании в JSON:")
                print(f"Очищенные данные: {cleaned_value}")
                print(f"Ошибка: {e}")
        else:
            print(f"Объект {object_name} не найден.")
    except FileNotFoundError:
        print(f"Файл {file_path} не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def extract_json_product(soup):
    # Находим все теги <script> с типом application/ld+json
    script_tags = soup.find_all("script", {"type": "application/ld+json"})
    for script in script_tags:
        try:
            # Преобразуем содержимое тега <script> в Python-объект
            data = json.loads(script.string)
            # Проверяем наличие ключа @type и его значение
            if data.get("@type") == "Product":
                return data
        except json.JSONDecodeError:
            continue
    return None


def extract_json_breadcrumblist(soup):
    # Находим все теги <script> с типом application/ld+json
    script_tags = soup.find_all("script", {"type": "application/ld+json"})
    for script in script_tags:
        try:
            # Преобразуем содержимое тега <script> в Python-объект
            data = json.loads(script.string)
            # Проверяем наличие ключа @type и его значение
            if data.get("@type") == "BreadcrumbList":
                return data
        except json.JSONDecodeError:
            continue
    return None


def extract_description_texts(soup):
    """
    Извлекает теги (h1, h2, p, b) внутри div с data-box-name="Description".

    :param soup: Объект BeautifulSoup для HTML-страницы
    :return: Список тегов (элементов BeautifulSoup)
    """
    # Находим div с атрибутом data-box-name="Description"
    description_div = soup.find("div", {"id": "description-body"})

    if not description_div:
        return ""  # Возвращаем пустую строку, если div не найден

    # Извлекаем текстовые теги внутри найденного div
    tags = description_div.find_all(["h1", "h2", "p", "b", "ul", "li", "img"])

    # Преобразуем все теги в строки и объединяем их через join
    return "".join(str(tag) for tag in tags)


def extract_img_texts(soup):
    """
    Извлекает теги (h1, h2, p, b) внутри div с data-box-name="Description".

    :param soup: Объект BeautifulSoup для HTML-страницы
    :return: Список тегов (элементов BeautifulSoup)
    """
    # Находим div с атрибутом data-box-name="Description"
    description_div = soup.find("div", {"id": "product-gallery"})

    if not description_div:
        return ""  # Возвращаем пустую строку, если div не найден

    # Извлекаем текстовые теги внутри найденного div
    tags = description_div.find_all(["h1", "h2", "p", "b", "ul", "li", "img"])

    # Преобразуем все теги в строки и объединяем их через join
    return "".join(str(tag) for tag in tags)


def get_reviews_count(soup):

    # Находим контейнеры с рейтингами 5* и 1*
    rating_5 = soup.select_one(".rating-5-stars a:last-child")
    rating_1 = soup.select_one(".rating-1-stars a:last-child")

    # Извлекаем количество отзывов
    count_5 = int(rating_5.text.strip("()")) if rating_5 else 0
    count_1 = int(rating_1.text.strip("()")) if rating_1 else 0

    return count_5, count_1


def process_html():
    html_file = "Polizor.html"
    # Чтение содержимого файла
    with open(html_file, "r", encoding="utf-8") as file:
        content = file.read()

    # Создаем объект BeautifulSoup
    soup = BeautifulSoup(content, "lxml")

    # Парсим dataLayer.push({...})
    output_data = {}
    script_tags = soup.find_all("script", {"type": "text/javascript"})
    for script in script_tags:
        script_content = script.string
        if script_content and "dataLayer.push" in script_content:
            json_match = re.search(
                r"dataLayer\.push\((\{.*?\})\);", script_content, re.DOTALL
            )
            if json_match:
                json_data = json_match.group(1)
                try:
                    cleaned_data = re.sub(r"'", '"', json_data)
                    cleaned_data = re.sub(r",\s*([\}\]])", r"\1", cleaned_data)
                    cleaned_data = re.sub(
                        r"(?<!\")([a-zA-Z_]+)(?=\s*:)", r'"\1"', cleaned_data
                    )
                    output_data = json.loads(cleaned_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Ошибка при парсинге JSON: {e}")
                    logger.error(f"Содержимое вызова dataLayer.push: {cleaned_data}")

    # Парсим объекты вида EM.key = value
    script_tag = soup.find(
        "script", string=lambda text: text and "var dataLayer=dataLayer||[]" in text
    )
    extracted_data = {}
    excluded_keys = {
        "EM.brand",
        "EM.used_offer",
        "EM.abTestsAuto",
        "EM.flags",
        "EM.GLOBAL_OPTIONS",
        "EM.google_recaptcha_keys",
        "EM.product",
        "EM.general_product_safety_regulation",
        "EM.cookie_group_policy",
        "EM.siteModules",
    }
    if script_tag:
        pattern = re.compile(r"(EM\.[a-zA-Z0-9_]+)\s*=\s*(\{.*?\});", re.DOTALL)
        for match in pattern.finditer(content):
            key = match.group(1)
            raw_value = match.group(2)
            if key in excluded_keys:
                continue
            try:
                # Специальная обработка для EM.feedback
                if key == "EM.feedback":
                    cleaned_value = clean_feedback(raw_value)
                elif key == "EM.product":
                    cleaned_value = clean_product(raw_value)
                else:
                    cleaned_value = clean_general(raw_value)

                # Преобразуем строку в валидный JSON
                value = json.loads(cleaned_value)
                extracted_data[key] = value
            except json.JSONDecodeError:
                pass
                # logger.error(f"Не удалось распарсить значение для ключа: {key}")

    # Объединяем данные
    if "EM.feedback" in extracted_data:
        rating = extracted_data["EM.feedback"].get("rating", None)
        url = f'https://www.emag.ro{extracted_data.get("EM.url", {}).get("path", "")}'
        if "ecommerce" in output_data and "detail" in output_data["ecommerce"]:
            if "products" in output_data["ecommerce"]["detail"]:
                output_data["ecommerce"]["detail"]["products"][0]["rating"] = rating
                output_data["ecommerce"]["detail"]["products"][0]["url"] = url
    # Ключи, которые нужно удалить
    keys_to_remove = ["pageType_google", "pageType", "depId", "sdId", "event", "dish"]
    specifications_dict = extract_specifications(soup)

    # Удаление ключей
    output_data = remove_keys(output_data, keys_to_remove)

    # Удаление вложенных ключей
    if "ecommerce" in output_data and "detail" in output_data["ecommerce"]:
        if "actionField" in output_data["ecommerce"]["detail"]:
            del output_data["ecommerce"]["detail"]["actionField"]

    # Добавляем specifications_dict в output_data
    output_data = add_specifications_to_json(output_data, specifications_dict)
    img_title_tag = soup.find("meta", {"property": "og:image"})
    if img_title_tag:
        img_title = img_title_tag.get("content") if img_title_tag else None
    output_data["ecommerce"]["detail"]["products"][0]["img_title"] = img_title
    product_json = extract_json_product(soup)
    product_sku = product_json["sku"]
    output_data["ecommerce"]["detail"]["products"][0]["sku"] = product_sku
    breadcrumblist_json = extract_json_breadcrumblist(soup)
    item_list = breadcrumblist_json.get("itemListElement", [])
    if len(item_list) >= 2:  # Проверяем, есть ли хотя бы два элемента
        penultimate_item = item_list[-2]  # Предпоследний элемент
        penultimate_id = penultimate_item.get("item", {}).get("@id", None)
        penultimate_name = penultimate_item.get("item", {}).get("name", None)
    output_data["ecommerce"]["detail"]["products"][0]["url_category"] = penultimate_id
    output_data["ecommerce"]["detail"]["products"][0][
        "name_category"
    ] = penultimate_name

    description = extract_description_texts(soup)
    output_data["ecommerce"]["detail"]["products"][0]["description"] = description
    img_raw = extract_img_texts(soup)
    output_data["ecommerce"]["detail"]["products"][0]["img"] = img_raw

    secondary_offers_count = len(output_data.get("secondary_offers", []))
    output_data["secondary_offers_count"] = secondary_offers_count
    count_5, count_1 = get_reviews_count(soup)
    output_data["ecommerce"]["detail"]["products"][0]["positive_reviews"] = count_5
    output_data["ecommerce"]["detail"]["products"][0]["negative_reviews"] = count_1

    # Сохраняем оба JSON файла
    with open("output.json", "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=4, ensure_ascii=False)

    flattened_data = flatten_json(output_data)

    # Конвертируем в DataFrame и сохраняем в Excel
    df = pd.DataFrame([flattened_data])
    df.to_excel("output_flattened.xlsx", index=False, engine="openpyxl")

    with open("extracted_data.json", "w", encoding="utf-8") as extracted_file:
        json.dump(extracted_data, extracted_file, indent=4, ensure_ascii=False)

    logger.info(
        "Данные успешно обработаны и сохранены в 'output.json' и 'extracted_data.json'."
    )

    # Преобразование JSON в плоскую структуру для Excel


def flatten_json(json_data, parent_key="", sep="_"):
    """Flatten nested JSON recursively."""
    items = []
    for k, v in json_data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_json(item, f"{new_key}_{i}", sep=sep).items())
                else:
                    items.append((f"{new_key}_{i}", item))
        else:
            items.append((new_key, v))
    return dict(items)


def add_specifications_to_json(data, specifications_dict):
    """
    Добавляет specifications_dict в 'ecommerce.detail.products' секции JSON.
    :param data: JSON-структура
    :param specifications_dict: Словарь спецификаций
    """
    if "ecommerce" in data and "detail" in data["ecommerce"]:
        products = data["ecommerce"]["detail"].get("products", [])
        if products and isinstance(
            products, list
        ):  # Проверяем, что products — это список
            for product in products:
                product["specifications"] = (
                    specifications_dict  # Добавляем спецификации
                )
    return data


def extract_specifications(soup):
    """
    Извлекает характеристики из блока с ID 'specifications-body'.

    :param html_content: HTML контент как строка
    :return: Словарь характеристик
    """

    specifications = {}

    # Находим div с ID 'specifications-body'
    specifications_body = soup.find("div", {"id": "specifications-body"})
    if not specifications_body:
        return specifications  # Возвращаем пустой словарь, если элемент не найден

    # Находим все таблицы внутри блока
    tables = specifications_body.find_all("table", class_="specifications-table")

    # Проходим по каждой таблице
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            # Извлекаем ключ (первый столбец) и значение (второй столбец)
            key_cell = row.find("td", class_="col-xs-4 text-muted")
            value_cell = row.find("td", class_="col-xs-8")
            if key_cell and value_cell:
                key = key_cell.get_text(strip=True)
                value = value_cell.get_text(strip=True).replace(
                    "\n", " "
                )  # Убираем переносы строк
                specifications[key] = value

    return specifications


def remove_keys(data, keys_to_remove):
    """
    Удаляет указанные ключи из JSON-структуры.

    :param data: JSON-структура (словарь или вложенный словарь)
    :param keys_to_remove: Список ключей для удаления
    :return: Обновленный JSON-объект без указанных ключей
    """
    if isinstance(data, dict):
        return {
            k: remove_keys(v, keys_to_remove)
            for k, v in data.items()
            if k not in keys_to_remove
        }
    elif isinstance(data, list):
        return [remove_keys(item, keys_to_remove) for item in data]
    return data


# def flatten_json(json_data, parent_key="", sep="_"):
#     """Flatten nested JSON recursively."""
#     items = []
#     for k, v in json_data.items():
#         new_key = f"{parent_key}{sep}{k}" if parent_key else k
#         if isinstance(v, dict):
#             items.extend(flatten_json(v, new_key, sep=sep).items())
#         elif isinstance(v, list):
#             for i, item in enumerate(v):
#                 if isinstance(item, dict):
#                     items.extend(flatten_json(item, f"{new_key}_{i}", sep=sep).items())
#                 else:
#                     items.append((f"{new_key}_{i}", item))
#         else:
#             items.append((new_key, v))
#     return dict(items)


if __name__ == "__main__":
    # Использование
    process_html()
    # write_json()
    # write_js()
    # read_js()
    # # Вызов функции
    # extract_feedback_from_file(
    #     "dataLayer_script_content.js", object_name="EM.productDiscountedPrice"
    # )
