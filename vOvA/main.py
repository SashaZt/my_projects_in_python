import re
from bs4 import BeautifulSoup
from googletrans import Translator
from configuration.logger_setup import logger


def process_element(element, translator, cyrillic_pattern):
    # Если текущий элемент содержит текст напрямую
    if element.string:
        text = element.string.strip()
        text = re.sub(r"\s+", " ", text).strip()

        # Исключаем строки, содержащие HTML-теги или JS-код
        if re.search(r"<[^>]+>", text) or re.search(r"[{};<>]", text):
            return

        if cyrillic_pattern.search(text):
            # Перевод текста
            translated = translator.translate(text, src="ru", dest="it").text
            logger.info(f"Original: {text} | Translated: {translated}")
            # Замена текста в элементе
            element.string.replace_with(translated)
    else:
        # Если текст вложен в другие теги, продолжаем рекурсивный вызов
        for child in element.children:
            process_element(child, translator, cyrillic_pattern)


def extract_and_translate(file_path: str):
    # Чтение HTML файла
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Парсинг HTML с использованием BeautifulSoup и парсера lxml
    soup = BeautifulSoup(html_content, "lxml")

    # Регулярное выражение для поиска фраз на кириллице (русский и украинский), включая апострофы
    cyrillic_pattern = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґ'ʼ]+")

    # Инициализация переводчика
    translator = Translator()

    # Проход по всем нужным тегам и перевод текста
    for element in soup.find_all(["p", "li", "div", "span", "a", "strong"]):
        process_element(element, translator, cyrillic_pattern)

    # Сохранение измененного HTML-контента в тот же файл
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(str(soup))
    logger.info(f"Translated HTML content saved back to {file_path}")


# Основной код для выполнения всех шагов
file_path = "index.html"
extract_and_translate(file_path)
