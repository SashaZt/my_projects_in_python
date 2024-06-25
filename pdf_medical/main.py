import pdfplumber
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import pandas as pd
import re
import json
import os
import shutil

# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")


def save_high_resolution_screenshot(pdf_path, page_no):
    resolution = 300
    # page_number = 0  # Номер страницы (начиная с 0)
    output_image_path = os.path.join(temp_path, "high_res_screenshot.png")
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_no]
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
        print(f"Скриншот сохранен для страницы: {page_no}")


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

    image_path = os.path.join(temp_path, "high_res_screenshot.png")

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

    all_texts = {}

    # Генерируем ключи начиная с 44
    image_keys = [str(44 + i) for i in range(len(crop_areas))]

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

        # Извлекаем текст с помощью Tesseract OCR
        custom_config = r"--oem 3 --psm 6"
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

    return data


def write_json(pdf_path):
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)

    os.makedirs(temp_path, exist_ok=True)
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

    results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            page_data = []
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
            if page_data or data_table:
                results.append(
                    {
                        f"Page:{page_no + 1}": {
                            "pdf_data": pdf_data_with_keys,
                            "image_data": data_table,
                        }
                    }
                )

    # Сохранение результатов в JSON файл
    with open("output.json", "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    pdf_path = "01.pdf"
    write_json(pdf_path)
