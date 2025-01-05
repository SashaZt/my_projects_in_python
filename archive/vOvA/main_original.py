import re
from bs4 import BeautifulSoup
from googletrans import Translator
from configuration.logger_setup import logger


def extract_cyrillic_phrases_from_html(file_path: str):
    # Чтение HTML файла
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Парсинг HTML с использованием BeautifulSoup и парсера lxml
    soup = BeautifulSoup(html_content, "lxml")

    # Регулярное выражение для поиска фраз на кириллице (русский и украинский), включая апострофы
    cyrillic_pattern = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґ'ʼ]+")

    # Список для хранения найденных фраз
    russian_phrases = []

    def extract_text_recursive(element):
        # Извлечение текста из текущего элемента
        if element.string:  # Если текущий элемент содержит текст напрямую
            text = element.string.strip()
            text = re.sub(r"\s+", " ", text).strip()
            if cyrillic_pattern.search(text):
                russian_phrases.append(text)
        else:
            # Если текст вложен в другие теги, продолжаем рекурсивный вызов
            for child in element.children:
                extract_text_recursive(child)

    # Проход по всем нужным тегам
    for element in soup.find_all(["p", "li", "div", "span", "a", "strong"]):
        extract_text_recursive(element)

    return list(set(russian_phrases)), html_content


def translate_phrases(phrases):
    translator = Translator()
    translations = []
    translation_cache = {}

    for phrase in phrases:
        if phrase in translation_cache:
            translated = translation_cache[phrase]
        else:
            translated = translator.translate(phrase, src="ru", dest="it").text
            translation_cache[phrase] = translated

        logger.info(translated)
        translations.append(translated)

    return translations


# def translate_phrases(phrases):
#     translator = Translator()
#     translations = []
#     for phrase in phrases:
#         translated = translator.translate(phrase, src="ru", dest="it")
#         logger.info(translated)
#         translations.append(translated.text)
#     return translations


def replace_and_save_html(file_path: str, phrases, translations, html_content):
    # Заменяем исходные фразы на переведенные в HTML-контенте
    for original, translated in zip(phrases, translations):
        html_content = html_content.replace(original, translated)

    # Сохранение измененного HTML-контента в тот же файл
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    logger.info(f"Translated HTML content saved back to {file_path}")


# Основной код для выполнения всех шагов
file_path = "index.html"

# Шаг 1: Извлечение фраз
phrases, html_content = extract_cyrillic_phrases_from_html(file_path)
logger.info(len(phrases))
logger.info(phrases)
# # # # Шаг 2: Перевод фраз
translations = translate_phrases(phrases)
# logger.info(translations)
# # # # # Шаг 3: Замена фраз и сохранение переведенного HTML в тот же файл
replace_and_save_html(file_path, phrases, translations, html_content)
