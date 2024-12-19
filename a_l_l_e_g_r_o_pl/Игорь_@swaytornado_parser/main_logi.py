import asyncio
import json
import os
import re
import shutil
from parser import Parser
from pathlib import Path

from bs4 import BeautifulSoup
from configuration.logger_setup import logger

# Указываем пути к файлам и папкам
current_directory = Path.cwd()
html_page_directory = current_directory / "html_page"


# # def parsing_page():
# #     all_data = set()
# #     consecutive_no_additions = 0  # Счетчик файлов, где не добавлено уникальных ссылок
# #     max_no_additions = 2  # Лимит на количество подряд файлов без добавлений

# #     for html_file in html_page_directory.glob("*.html"):

# #         with open(html_file, encoding="utf-8") as file:
# #             src = file.read()
# #         soup = BeautifulSoup(src, "lxml")

# #         # Поиск всех элементов <span> с текстом, содержащим "osób"
# #         result = soup.find_all("span", string=lambda t: t and "osób" in t)
# #         url_r = set()
# #         for rs in result:
# #             osob = int(rs.text.replace(" osób", ""))
# #             # Проверяем условие
# #             if osob >= 50:
# #                 # Поднимаемся к <article> и ищем ссылку <a>
# #                 article = rs.find_parent("article")
# #                 if article:
# #                     link_raw = article.find("a", href=True)
# #                     if link_raw:
# #                         link = link_raw["href"]
# #                         url_r.add(link)

# #         # Логируем результаты текущего файла
# #         # logger.info(f"Файл: {html_file.name}, Найдено ссылок: {len(url_r)}")

# #         # Состояние all_data до обновления
# #         before_update = len(all_data)

# #         # Обновляем общий набор уникальных ссылок
# #         all_data.update(url_r)

# #         # Количество уникальных ссылок, добавленных из текущего файла
# #         added_count = len(all_data) - before_update
# #         logger.info(
# #             f"Файл: {html_file.name}, Уникальных ссылок добавлено: {added_count}"
# #         )

# #         # Проверяем, были ли добавлены уникальные ссылки
# #         if added_count == 0:
# #             consecutive_no_additions += 1
# #             logger.info(
# #                 f"Файл: {html_file.name}, Ничего нового не добавлено. Подряд файлов без добавлений: {consecutive_no_additions}"
# #             )
# #             # Проверяем, достигли ли лимита
# #             if consecutive_no_additions >= max_no_additions:
# #                 logger.info(
# #                     "Достигнут лимит файлов без добавлений. Завершаем обработку."
# #                 )
# #                 break
# #         else:
# #             consecutive_no_additions = (
# #                 0  # Сбрасываем счетчик, если добавлены уникальные ссылки
# #             )

# #     # Логируем общее количество уникальных ссылок
# #     logger.info(f"Общее количество уникальных ссылок: {len(all_data)}")
# #     return all_data


def parsin_page_json():
    """
    Находит первый тег <script type="application/json">, который начинается с '{"__listing_StoreState'.
    Преобразует содержимое тега в JSON и возвращает.

    :param src: HTML-код страницы
    :return: Python-объект (результат json.loads) или None, если не найдено
    """
    for html_file in html_page_directory.glob("*.html"):
        with open(html_file, encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, "lxml")

        # Поиск всех тэгов <script type="application/json">
        script_tags = soup.find_all("script", {"type": "application/json"})

        for script in script_tags:
            if script.string and script.string.strip().startswith(
                '{"__listing_StoreState'
            ):
                try:
                    # Преобразуем JSON в Python-объект
                    json_data = json.loads(script.string.strip())
                    js_data = parse_listing_store_state(json_data)
                    logger.info(js_data)
                    with open("kyky.json", "w", encoding="utf-8") as f:
                        json.dump(
                            json_data, f, ensure_ascii=False, indent=4
                        )  # Записываем в файл
                    logger.info("JSON-данные успешно извлечены.")
                    break
                    # return json_data  # Возвращаем JSON-объект и прекращаем поиск
                except json.JSONDecodeError as e:
                    # Логируем ошибку при декодировании JSON
                    logger.error(f"Ошибка декодирования JSON: {e}")
                    return None

        logger.warning("Не найдено подходящего тега <script>.")
        # return None


def parse_listing_store_state():
    """
    Парсит JSON-данные из __listing_StoreState, извлекает URL, если count >= 50.

    :param json_data: JSON-объект, содержащий __listing_StoreState
    :return: Список URL, где count >= 50
    """
    urls = []
    with open("decoded_json_output.json", "r", encoding="utf-8") as json_file:
        loaded_json_data = json.load(json_file)
    try:
        # Извлекаем __listing_StoreState -> items -> elements
        elements = loaded_json_data["__listing_StoreState"]["items"]["elements"]

        for element in elements:
            # Извлекаем URL из текущего элемента
            url = element.get("url", None)

            # Ищем словарь productPopularity внутри элемента
            product_popularity = element.get("productPopularity", {})
            label = product_popularity.get("label", "")
            # Регулярное выражение для извлечения числа перед 'osoby', 'osób', или 'osoba'
            match = re.search(r"(\d+)\s+(osoby|osób|osoba)", label)
            count = int(match.group(1)) if match else 0
            if count >= 50 and url:
                logger.info(count)
    except KeyError as e:
        logger.error(f"Ошибка в структуре JSON: отсутствует ключ {e}")
    except Exception as e:
        logger.error(f"Общая ошибка при разборе JSON: {e}")


if __name__ == "__main__":
    parse_listing_store_state()
