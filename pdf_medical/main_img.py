from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from configuration.logger_setup import logger
import json
import wordninja
import argparse
import re
import pytesseract
import os
from collections import defaultdict
import pdfplumber
import platform
import time

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")


def validity_text(text_list):
    """
    Принимает список строк, проверяет каждую строку на наличие чисел, заглавных букв, точек и других условий,
    и разделяет её соответствующим образом, добавляя пробелы после определенных последовательностей или с помощью wordninja.split.
    Возвращает список с объединенными строками.
    """
    result_list = []

    # Регулярное выражение для шаблона "числа + заглавные буквы + заглавная с последующими строчными буквами"
    pattern = re.compile(r"(\d+)([A-Z]+)([A-Z][a-z]+)([A-Z][a-z]+)([A-Z][a-z]*)")

    # Регулярное выражение для "город + двухбуквенный штат + цифры"
    city_state_zip_pattern = re.compile(r"([A-Za-z]+)([A-Z]{2})(\d+)")

    # Регулярное выражение для формата "4 заглавные буквы + одна цифра"
    four_caps_one_digit_pattern = re.compile(r"^[A-Z]{4}\d$")

    # Регулярное выражение для числа с десятичной точкой
    decimal_number_pattern = re.compile(r"^\d+\.\d+$")

    # Регулярное выражение для одной буквы и нескольких цифр
    single_letter_digits_pattern = re.compile(r"^[A-Za-z]\d+$")

    # Регулярное выражение для формата "O422M2Z2Z62"
    exclude_pattern = re.compile(r"^O\d{3}M\d{1}Z\d{1}Z\d{2}$")

    # Регулярное выражение для буквы и 3, 4 или 5 цифр
    letter_and_digits_pattern = re.compile(r"^[A-Za-z]\d{3,5}$")

    # Регулярное выражение для формата "буква цифра буква цифры"
    letter_digit_letter_digits_pattern = re.compile(r"^[A-Za-z]\d[A-Za-z]\d+$")

    for text in text_list:
        processed_words = []

        # Проверяем каждое слово в строке
        for word in text.split():
            # Условие для сохранения формата "O422M2Z2Z62" без обработки
            if exclude_pattern.match(word):
                processed_words.append(word)
            # Условие для формата "буква цифра буква цифры"
            elif letter_digit_letter_digits_pattern.match(word):
                processed_words.append(word)
            # Условие для формата "буква и 3, 4 или 5 цифр"
            elif letter_and_digits_pattern.match(word):
                processed_words.append(word)
            # Условие для формата "4 заглавные буквы + одна цифра"
            elif four_caps_one_digit_pattern.match(word):
                processed_words.append(word)
            # Условие для формата "число с десятичной точкой"
            elif decimal_number_pattern.match(word):
                processed_words.append(word)
            # Условие для формата "одна буква и несколько цифр"
            elif single_letter_digits_pattern.match(word):
                processed_words.append(word)
            # Условие для замены "P.0." на "P.O."
            elif "P.0." in word:
                processed_words.append(word.replace("P.0.", "P.O. ") + " ")
            elif city_state_zip_pattern.match(word):
                # Разделяем слово по шаблону "город + двухбуквенный штат + цифры"
                processed_words.extend(city_state_zip_pattern.match(word).groups())
            elif pattern.match(word):
                # Разделяем слово по регулярному выражению и добавляем в обработанные слова
                processed_words.extend(pattern.match(word).groups())
            elif re.match(r"^\d+[A-Z]", word):
                # Если начинается с чисел и заглавных букв, оставляем его как есть
                processed_words.append(word)
            elif re.search(r"[a-z]+[A-Z]", word):
                # Если найдено "строчные + заглавная", разделяем его по заглавным буквам
                processed_words.extend(re.findall(r"[A-Z][a-z]*|[a-z]+[A-Z]", word))
            else:
                # Если не соответствует, используем wordninja.split
                processed_words.extend(wordninja.split(word))

        # Объединяем слова обратно в строку и добавляем в результат
        result_list.append(" ".join(processed_words))

    return result_list


def enhance_image(image):
    """
    Улучшает качество изображения для улучшения распознавания текста.
    """
    image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
    image = image.filter(ImageFilter.MedianFilter(size=3))  # Удаление шумов
    image = image.filter(ImageFilter.SHARPEN)  # Повышение резкости

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)  # Повышение контраста

    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(2)  # Повышение яркости

    image = image.convert("L")  # Конвертация в черно-белое изображение

    # Применяем бинаризацию методом Otsu
    threshold = 140
    image = image.point(lambda p: p > threshold and 255)

    image = ImageOps.autocontrast(image)  # Применяем автоконтраст

    return image


def scale_crop_area(crop_area, scale_factor):
    # Убедимся, что crop_area имеет 4 элемента
    if len(crop_area) != 4:
        raise ValueError(
            "crop_area должен содержать ровно 4 элемента: (left, top, right, bottom)"
        )
    return tuple(int(coord * scale_factor) for coord in crop_area)


def clean_text(text):
    # Убираем все символы, кроме точки
    return re.sub(r"[^A-Za-z0-9.\s]", "", text)


def process_image(pdf_path, output_path, temp_path, scale_factor):
    # Коэффициент масштабирования
    scale_factor = 1  # Увеличение на 1.1
    image_path = "high_res_screenshot.png"  # Укажите путь к вашему изображению
    temp_path = "temp"  # Укажите временный путь для сохранения изображений
    crop_areas = {
        "01": [(75, 70, 800, 255)],
        "3a": [(1620, 70, 2320, 120)],
        "3b": [(1620, 120, 2320, 170)],
        "4": [(2320, 120, 2475, 170)],
        "5": [(1538, 215, 1828, 260)],
        "6a": [(1828, 215, 2030, 260)],
        "6b": [(2032, 215, 2235, 260)],
        "8b": [(110, 310, 950, 360)],
        "9a": [(1280, 265, 2470, 310)],
        "9b": [(980, 310, 1905, 360)],
        "9c": [(1945, 310, 2030, 360)],
        "9d": [(2060, 310, 2350, 360)],
        "10": [(75, 410, 340, 460)],
        "11": [(340, 410, 425, 460)],
        "12": [(425, 410, 600, 460)],
        "13": [(605, 410, 690, 460)],
        "14": [(695, 410, 775, 460)],
        "15": [(780, 410, 865, 460)],
        "16": [(870, 410, 950, 460)],
        "17": [(955, 410, 1040, 460)],
        "31a": [(75, 510, 165, 560)],
        "31b": [(170, 510, 360, 560)],
        "32a": [(375, 510, 450, 560)],
        "32b": [(465, 510, 655, 560)],
        "35a": [(1250, 510, 1325, 560)],
        "35b": [(1340, 510, 1530, 560)],
        "35c": [(1540, 510, 1740, 560)],
        "38a": [(110, 610, 1290, 660)],
        "38b": [(110, 660, 1290, 710)],
        "38c": [(110, 710, 1290, 760)],
        "38d": [(110, 760, 1290, 810)],
        "38e": [(90, 810, 1290, 850)],
        "39a": [(1340, 660, 1410, 845)],
        "39b": [(1430, 660, 1650, 845)],
        "39c": [(1650, 660, 1708, 845)],
        "40a": [(1717, 660, 1793, 845)],
        "40b": [(1805, 660, 2030, 845)],
        "40c": [(2040, 660, 2088, 845)],
        "41": [(2100, 660, 2175, 845)],
        "41a": [(2190, 660, 2410, 845)],
        "41b": [(2410, 660, 2465, 845)],
        "42": [(75, 900, 200, 1900)],
        "43": [(220, 900, 750, 1900)],
        "44": [(945, 901, 1355, 1900)],
        "45": [(1390, 899, 1560, 1900)],
        "46": [(1730, 900, 1790, 1900)],
        "47": [(1850, 901, 2030, 1900)],
        "47a": [(2032, 901, 2085, 1900)],
        "28": [(78, 1965, 180, 2000)],
        "gre_dat": [(1400, 1965, 1560, 2000)],
        "totals": [(1920, 1970, 2030, 2000)],
        "50": [(75, 2060, 700, 2120)],
        "51": [(760, 2065, 1150, 2120)],
        "52": [(1190, 2065, 1240, 2120)],
        "53": [(1275, 2065, 1330, 2120)],
        "55": [(1780, 2065, 1888, 2120)],
        "55a": [(1895, 2065, 1943, 2120)],
        "56": [(2040, 2015, 2400, 2060)],
        "58": [(75, 2260, 800, 2300)],
        "59": [(835, 2260, 910, 2300)],
        "60": [(925, 2260, 1400, 2300)],
        "63": [(75, 2455, 900, 2550)],
        "66": [(105, 2600, 300, 2645)],
        "66a": [(340, 2600, 540, 2645)],
        "66b": [(580, 2600, 750, 2645)],
        "66c": [(810, 2600, 990, 2645)],
        "66d": [(1045, 2600, 1220, 2645)],
        "66e": [(1280, 2600, 1450, 2645)],
        "66f": [(1510, 2600, 1650, 2645)],
        "66g": [(1745, 2600, 1900, 2645)],
        "66h": [(1980, 2600, 2165, 2645)],
        "66i": [(105, 2650, 300, 2690)],
        "69": [(190, 2700, 380, 2745)],
        "76": [(1800, 2750, 2080, 2795)],
        "76last": [(1605, 2805, 2055, 2840)],
        "76first": [(2145, 2805, 2300, 2840)],
        "81a": [(838, 2950, 890, 2985)],
        "81b": [(900, 2950, 1180, 2988)],
    }

    # Открываем изображение
    image = Image.open(image_path)

    all_texts = {}

    # Пример использования функции split_on_capitals
    for key, areas in crop_areas.items():
        for i, crop_area in enumerate(areas):
            # Масштабируем каждый список
            scaled_area = scale_crop_area(
                crop_area, scale_factor
            )  # Передаем кортеж, а не список
            # Обрезаем изображение до заданной области
            cropped_image = image.crop(scaled_area)
            # Улучшаем обрезанное изображение
            cropped_image = enhance_image(cropped_image)
            # Сохраняем обрезанное изображение для визуализации
            filename_cropped_image = os.path.join(
                temp_path, f"cropped_image_{key}_{i+1}.png"
            )
            cropped_image.save(filename_cropped_image)

            # Рисуем прямоугольник на оригинальном изображении для визуализации
            draw = ImageDraw.Draw(image)
            draw.rectangle(crop_area, outline="red", width=2)

            # Все символы, включая буквы, цифры и специальные символы
            whitelist = (
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,."
            )

            custom_config = f"--oem 3 --psm 6 -c tessedit_char_whitelist={whitelist} -c preserve_interword_spaces=1"

            # Извлекаем текст из обрезанного изображения
            text = pytesseract.image_to_string(
                cropped_image, config=custom_config, lang="eng"
            )
            cleaned_text = [
                clean_text(line) for line in text.strip().split("\n") if line
            ]
            # logger.info(f"До обработки: {cleaned_text}")

            # Очистка и проверка текста
            cleaned_text = validity_text(cleaned_text)
            # logger.info(f"Результирующие данные: {cleaned_text}")

            # Сохраняем результат в all_texts
            if key not in all_texts:
                all_texts[key] = []
            all_texts[key].extend(cleaned_text)

    # Сохраняем изображение с нарисованной областью обрезки
    filename_outlined = os.path.join(temp_path, "outlined_image.png")
    image.save(filename_outlined)

    # Проверяем, есть ли данные в all_texts перед созданием DataFrame
    if all_texts:
        max_rows = max(len(column_texts) for column_texts in all_texts.values())
        data = defaultdict(
            list
        )  # Используем defaultdict для автоматического создания списков

        for key, column_texts in all_texts.items():
            # Убираем пустые строки
            cleaned_texts = [text for text in column_texts if text.strip()]
            if cleaned_texts:
                # Если есть непустые строки, добавляем их в data
                data[key].extend(cleaned_texts)

        # Приводим data к обычному словарю для вывода
        data = dict(data)
        logger.info(data)
        # Сохранение результатов в JSON файл
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        return data
    else:
        logger.error("Нет данных для обработки. Словарь all_texts пуст.")
        return {}


def save_high_resolution_screenshot(pdf_path):
    resolution = 300
    page_number = 57  # Номер страницы (начиная с 0)
    output_image_path = "high_res_screenshot.png"

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        # Создаем изображение страницы с указанным разрешением
        image = page.to_image(resolution=resolution).original

        # Преобразуем изображение в оттенки серого
        image = image.convert("L")

        # Повышаем контрастность
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2)

        # Применяем адаптивный порог
        image = ImageOps.autocontrast(image)

        # Применяем размытие для устранения шума
        image = image.filter(ImageFilter.GaussianBlur(radius=1))

        # Повышаем резкость
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(7.5)

        # Сохраняем изображение в файл
        image.save(output_image_path)
        print(f"Скриншот сохранен: {output_image_path}")


def main():
    parser = argparse.ArgumentParser(description="PDF analysis script")
    parser.add_argument("pdf_path", help="Full path to the PDF file")
    parser.add_argument("output_path", help="Full path to the output JSON file")
    parser.add_argument(
        "scale_factor", type=float, help="Scaling factor for image processing"
    )

    args = parser.parse_args()

    # Определяем пути для различных операционных систем и устанавливаем путь к Tesseract
    if platform.system() == "Linux":
        pdf_path = args.pdf_path
        output_path = args.output_path
        pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    elif platform.system() == "Windows":
        pdf_path = args.pdf_path
        output_path = args.output_path
        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )
    else:
        print("Unsupported operating system")
        return

    current_directory = os.getcwd()
    timestamp = str(int(time.time()))
    temp_path = os.path.join(current_directory, "temp", timestamp)

    # Преобразуем аргумент scale_factor в float
    scale_factor = args.scale_factor

    # Вызываем process_image с переданным scale_factor
    process_image(pdf_path, output_path, temp_path, scale_factor)
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()
    # pdf_path = "01.pdf"
    # save_high_resolution_screenshot(pdf_path)
    # process_image()
