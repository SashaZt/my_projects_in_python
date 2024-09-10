import wordninja
from configuration.logger_setup import logger
import pdfplumber
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import pandas as pd
import re
import json
import os
import shutil
from collections import defaultdict


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")


def anali_pdf_02(pdf_path, test_page_no=0):

    os.makedirs(temp_path, exist_ok=True)
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            if page_no == test_page_no:
                # Настройки для обнаружения таблиц

                vertical_lines_01 = [18, 193]
                horizontal_lines_01 = [
                    15,
                    25,
                    40,
                    51,
                    63,
                ]
                vertical_lines_02 = [193, 368]
                horizontal_lines_02 = [
                    15,
                    25,
                    40,
                    51,
                    63,
                ]
                vertical_lines_03a = [390, 505, 510]
                horizontal_lines_03a = [
                    15,
                    28,
                ]
                vertical_lines_03b = [390, 505, 510]
                horizontal_lines_03b = [
                    28,
                    40,
                ]
                vertical_lines_04 = [550, 560, 595]
                horizontal_lines_04 = [
                    28,
                    40,
                ]
                vertical_lines_05 = [370, 375, 440]
                horizontal_lines_05 = [
                    51,
                    63,
                ]
                vertical_lines_06 = [440, 490, 537]
                horizontal_lines_06 = [
                    51,
                    63,
                ]
                vertical_lines_07 = [537, 539, 595]
                horizontal_lines_07 = [
                    51,
                    63,
                ]
                vertical_lines_08 = [25, 220]
                horizontal_lines_08 = [
                    62,
                    75,
                    88,
                ]
                vertical_lines_09 = [300, 580]
                horizontal_lines_09 = [
                    62,
                    75,
                    88,
                ]

                vertical_lines_10 = [18, 76, 80]
                horizontal_lines_10 = [
                    98,
                    110,
                ]
                vertical_lines_11 = [82, 98, 103]
                horizontal_lines_11 = [
                    98,
                    110,
                ]
                vertical_lines_12 = [103, 141, 146]
                horizontal_lines_12 = [
                    98,
                    110,
                ]
                vertical_lines_13 = [143, 148, 165]
                horizontal_lines_13 = [
                    98,
                    110,
                ]
                vertical_lines_14 = [162, 167, 186]
                horizontal_lines_14 = [
                    98,
                    110,
                ]
                vertical_lines_15 = [184, 189, 207]
                horizontal_lines_15 = [
                    98,
                    110,
                ]
                vertical_lines_16 = [203, 208, 228]
                horizontal_lines_16 = [
                    98,
                    110,
                ]
                vertical_lines_17 = [223, 228, 250]
                horizontal_lines_17 = [
                    98,
                    110,
                ]
                vertical_lines_18 = [247, 252, 270]
                horizontal_lines_18 = [
                    98,
                    110,
                ]
                vertical_lines_19 = [268, 273, 292]
                horizontal_lines_19 = [
                    98,
                    110,
                ]
                vertical_lines_20 = [290, 295, 313]
                horizontal_lines_20 = [
                    98,
                    110,
                ]
                vertical_lines_21 = [310, 315, 335]
                horizontal_lines_21 = [
                    98,
                    110,
                ]
                vertical_lines_22 = [330, 335, 355]
                horizontal_lines_22 = [
                    98,
                    110,
                ]
                vertical_lines_23 = [352, 357, 375]
                horizontal_lines_23 = [
                    98,
                    110,
                ]
                vertical_lines_31 = [20, 40, 80]
                horizontal_lines_31 = [
                    120,
                    132,
                ]
                vertical_lines_32 = [88, 110, 157]
                horizontal_lines_32 = [
                    120,
                    132,
                ]
                vertical_lines_35 = [300, 318, 368, 415]
                horizontal_lines_35 = [
                    120,
                    145,
                ]
                vertical_lines_38 = [
                    20,
                    150,
                    158,
                ]
                horizontal_lines_38 = [
                    145,
                    158,
                ]

                vertical_lines_39a = [318, 323, 340]
                horizontal_lines_39a = [156, 205]
                vertical_lines_39b = [338, 342, 410]
                horizontal_lines_39b = [156, 205]
                vertical_lines_40a = [
                    408,
                    412,
                    432,
                ]
                horizontal_lines_40a = [156, 205]
                vertical_lines_40b = [
                    428,
                    432,
                    502,
                ]
                horizontal_lines_40b = [156, 205]
                vertical_lines_41a = [
                    502,
                    507,
                    522,
                ]
                horizontal_lines_41a = [156, 205]
                vertical_lines_41b = [522, 527, 595]
                horizontal_lines_41b = [156, 205]
                vertical_lines_23t = [18, 50, 90, 105, 145, 330, 380, 450, 510]
                horizontal_lines_23t = [470, 485]
                vertical_lines_50 = [18, 175, 180]
                horizontal_lines_50 = [495, 530]
                vertical_lines_51 = [180, 280, 285]
                horizontal_lines_51 = [495, 530]
                vertical_lines_52 = [283, 298, 303]
                horizontal_lines_52 = [495, 530]
                vertical_lines_53 = [300, 308, 320]
                horizontal_lines_53 = [495, 530]
                vertical_lines_54 = [320, 325, 390]
                horizontal_lines_54 = [495, 530]
                vertical_lines_55 = [390, 395, 467]
                horizontal_lines_55 = [495, 530]
                vertical_lines_56 = [487, 590, 595]
                horizontal_lines_56 = [482, 495]
                vertical_lines_57 = [487, 590, 595]
                horizontal_lines_57 = [495, 530]
                vertical_lines_58 = [18, 195, 200]
                horizontal_lines_58 = [542, 575]
                vertical_lines_59 = [195, 200, 220]
                horizontal_lines_59 = [542, 575]
                vertical_lines_60 = [220, 357, 362]
                horizontal_lines_60 = [542, 575]
                vertical_lines_66 = [
                    18,
                    70,
                    80,
                    124,
                    138,
                    185,
                    195,
                    230,
                    250,
                    295,
                    305,
                    350,
                    362,
                    410,
                    420,
                    465,
                    475,
                    525,
                    532,
                ]
                horizontal_lines_66 = [625, 635]
                vertical_lines_67 = [
                    18,
                    70,
                    80,
                    120,
                    138,
                    185,
                    195,
                    230,
                    250,
                    295,
                    305,
                    350,
                    362,
                    410,
                    420,
                    465,
                    475,
                    525,
                    532,
                ]
                horizontal_lines_67 = [635, 645]
                vertical_lines_69 = [45, 90, 95]
                horizontal_lines_69 = [647, 660]
                vertical_lines_76 = [
                    420,
                    500,
                    505,
                ]
                horizontal_lines_76 = [660, 672]
                vertical_lines_76L = [
                    385,
                    490,
                    495,
                ]
                horizontal_lines_76L = [672, 682]
                vertical_lines_76F = [
                    515,
                    580,
                    585,
                ]
                horizontal_lines_76F = [672, 682]
                vertical_lines_81 = [
                    200,
                    215,
                    285,
                ]
                horizontal_lines_81 = [705, 720]
                # Стратегии могут быть: "lines", "text", "explicit"
                table_settings = {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": vertical_lines_66,
                    "horizontal_strategy": "explicit",
                    "explicit_horizontal_lines": horizontal_lines_66,
                    "snap_tolerance": 3,  # Толерантность при поиске линий (в пикселях)
                    "join_tolerance": 3,  # Толерантность при объединении линий
                    "edge_min_length": 10,  # Минимальная длина линий
                    "min_words_vertical": 1,  # Минимальное количество слов для вертикальной линии
                    "min_words_horizontal": 1,  # Минимальное количество слов для горизонтальной линии
                }
                tables = page.extract_tables(table_settings)

                # Выводим данные всех найденных таблиц
                for table_no, table in enumerate(tables):
                    print(f"Страница №{page_no + 1}, Таблица №{table_no + 1}:")
                    for row in table:
                        print(row)
                    print("\n")  # Добавляем пустую строку для разделения таблиц

                # Визуализация поиска таблиц с настройками
                image = page.to_image(resolution=150)
                image.debug_tablefinder(table_settings)
                filename = os.path.join(temp_path, "analis.png")
                image.save(filename)
                break


def write_json(pdf_path):
    # Определение всех наборов линий
    lines = {
        1: ([18, 192], [15, 25, 40, 51, 63]),
        2: ([390, 505, 510], [15, 28]),
        2.1: ([390, 505, 595], [28, 40]),
        2.2: ([370, 440, 490, 599], [51, 63]),
        3: ([25, 580], [62, 75, 90]),
        4: ([20, 80, 100, 143, 165, 186, 207, 228, 250], [98, 110]),
        5: ([20, 40, 80, 110, 158, 318, 368, 415], [120, 132]),
        6: ([20, 150, 158], [145, 158]),
        7: ([320, 340, 410, 432, 502, 522, 595], [156, 170]),
        8: ([18, 50, 90, 105, 145, 330, 380, 450, 510], [470, 485]),
        9: ([18, 180, 285, 300, 320, 390, 465, 490, 590], [495, 530]),
        10: ([18, 200, 220, 300, 320, 360, 465, 490, 590], [545, 575]),
        11: (
            [
                18,
                70,
                80,
                120,
                138,
                185,
                195,
                230,
                250,
                295,
                305,
                350,
                362,
                410,
                420,
                465,
                475,
                525,
                532,
            ],
            [625, 635],
        ),
        12: (
            [
                18,
                70,
                80,
                120,
                138,
                185,
                195,
                230,
                250,
                295,
                305,
                350,
                362,
                410,
                420,
                465,
                475,
                525,
                532,
            ],
            [635, 645],
        ),
        13: ([45, 95, 130, 180, 230, 278, 342, 412, 468, 525, 590], [647, 660]),
        14: ([420, 500, 532], [660, 672]),
        15: ([380, 490, 580], [672, 682]),
        16: ([200, 215, 285], [705, 720]),
    }

    def flatten_data(nested_list):
        # Объединяем все строки в один список, игнорируя пустые строки
        return [
            ";".join(
                filter(None, [item for sublist in nested_list for item in sublist])
            )
        ]

    results = {}

    page_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            # if page_no == test_page_no:
            save_high_resolution_screenshot(pdf_path, page_no)
            for line_no, (v_lines, h_lines) in lines.items():
                # Пропуск пустых списков линий
                if not v_lines or not h_lines:
                    continue

                table_settings = {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": v_lines,
                    "horizontal_strategy": "explicit",
                    "explicit_horizontal_lines": h_lines,
                    "snap_tolerance": 3,
                    "join_tolerance": 3,
                    "edge_min_length": 10,
                    "min_words_vertical": 1,
                    "min_words_horizontal": 1,
                }
                tables = page.extract_tables(table_settings)

                if tables:  # Пропуск пустых таблиц
                    for table in tables:
                        flattened_table = flatten_data(table)
                        page_data.extend(flattened_table)
            # Извлекаем текст из изображения
            data_table = extract_text_from_image()

            # Пример ключей, привязанных к данным PDF (это пример, необходимо настроить под ваш конкретный случай)
            keys = [
                "1",
                "3a",
                "3b",
                "5",
                "9a",
                "10",
                "31",
                "38",
                "39",
                "23",
                "50",
                "58",
                "66",
                "67",
                "69",
                "76",
                "76L",
                "81",
            ]

            # Привязываем ключи к данным PDF
            pdf_data_with_keys = {key: value for key, value in zip(keys, page_data)}

            # Добавляем данные из PDF и из изображения в результаты
            if page_data:
                results[f"Page:{page_no + 1}"] = {
                    "pdf_data": pdf_data_with_keys,
                    "image_data": data_table,
                }

    # Сохранение результатов в JSON файл
    with open("output.json", "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)


def save_high_resolution_screenshot(pdf_path):
    resolution = 300
    page_number = 0  # Номер страницы (начиная с 0)
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


# def enhance_image(image):
#     """
#     Улучшает качество изображения для улучшения распознавания текста.
#     """
#     # Повышаем резкость
#     image = image.filter(ImageFilter.SHARPEN)

#     # Повышаем контраст
#     enhancer = ImageEnhance.Contrast(image)
#     image = enhancer.enhance(2)

#     # Повышаем яркость
#     enhancer = ImageEnhance.Brightness(image)
#     image = enhancer.enhance(1.5)

#     # Конвертируем изображение в черно-белое
#     image = image.convert("L")

#     return image


# # Рабочий вариант
# def enhance_image(image):
#     """
#     Улучшает качество изображения для улучшения распознавания текста.
#     """
#     # Повышаем резкость
#     image = image.filter(ImageFilter.SHARPEN)

#     # Повышаем контраст
#     enhancer = ImageEnhance.Contrast(image)
#     image = enhancer.enhance(2)

#     # Повышаем яркость
#     enhancer = ImageEnhance.Brightness(image)
#     image = enhancer.enhance(2)

#     # Конвертируем изображение в черно-белое
#     image = image.convert("L")

#     # Експерементально
#     # # Применяем адаптивную бинаризацию
#     # image = ImageOps.autocontrast(image)
#     # image = ImageOps.invert(image)
#     # threshold = 150
#     # image = image.point(lambda p: p > threshold and 255)


#     return image
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


def clean_text(text):
    # Убираем все символы, кроме точки
    return re.sub(r"[^A-Za-z0-9.\s]", "", text)


def generate_keys():
    keys = []
    i = 42
    while len(keys) < 9:  # Должно совпадать с количеством crop_areas
        if i == 47:
            keys.append(f"{i}a")
            keys.append(f"{i}b")
        else:
            keys.append(str(i))
        i += 1
    return keys


# def validity_text(text_list):
#     """
#     Принимает список строк, делит каждую строку на слова с помощью wordninja.split,
#     и возвращает список с объединенными строками.
#     """
#     result_list = []
#     for text in text_list:
#         # Разделяем строку на слова
#         split_words = wordninja.split(text)
#         # Объединяем слова обратно в строку и добавляем в результат
#         result_list.append(" ".join(split_words))
#     return result_list


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


def extract_text_from_image():
    # Коэффициент масштабирования
    scale_factor = 1  # Увеличение на 1.1
    image_path = "high_res_screenshot.png"  # Укажите путь к вашему изображению
    temp_path = "temp"  # Укажите временный путь для сохранения изображений

    crop_areas_42_49 = [
        (75, 900, 200, 1900),
        (220, 900, 750, 1900),
        (945, 901, 1355, 1900),
        (1390, 900, 1560, 1900),
        (1730, 900, 1790, 1900),
        (1850, 901, 2030, 1900),
        (2032, 901, 2085, 1900),
        (2130, 900, 2385, 1900),
        (2410, 900, 2465, 1900),
    ]
    crop_areas_01 = [
        (75, 70, 800, 255),
    ]
    crop_areas_3a = [
        (1620, 70, 2320, 120),
    ]
    crop_areas_3b = [
        (1620, 120, 2320, 170),
    ]
    crop_areas_4 = [
        (2320, 120, 2475, 170),
    ]
    crop_areas_5 = [
        (1538, 215, 1828, 260),
    ]
    crop_areas_6a = [
        (1828, 215, 2030, 260),
    ]
    crop_areas_6b = [
        (2032, 215, 2235, 260),
    ]
    crop_areas_8b = [
        (110, 310, 950, 360),
    ]
    crop_areas_9a = [
        (1280, 265, 2470, 310),
    ]
    crop_areas_9b = [
        (980, 310, 1905, 360),
    ]
    crop_areas_9c = [
        (1945, 310, 2030, 360),
    ]
    crop_areas_9d = [
        (2060, 310, 2350, 360),
    ]

    crop_areas_10 = [
        (75, 410, 340, 460),
    ]

    crop_areas_11 = [
        (340, 410, 425, 460),
    ]
    crop_areas_12 = [
        (425, 410, 600, 460),
    ]
    crop_areas_13 = [
        (605, 410, 690, 460),
    ]
    crop_areas_14 = [
        (695, 410, 775, 460),
    ]
    crop_areas_15 = [
        (780, 410, 865, 460),
    ]
    crop_areas_16 = [
        (870, 410, 950, 460),
    ]
    crop_areas_17 = [
        (955, 410, 1040, 460),
    ]
    crop_areas_31a = [
        (75, 510, 165, 560),
    ]
    crop_areas_31b = [
        (170, 510, 360, 560),
    ]
    crop_areas_32a = [
        (375, 510, 450, 560),
    ]
    crop_areas_32b = [
        (465, 510, 655, 560),
    ]
    crop_areas_35a = [
        (1250, 510, 1325, 560),
    ]
    crop_areas_35b = [
        (1340, 510, 1530, 560),
    ]
    crop_areas_35c = [
        (1540, 510, 1740, 560),
    ]
    crop_areas_38a = [
        (110, 610, 1290, 660),
    ]
    crop_areas_38b = [
        (110, 660, 1290, 710),
    ]
    crop_areas_38 = [
        (110, 710, 1290, 760),
    ]
    crop_areas = [
        (1620, 70, 2320, 120),
    ]

    # Масштабируем каждый список
    crop_areas_01 = scale_crop_areas(crop_areas_01, scale_factor)
    crop_areas_3a = scale_crop_areas(crop_areas_3a, scale_factor)
    crop_areas_3b = scale_crop_areas(crop_areas_3b, scale_factor)

    # Открываем изображение
    image = Image.open(image_path)

    all_texts = {}

    cropped_image = image.crop(crop_area)

    # Улучшаем обрезанное изображение
    cropped_image = enhance_image(cropped_image)

    # Сохраняем обрезанное изображение для визуализации
    filename_cropped_image = os.path.join(temp_path, f"cropped_image_{i+1}.png")
    cropped_image.save(filename_cropped_image)
    # Рисуем прямоугольник на оригинальном изображении для визуализации
    draw = ImageDraw.Draw(image)
    draw.rectangle(crop_area, outline="red", width=2)

    # Все символы, включая буквы, цифры и специальные символы
    whitelist = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,."

    custom_config = f"--oem 3 --psm 6 -c tessedit_char_whitelist={whitelist} -c preserve_interword_spaces=1"

    text = pytesseract.image_to_string(cropped_image, config=custom_config, lang="eng")
    text = split_on_capitals(text)
    logger.info(text)
    # Чистим текст и удаляем пустые строки
    cleaned_text = [clean_text(line) for line in text.strip().split("\n") if line]
    logger.info(cleaned_text)
    all_texts[image_keys[i]] = cleaned_text  # Привязываем ключ к списку

    # Сохраняем изображение с нарисованной областью обрезки
    filename_outlined = os.path.join(temp_path, "outlined_image.png")
    image.save(filename_outlined)

    # Создаем DataFrame для структурирования данных
    max_rows = max(len(column_texts) for column_texts in all_texts.values())
    data = {
        key: column_texts + [""] * (max_rows - len(column_texts))
        for key, column_texts in all_texts.items()
    }
    logger.info(data)
    return data


def process_single_crop_area():

    crop_areas = [(2215, 2650, 2465, 2690)]

    scale_factor = 1  # Увеличение на 1.1
    image_path = "high_res_screenshot.png"  # Укажите путь к вашему изображению
    temp_path = "temp"  # Укажите временный путь для сохранения изображений
    # Открываем изображение
    image = Image.open(image_path)

    # Извлекаем первую (и единственную) область из списка
    crop_area = crop_areas[0]

    # Обрезаем изображение до заданной области
    cropped_image = image.crop(crop_area)

    # Улучшаем обрезанное изображение
    cropped_image = enhance_image(cropped_image)

    # Сохраняем обрезанное изображение для визуализации
    filename_cropped_image = os.path.join(temp_path, "cropped_image.png")
    cropped_image.save(filename_cropped_image)

    # Рисуем прямоугольник на оригинальном изображении для визуализации
    draw = ImageDraw.Draw(image)
    draw.rectangle(crop_area, outline="red", width=2)

    # Все символы, включая буквы, цифры и специальные символы
    whitelist = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,."

    custom_config = f"--oem 3 --psm 6 -c tessedit_char_whitelist={whitelist} -c preserve_interword_spaces=1"

    text = pytesseract.image_to_string(cropped_image, config=custom_config, lang="eng")
    cleaned_text = [clean_text(line) for line in text.strip().split("\n") if line]
    logger.info(f"До обработки: {cleaned_text}")
    cleaned_text = validity_text(cleaned_text)
    logger.info(f"Результирующие данные: {cleaned_text}")

    # Сохраняем изображение с нарисованной областью обрезки
    filename_outlined = os.path.join(temp_path, "outlined_image.png")
    image.save(filename_outlined)

    return cleaned_text


# def validity_text(text_list):
#     """
#     Принимает список строк, делит каждую строку на слова с помощью wordninja.split,
#     и выполняет дополнительную проверку для слов с внутренними заглавными буквами.
#     Возвращает список с объединенными строками.
#     """
#     result_list = []
#     for text in text_list:
#         # Разделяем строку на слова
#         split_words = wordninja.split(text)

#         # Обрабатываем каждое слово, проверяя наличие внутренней заглавной буквы
#         processed_words = []
#         for word in split_words:
#             # Если слово соответствует шаблону, разделяем его
#             if re.search(r"[a-z]+[A-Z]", word):
#                 processed_words.extend(re.findall(r"[A-Z][a-z]*|[a-z]+[A-Z]", word))
#             else:
#                 processed_words.append(word)

#         # Объединяем слова обратно в строку и добавляем в результат
#         result_list.append(" ".join(processed_words))

#     return result_list


def update_json_with_image_data():
    json_path = "output.json"
    # Чтение существующего файла JSON
    with open(json_path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)

    # Извлечение новых данных из изображения
    new_data = extract_text_from_image()

    # Добавление новых данных в существующий JSON
    page_no = max(json_data.keys(), key=int)  # Получаем последний номер страницы
    page_no = int(page_no) + 1  # Увеличиваем номер страницы для новых данных

    json_data[page_no] = new_data

    # Сохранение обновленных данных обратно в JSON
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=4)

    print(f"Данные успешно добавлены в {json_path}")


def split_on_capitals(text):
    """
    Разделяет текст на слова в местах, где начинаются заглавные буквы,
    сохраняя числа и учитывая, что слово состоит только из заглавных букв.
    Например, "1199SEIUNationalBenfitFund" -> ["1199", "SEIU", "National", "Benfit", "Fund"]
    """
    # Проверяем, состоит ли слово только из заглавных букв
    if text.isupper():
        return [text]  # Возвращаем слово как есть

    # Регулярное выражение, которое учитывает числа и заглавные буквы
    return re.findall(r"[0-9]+|[A-Z][a-z]*|[A-Z]+(?=[A-Z]|$)", text)


def scale_crop_area(crop_area, scale_factor):
    # Убедимся, что crop_area имеет 4 элемента
    if len(crop_area) != 4:
        raise ValueError(
            "crop_area должен содержать ровно 4 элемента: (left, top, right, bottom)"
        )
    return tuple(int(coord * scale_factor) for coord in crop_area)


# На весь список ПОКА ЗАКРЫТА она
def process_image():
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
            logger.info(f"До обработки: {cleaned_text}")

            # Очистка и проверка текста
            cleaned_text = validity_text(cleaned_text)
            logger.info(f"Результирующие данные: {cleaned_text}")

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
        return data
    else:
        logger.error("Нет данных для обработки. Словарь all_texts пуст.")
        return {}


if __name__ == "__main__":
    pdf_path = "02.pdf"
    # write_json(pdf_path)
    save_high_resolution_screenshot(pdf_path)
    # anali_pdf_02(pdf_path, test_page_no=0)
    process_single_crop_area()
    # process_image()
    # extract_text_from_image()
    # update_json_with_image_data()
