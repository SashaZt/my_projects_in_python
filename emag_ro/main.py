import json
import re

from bs4 import BeautifulSoup
from configuration.logger_setup import logger


def write_json():
    # Загрузка содержимого HTML файла
    with open("Masina.html", "r", encoding="utf-8") as file:
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


# РАБОЧИЙ
# def read_js():
#     # Чтение содержимого файла
#     with open("dataLayer_script_content.js", "r", encoding="utf-8") as file:
#         content = file.read()

#     # Регулярное выражение для поиска объектов вида EM.key = value;
#     pattern = re.compile(r"(EM\.[a-zA-Z0-9_]+)\s*=\s*(\{.*?\});", re.DOTALL)

#     # Словарь для хранения извлеченных данных
#     extracted_data = {}
#     excluded_keys = {
#         "EM.abTestsAuto",
#         "EM.flags",
#         "EM.GLOBAL_OPTIONS",
#         "EM.google_recaptcha_keys",
#     }

#     # Проходим по всем совпадениям
#     for match in pattern.finditer(content):
#         key = match.group(1)  # Название ключа, например EM.page_type
#         raw_value = match.group(2)  # Содержимое объекта

#         # Исключаем обработку определенных ключей
#         if key in excluded_keys:

#             # logger.info(f"Ключ {key} исключен из обработки.")
#             continue

#         try:
#             # Очистка данных для JSON
#             cleaned_value = re.sub(r"'", '"', raw_value)  # Одинарные кавычки -> двойные
#             cleaned_value = re.sub(
#                 r"//.*?\n", "", cleaned_value
#             )  # Удаление комментариев
#             cleaned_value = re.sub(
#                 r"\b(function|new)\b.*?\{.*?\}", '"placeholder_function"', cleaned_value
#             )  # Замена функций на заглушки
#             cleaned_value = re.sub(
#                 r"\bgetById\s*:\s*function\(.*?\}\,", "", cleaned_value, flags=re.DOTALL
#             )  # Удаление методов getById

#             # Преобразуем строку в валидный JSON
#             value = json.loads(cleaned_value)
#             extracted_data[key] = value
#         except json.JSONDecodeError:
#             logger.error(f"Не удалось распарсить значение для ключа: {key}")
#             logger.error(f"Сырые данные: {raw_value}")
#             logger.error(f"Очищенные данные: {cleaned_value}")

#     # Сохраняем данные в файл JSON
#     with open("extracted_data.json", "w", encoding="utf-8") as output_file:
#         json.dump(extracted_data, output_file, indent=4, ensure_ascii=False)


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
    with open("dataLayer_script_content.js", "r", encoding="utf-8") as file:
        content = file.read()

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


#     logger.info("Данные извлечены и сохранены в 'extracted_data.json'.")
# def clean_json(raw_value):
#     """
#     Очистка данных, чтобы они стали валидным JSON.
#     """
#     try:
#         # Удаление комментариев
#         cleaned = re.sub(r"//.*?\n", "", raw_value)

#         # Оборачивание ключей в кавычки
#         cleaned = re.sub(r"(?<!\w)([a-zA-Z_][a-zA-Z0-9_]*)(?=\s*:)", r'"\1"', cleaned)

#         # Замена функций на строку-заглушку
#         cleaned = re.sub(
#             r"\b(function|new)\b.*?\{.*?\}",
#             '"placeholder_function"',
#             cleaned,
#             flags=re.DOTALL,
#         )

#         # Удаление методов и лишних запятых
#         cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
#         cleaned = re.sub(
#             r"\b(getById|setById|onClick):.*?function\(.*?\}\,",
#             "",
#             cleaned,
#             flags=re.DOTALL,
#         )

#         return cleaned
#     except Exception as e:
#         logger.error(f"Ошибка очистки JSON: {e}")
#         return raw_value


# def read_js():
#     # Чтение содержимого файла
#     with open("dataLayer_script_content.js", "r", encoding="utf-8") as file:
#         content = file.read()

#     # Регулярное выражение для поиска объектов вида EM.key = value;
#     pattern = re.compile(r"(EM\.[a-zA-Z0-9_]+)\s*=\s*(\{.*?\});", re.DOTALL)

#     # Словарь для хранения извлеченных данных
#     extracted_data = {}

#     # Проходим по всем совпадениям
#     for match in pattern.finditer(content):
#         key = match.group(1)  # Название ключа
#         raw_value = match.group(2)  # Содержимое объекта

#         try:
#             cleaned_value = clean_json(raw_value)

#             # Преобразование в JSON
#             value = json.loads(cleaned_value)
#             extracted_data[key] = value
#         except json.JSONDecodeError as e:
#             logger.error(f"Не удалось распарсить значение для ключа: {key}")
#             logger.error(f"Сырые данные: {raw_value}")
#             logger.error(f"Очищенные данные: {cleaned_value}")
#             logger.error(f"Ошибка: {e}")

#     # Сохранение данных в файл
#     with open("extracted_data.json", "w", encoding="utf-8") as output_file:
#         json.dump(extracted_data, output_file, indent=4, ensure_ascii=False)

#     logger.info("Данные извлечены и сохранены в 'extracted_data.json'.")


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


if __name__ == "__main__":
    read_js()
    # # Вызов функции
    # extract_feedback_from_file(
    #     "dataLayer_script_content.js", object_name="EM.productDiscountedPrice"
    # )
