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
    image_keys = [str(42 + i) for i in range(len(crop_areas))]

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
        1: ([18, 193], [15, 25, 40, 51, 63]),
        2: ([193, 368], [15, 25, 40, 51, 63]),
        3: ([390, 505, 510], [15, 28]),
        3.1: ([390, 505, 510], [28, 40]),
        4: ([550, 560, 595], [28, 40]),
        5: ([370, 375, 440], [51, 63]),
        6: ([440, 490, 537], [51, 63]),
        7: ([537, 539, 595], [51, 63]),
        8: ([25, 580], [62, 75, 88]),
        9: ([18, 76, 80], [98, 110]),
        10: ([82, 98, 103], [98, 110]),
        11: ([103, 141, 146], [98, 110]),
        12: ([143, 148, 165], [98, 110]),
        13: ([162, 167, 186], [98, 110]),
        14: ([184, 189, 207], [98, 110]),
        15: ([203, 208, 228], [98, 110]),
        16: ([223, 228, 250], [98, 110]),
        17: ([247, 252, 270], [98, 110]),
        18: ([268, 273, 292], [98, 110]),
        19: ([290, 295, 313], [98, 110]),
        20: ([310, 315, 335], [98, 110]),
        21: ([330, 335, 355], [98, 110]),
        22: ([352, 357, 375], [98, 110]),
        23: ([20, 40, 80], [120, 132]),
        24: ([88, 110, 157], [120, 132]),
        25: ([300, 318, 368, 415], [120, 132]),
        26: ([20, 150, 158], [145, 158]),
        27: ([320, 340, 410], [156, 170]),
        28: ([410, 432, 502], [156, 170]),
        29: ([502, 522, 595], [156, 170]),
        30: ([18, 50, 90, 105, 145, 330, 380, 450, 510], [470, 485]),
        31: ([18, 175, 180], [495, 530]),
        32: ([180, 280, 285], [495, 530]),
        33: ([283, 298, 303], [495, 530]),
        34: ([300, 308, 320], [495, 530]),
        35: ([320, 325, 390], [495, 530]),
        36: ([390, 395, 467], [495, 530]),
        37: ([487, 590, 595], [482, 495]),
        38: ([487, 590, 595], [495, 530]),
        39: ([18, 195, 200], [542, 575]),
        40: ([195, 200, 220], [542, 575]),
        41: ([220, 357, 362], [542, 575]),
        42: (
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
        43: (
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
        44: ([45, 90, 95], [647, 660]),
        45: ([420, 500, 505], [660, 672]),
        46: ([385, 490, 495], [672, 682]),
        47: ([515, 580, 585], [672, 682]),
        48: ([200, 215, 285], [705, 720]),
    }

    def flatten_data(nested_list):
        # Объединяем все строки в один список, игнорируя пустые строки
        return [
            " ".join(
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
                "01",
                "02",
                "3a",
                "3b",
                "04",
                "05",
                "06",
                "09",
                "10",
                "11",
                "12",
                "13",
                "14",
                "15",
                "16",
                "17",
                "18",
                "19",
                "20",
                "21",
                "22",
                "23",
                "31",
                "32",
                "35",
                "38",
                "39",
                "40",
                "41",
                "23t",
                "50",
                "51",
                "52",
                "53",
                "54",
                "55",
                "56",
                "57",
                "58",
                "59",
                "60",
                "66",
                "67",
                "69",
                "76",
                "76L",
                "76F",
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
