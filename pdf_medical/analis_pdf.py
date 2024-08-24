import pdfplumber
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import pandas as pd
import re
import json
import os
import shutil

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
    page_number = 15  # Номер страницы (начиная с 0)
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
    # Увеличиваем изображение для лучшего распознавания
    image = image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)

    # Повышаем резкость
    image = image.filter(ImageFilter.SHARPEN)

    # Повышаем контраст
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(
        1.5
    )  # Слегка уменьшаем контраст, чтобы не потерять мелкие детали

    # Повышаем яркость
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.2)  # Слегка уменьшаем яркость, чтобы сохранить детали

    # Конвертируем изображение в черно-белое
    image = image.convert("L")

    # # Применяем пороговое значение для улучшения контраста текста
    # threshold = 140
    # image = image.point(lambda p: p > threshold and 255)
    # Применяем бинаризацию Otsu для улучшения контраста текста
    image = ImageOps.autocontrast(image)
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


def scale_crop_areas(crop_areas, scale_factor):
    return [tuple(int(coord * scale_factor) for coord in area) for area in crop_areas]


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
    crop_areas = [
        (110, 710, 1290, 760),
    ]

    # Масштабируем каждый список
    crop_areas_01 = scale_crop_areas(crop_areas_01, scale_factor)
    crop_areas_3a = scale_crop_areas(crop_areas_3a, scale_factor)
    crop_areas_3b = scale_crop_areas(crop_areas_3b, scale_factor)

    # Открываем изображение
    image = Image.open(image_path)

    all_texts = {}

    # Генерируем ключи начиная с 42, включая 47a и 47b
    image_keys = generate_keys()

    for i, crop_area in enumerate(crop_areas):
        # Обрезаем изображение до заданной области
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

        custom_config = f"--oem 3 --psm 6 -c tessedit_char_whitelist={whitelist}"
        text = pytesseract.image_to_string(
            cropped_image, config=custom_config, lang="eng"
        )

        # Чистим текст и удаляем пустые строки
        cleaned_text = [clean_text(line) for line in text.strip().split("\n") if line]
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
    print(data)
    return data


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


if __name__ == "__main__":
    pdf_path = "01.pdf"
    # write_json(pdf_path)
    # save_high_resolution_screenshot(pdf_path)
    # anali_pdf_02(pdf_path, test_page_no=0)

    extract_text_from_image()
    # update_json_with_image_data()
