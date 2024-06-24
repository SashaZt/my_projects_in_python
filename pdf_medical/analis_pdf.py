import pdfplumber
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import pandas as pd
import re
import json

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


def anali_pdf_02(pdf_path, test_page_no=0):
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            if page_no == test_page_no:
                # Настройки для обнаружения таблиц

                vertical_lines_01 = [18, 192]
                horizontal_lines_01 = [
                    15,
                    25,
                    40,
                    51,
                    63,
                    76,
                    88,
                ]
                vertical_lines_02 = [370, 599]
                horizontal_lines_02 = [
                    15,
                    28,
                    40,
                    51,
                    63,
                ]
                vertical_lines_03 = [25, 580]
                horizontal_lines_03 = [
                    62,
                    75,
                    90,
                ]
                vertical_lines_04 = [20, 80, 100, 143, 165, 186, 207, 228, 250]
                horizontal_lines_04 = [
                    98,
                    110,
                ]
                vertical_lines_05 = [20, 80, 110, 158, 318, 368, 415]
                horizontal_lines_05 = [
                    120,
                    132,
                ]
                vertical_lines_06 = [
                    20,
                    150,
                    158,
                ]
                horizontal_lines_06 = [
                    145,
                    158,
                ]

                vertical_lines_07 = [320, 340, 410, 432, 502, 522, 595]
                horizontal_lines_07 = [156, 170]
                vertical_lines_08 = [380, 510]
                horizontal_lines_08 = [470, 485]
                vertical_lines_09 = [18, 180, 285, 300, 320, 390, 465, 490, 590]
                horizontal_lines_09 = [495, 530]
                vertical_lines_10 = [18, 200, 220, 300, 320, 360, 465, 490, 590]
                horizontal_lines_10 = [545, 575]
                vertical_lines_11 = [
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
                horizontal_lines_11 = [625, 635]
                vertical_lines_12 = [
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
                horizontal_lines_12 = [635, 645]
                vertical_lines_13 = [
                    45,
                    95,
                    130,
                    180,
                    230,
                    278,
                    342,
                    412,
                    468,
                    525,
                    590,
                ]
                horizontal_lines_13 = [647, 660]
                vertical_lines_14 = [
                    420,
                    500,
                    532,
                ]
                horizontal_lines_14 = [660, 672]
                vertical_lines_15 = [
                    380,
                    490,
                    580,
                ]
                horizontal_lines_15 = [672, 682]
                vertical_lines_16 = [
                    200,
                    215,
                    285,
                ]
                horizontal_lines_16 = [705, 720]
                # Стратегии могут быть: "lines", "text", "explicit"
                table_settings = {
                    "vertical_strategy": "explicit",
                    "explicit_vertical_lines": vertical_lines_07,
                    "horizontal_strategy": "explicit",
                    "explicit_horizontal_lines": horizontal_lines_07,
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
                image.save("analis.png")


def write_json(pdf_path, test_page_no=0):
    # Определение всех наборов линий
    lines = {
        1: ([18, 192], [15, 25, 40, 51, 63, 76, 88]),
        2: ([370, 599], [15, 28, 40, 51, 63]),
        3: ([25, 580], [62, 75, 90]),
        4: ([20, 80, 100, 143, 165, 186, 207, 228, 250], [98, 110]),
        5: ([20, 80, 110, 158, 318, 368, 415], [120, 132]),
        6: ([20, 150, 158], [145, 158]),
        7: ([320, 340, 410, 432, 502, 522, 595], [156, 170]),
        8: ([380, 510], [470, 485]),
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

    results = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            if page_no == test_page_no:
                results[page_no + 1] = {}
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
                        table_data = []
                        for table in tables:
                            filtered_table = [
                                list(filter(None, row)) for row in table if any(row)
                            ]
                            if filtered_table:
                                table_data.append(filtered_table)

                        results[page_no + 1][line_no] = table_data

                break  # Останавливаем цикл после обработки нужной страницы
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


def enhance_image(image):
    """
    Улучшает качество изображения для улучшения распознавания текста.
    """
    # Повышаем резкость
    image = image.filter(ImageFilter.SHARPEN)

    # Повышаем контраст
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2)

    # Повышаем яркость
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.5)

    # Конвертируем изображение в черно-белое
    image = image.convert("L")

    return image


def clean_text(text):
    # Убираем все символы, кроме точки
    return re.sub(r"[^A-Za-z0-9.\s]", "", text)


def extract_text_from_image():
    image_path = "high_res_screenshot.png"  # Укажите путь к вашему изображению
    # Задайте координаты областей обрезки (left, upper, right, lower)
    crop_areas = [
        (75, 900, 200, 1900),
        (220, 900, 750, 1900),
        (945, 900, 1355, 1900),
        (1390, 900, 1560, 1900),
        (1730, 900, 1790, 1900),
        (1850, 900, 2032, 1900),
        (2035, 900, 2085, 1900),
        (2130, 900, 2385, 1900),
        (2410, 900, 2465, 1900),
    ]

    # Открываем изображение
    image = Image.open(image_path)

    all_texts = []

    for i, crop_area in enumerate(crop_areas):
        # Обрезаем изображение до заданной области
        cropped_image = image.crop(crop_area)

        # Улучшаем обрезанное изображение
        cropped_image = enhance_image(cropped_image)

        # Сохраняем обрезанное изображение для визуализации
        cropped_image_path = f"cropped_image_{i+1}.png"
        cropped_image.save(cropped_image_path)
        # Рисуем прямоугольник на оригинальном изображении для визуализации
        draw = ImageDraw.Draw(image)
        draw.rectangle(crop_area, outline="red", width=2)

        # Извлекаем текст с помощью Tesseract OCR
        custom_config = r"--oem 3 --psm 6"
        text = pytesseract.image_to_string(
            cropped_image, config=custom_config, lang="eng"
        )
        # Чистим текст и удаляем пустые строки
        cleaned_text = [clean_text(line) for line in text.strip().split("\n") if line]
        all_texts.append(cleaned_text)

    # Сохраняем изображение с нарисованной областью обрезки
    outlined_image_path = "outlined_image.png"
    image.save(outlined_image_path)

    # Создаем DataFrame для структурирования данных
    max_rows = max(len(column_texts) for column_texts in all_texts)
    data = {
        f"Текст из области {i+1}": column_texts + [""] * (max_rows - len(column_texts))
        for i, column_texts in enumerate(all_texts)
    }

    df = pd.DataFrame(data)

    # Сохраняем DataFrame в CSV файл с разделителем ;
    df.to_csv("extracted_texts.csv", index=False, sep=";", encoding="utf-8-sig")

    # # Выводим извлеченный текст из всех областей
    # for i, column_texts in enumerate(all_texts):
    #     print(f"Текст из области {i+1}:")
    #     for line in column_texts:
    #         print(line)
    #     print()


if __name__ == "__main__":
    pdf_path = "01.pdf"
    # save_high_resolution_screenshot(pdf_path)
    # anali_pdf_02(pdf_path, test_page_no=0)
    write_json(pdf_path, test_page_no=0)

    # extract_text_from_image()
