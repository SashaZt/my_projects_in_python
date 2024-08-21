import re
from bs4 import BeautifulSoup
from transformers import MarianMTModel, MarianTokenizer


def extract_cyrillic_phrases_from_html(file_path: str):
    # Чтение HTML файла
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Парсинг HTML с использованием BeautifulSoup и парсера lxml
    soup = BeautifulSoup(html_content, "lxml")

    # Извлечение текста из всех элементов
    text = soup.get_text(separator=" ")

    # Очистка текста от лишних пробелов, оставляя переносы строк
    text = re.sub(r"[^\S\r\n]+", " ", text).strip()

    # Разделение текста на части по каждому переносу строки
    blocks = re.split(r"\s*\n+\s*", text)

    # Регулярное выражение для поиска фраз на кириллице (русский и украинский), включая апостроф
    cyrillic_pattern = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґ'ʼ\s,.!?-]+")

    # Поиск всех фраз на кириллице и формирование списка фраз
    russian_phrases = []
    for block in blocks:
        phrases = cyrillic_pattern.findall(block)
        # Фильтрация фраз: удаляем те, которые не содержат кириллицы
        phrases = [
            phrase.strip()
            for phrase in phrases
            if re.search(r"[А-Яа-яЁёІіЇїЄєҐґ]", phrase)
        ]
        if phrases:
            russian_phrases.append(" ".join(phrases))

    return russian_phrases, soup, html_content


def translate_phrases(phrases, model, tokenizer):
    translated_phrases = []
    for phrase in phrases:
        # Подготовка текста для модели и перевод
        translated = model.generate(
            **tokenizer(phrase, return_tensors="pt", padding=True)
        )
        # Расшифровка и добавление перевода в список
        translated_text = tokenizer.decode(translated[0], skip_special_tokens=True)
        translated_phrases.append(translated_text)
    return translated_phrases


def replace_and_save_html(file_path: str, phrases, translations, html_content):
    # Заменяем исходные фразы на переведенные в HTML-контенте
    for original, translated in zip(phrases, translations):
        html_content = html_content.replace(original, translated)

    # Сохранение измененного HTML-контента в тот же файл
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(html_content)
    print(f"Translated HTML content saved back to {file_path}")


# Основной код для выполнения всех шагов
file_path = "index.html"

# Шаг 1: Извлечение фраз
phrases, soup, html_content = extract_cyrillic_phrases_from_html(file_path)

# Настройка модели для перевода с русского на итальянский
model_name = "Helsinki-NLP/opus-mt-ru-it"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

# Шаг 2: Перевод фраз
translations = translate_phrases(phrases, model, tokenizer)

# Шаг 3: Замена фраз и сохранение переведенного HTML в тот же файл
replace_and_save_html(file_path, phrases, translations, html_content)
