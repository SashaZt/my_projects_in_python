from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from configuration.logger_setup import logger
import json
import wordninja
import argparse
import re
import pytesseract
from collections import defaultdict
import pdfplumber
import platform
import time
from pathlib import Path
import pdfplumber
from dotenv import dotenv_values

from configuration.configurat import TEMP_PATH, JSON_PATH, PDF_PATH, LOG_PATH


# Используем пути из config.py
temp_directory = Path(TEMP_PATH)
json_directory = Path(JSON_PATH)
pdf_directory = Path(PDF_PATH)
log_directory = Path(LOG_PATH)

# Создаём директории, если их нет
temp_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
pdf_directory.mkdir(parents=True, exist_ok=True)
log_directory.mkdir(parents=True, exist_ok=True)


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"


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
    threshold = 128
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


# РАБОЧИЙ ВАРИАНТ полностью
def process_image(pdf_path, output_path, temp_path, scale_factor):
    # Итоговый словарь для всех страниц
    final_result = {}
    # Коэффициент масштабирования
    scale_factor = 1  # Увеличение на 1.1
    # Открываем PDF с помощью pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            # logger.info(page_no)
            logger.info(page)
            Path(temp_path).mkdir(parents=True, exist_ok=True)

            image_path = save_high_resolution_screenshot(pdf_path, page_no, temp_path)

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
                "11": [(341, 413, 420, 458)],
                "12": [(427, 411, 600, 461)],
                "13": [(605, 410, 690, 460)],
                "14": [(695, 412, 772, 458)],
                "15": [(780, 410, 865, 460)],
                "16": [(870, 410, 950, 460)],
                "17": [(955, 410, 1040, 460)],
                "31a": [(78, 510, 160, 560)],
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
                "39b": [(1550, 660, 1652, 845)],
                "39c": [(1657, 660, 1708, 845)],
                "40a": [(1717, 660, 1793, 845)],
                "40b": [(1805, 660, 2030, 845)],
                "40c": [(2040, 660, 2088, 845)],
                "41": [(2100, 660, 2175, 845)],
                "41a": [(2190, 660, 2405, 845)],
                "41b": [(2412, 660, 2465, 845)],
                "42_1": [(75, 900, 200, 940)],
                "42_2": [(75, 940, 200, 1000)],
                "42_3": [(75, 1000, 200, 1040)],
                "42_4": [(75, 1040, 200, 1100)],
                "42_5": [(75, 1100, 200, 1140)],
                "42_6": [(75, 1140, 200, 1200)],
                "42_7": [(75, 1200, 200, 1240)],
                "42_8": [(75, 1240, 200, 1300)],
                "43_1": [(220, 900, 940, 940)],
                "43_2": [(220, 940, 940, 1000)],
                "43_3": [(220, 1000, 940, 1040)],
                "43_4": [(220, 1040, 940, 1100)],
                "43_5": [(220, 1100, 940, 1140)],
                "43_6": [(220, 1140, 940, 1200)],
                "43_7": [(220, 1200, 940, 1240)],
                "43_8": [(220, 1240, 940, 1300)],
                "44_1": [(945, 900, 1370, 940)],
                "44_2": [(945, 940, 1370, 1000)],
                "44_3": [(945, 1000, 1370, 1040)],
                "44_4": [(945, 1040, 1370, 1100)],
                "44_5": [(945, 1100, 1370, 1140)],
                "44_6": [(945, 1140, 1370, 1200)],
                "44_7": [(945, 1200, 1370, 1240)],
                "44_8": [(945, 1240, 1370, 1300)],
                "45_1": [(1380, 900, 1575, 940)],
                "45_2": [(1390, 940, 1560, 1000)],
                "45_3": [(1390, 1000, 1560, 1040)],
                "45_4": [(1390, 1040, 1560, 1100)],
                "45_5": [(1390, 1100, 1560, 1140)],
                "45_6": [(1390, 1140, 1560, 1200)],
                "45_7": [(1390, 1200, 1560, 1240)],
                "45_8": [(1390, 1240, 1560, 1300)],
                "46_1": [(1730, 900, 1790, 940)],
                "46_2": [(1730, 940, 1790, 1000)],
                "46_3": [(1730, 1000, 1790, 1040)],
                "46_4": [(1730, 1040, 1790, 1100)],
                "46_5": [(1730, 1100, 1790, 1140)],
                "46_6": [(1730, 1140, 1790, 1200)],
                "46_7": [(1730, 1200, 1790, 1240)],
                "46_8": [(1730, 1240, 1790, 1300)],
                "47_1": [(1850, 900, 2030, 940)],
                "47_2": [(1850, 940, 2030, 1000)],
                "47_3": [(1850, 1000, 2030, 1040)],
                "47_4": [(1850, 1040, 2030, 1100)],
                "47_5": [(1850, 1100, 2030, 1140)],
                "47_6": [(1850, 1140, 2030, 1200)],
                "47_7": [(1850, 1200, 2030, 1240)],
                "47_8": [(1850, 1240, 2030, 1300)],
                "47a_1": [(2032, 900, 2085, 940)],
                "47a_2": [(2032, 940, 2085, 1000)],
                "47a_3": [(2032, 1000, 2085, 1040)],
                "47a_4": [(2032, 1040, 2085, 1100)],
                "47a_5": [(2032, 1100, 2085, 1140)],
                "47a_6": [(2032, 1140, 2085, 1200)],
                "47a_7": [(2032, 1200, 2085, 1240)],
                "47a_8": [(2032, 1240, 2085, 1300)],
                # "47a": [(2032, 901, 2085, 1900)],
                "28": [(78, 1965, 180, 2000)],
                "gre_dat": [(1400, 1967, 1560, 2000)],
                "totals_1": [(1905, 1968, 2030, 2000)],
                "totals_2": [(2040, 1968, 2100, 2000)],
                "50": [(75, 2060, 700, 2120)],
                "51": [(760, 2065, 1150, 2120)],
                "52": [(1200, 2070, 1230, 2120)],
                "53": [(1290, 2070, 1320, 2120)],
                "55": [(1760, 2065, 1888, 2110)],
                "55a": [(1895, 2065, 1944, 2120)],
                "56": [(2040, 2015, 2400, 2060)],
                "58": [(75, 2260, 800, 2300)],
                "59": [(835, 2260, 910, 2300)],
                "60": [(925, 2260, 1400, 2300)],
                "63": [(75, 2455, 900, 2550)],
                "66": [(105, 2600, 340, 2645)],
                "66a": [(340, 2600, 575, 2645)],
                "66b": [(580, 2600, 804, 2645)],
                "66c": [(810, 2600, 1042, 2645)],
                "66d": [(1045, 2600, 1275, 2645)],
                "66e": [(1280, 2600, 1505, 2645)],
                "66f": [(1510, 2600, 1738, 2645)],
                "66g": [(1745, 2600, 1975, 2645)],
                "66h": [(1980, 2600, 2210, 2645)],
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
                    scaled_area = scale_crop_area(crop_area, scale_factor)
                    # Передаем кортеж, а не список
                    # Обрезаем изображение до заданной области
                    cropped_image = image.crop(scaled_area)
                    # Улучшаем обрезанное изображение
                    cropped_image = enhance_image(cropped_image)
                    # Сохраняем обрезанное изображение для визуализации
                    filename_cropped_image = (
                        temp_path / f"cropped_image_{key}_{i+1}.png"
                    )

                    cropped_image.save(filename_cropped_image)

                    # Рисуем прямоугольник на оригинальном изображении для визуализации
                    draw = ImageDraw.Draw(image)
                    draw.rectangle(crop_area, outline="red", width=2)

                    # Все символы, включая буквы, цифры и специальные символы
                    # whitelist = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,."

                    # custom_config = f"--oem 3 --psm 6 -c tessedit_char_whitelist={whitelist} -c preserve_interword_spaces=1"

                    # Извлекаем текст из обрезанного изображения
                    # text = pytesseract.image_to_string(
                    #     cropped_image, config=custom_config, lang="eng"
                    # )
                    keys_all_text = [
                        "11",
                        "14",
                        "15",
                        "35a",
                        "39a",
                        "39b",
                        "39c",
                        "43_1",
                        "43_2",
                        "43_3",
                        "43_4",
                        "43_5",
                        "43_6",
                        "43_7",
                        "43_8",
                        "44_1",
                        "44_2",
                        "44_3",
                        "44_4",
                        "44_5",
                        "44_6",
                        "44_7",
                        "44_8",
                        "46_1",
                        "46_2",
                        "46_3",
                        "46_4",
                        "46_5",
                        "46_6",
                        "46_7",
                        "46_8",
                        "47_1",
                        "47_2",
                        "47_3",
                        "47_4",
                        "47_5",
                        "47_6",
                        "47_7",
                        "47_8",
                        "47a_1",
                        "47a_2",
                        "47a_3",
                        "47a_4",
                        "47a_5",
                        "47a_6",
                        "47a_7",
                        "47a_8",
                        "gre_dat",
                        "totals_1",
                        "totals_2",
                        "52",
                        "53",
                        "55a",
                        "59",
                    ]
                    keys_all_digital = [
                        "3b",
                        "4",
                        "5",
                        "6a",
                        "6b",
                        "9d",
                        "10",
                        "12",
                        "13",
                        "14",
                        "15",
                        "16",
                        "17",
                        "31a",
                        "35a",
                        "35b",
                        "35c",
                        "42_1",
                        "42_2",
                        "42_3",
                        "42_4",
                        "42_5",
                        "42_6",
                        "42_7",
                        "42_8",
                        "45_1",
                        "45_2",
                        "45_3",
                        "45_4",
                        "45_5",
                        "45_6",
                        "45_7",
                        "45_8",
                    ]
                    if key in keys_all_text:
                        # Все символы, включая буквы, цифры и специальные символы
                        whitelist = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,."

                        custom_config = f"--oem 3 --psm 6 -c tessedit_char_whitelist={whitelist} -c preserve_interword_spaces=1"

                        text = pytesseract.image_to_string(
                            cropped_image, config=custom_config, lang="eng"
                        )
                    elif key in keys_all_digital:
                        text = pytesseract.image_to_string(
                            cropped_image, config="digits"
                        )
                    else:
                        text = pytesseract.image_to_string(cropped_image)

                    logger.info(f"Срез {key}")
                    logger.info(f"Текст {text}")

                    cleaned_text = [
                        clean_text(line) for line in text.strip().split("\n") if line
                    ]
                    # logger.info(f"Очищенный текст {cleaned_text}")

                    # Очистка и проверка текста
                    # cleaned_text = validity_text(cleaned_text)
                    # logger.info(f"Результирующие данные: {cleaned_text}")

                    # Сохраняем результат в all_texts
                    if key not in all_texts:
                        all_texts[key] = []
                    all_texts[key].extend(cleaned_text)

            # Сохраняем изображение с нарисованной областью обрезки
            filename_outlined = temp_path / "outlined_image.png"

            image.save(filename_outlined)

            # Проверяем, есть ли данные в all_texts перед созданием DataFrame
            if all_texts:
                max_rows = max(len(column_texts) for column_texts in all_texts.values())
                data = defaultdict(list)
                # Используем defaultdict для автоматического создания списков

                for key, column_texts in all_texts.items():

                    # Убираем пустые строки
                    # cleaned_texts = [text for text in column_texts if text.strip()]
                    cleaned_texts = column_texts  # Без изменения списка

                    # if cleaned_texts:
                    # logger.info(cleaned_texts)
                    # Если есть непустые строки, добавляем их в data
                    data[key].extend(cleaned_texts)

                # Приводим data к обычному словарю для вывода
                data = dict(data)
                # logger.info(data)
                # Добавляем результат для текущей страницы в итоговый словарь
                final_result[f"Page:{page_no + 1}"] = data

            else:
                logger.error(f"Нет данных для обработки на странице {page_no + 1}.")
                final_result[f"Page:{page_no + 1}"] = {}

    # Сохранение всех результатов в JSON файл
    with open(output_path, "w", encoding="utf-8") as json_file:
        json.dump(final_result, json_file, ensure_ascii=False, indent=4)


def save_high_resolution_screenshot(pdf_path, page_no, temp_path):

    resolution = 300
    # page_number = 0  # Номер страницы (начиная с 0)
    output_image_path = temp_path / "high_res_screenshot.png"

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
        print(f"Скриншот сохранен: {output_image_path}")
    return output_image_path


def main():
    # Создаем парсер аргументов
    parser = argparse.ArgumentParser(description="PDF analysis script")
    parser.add_argument("pdf_filename", help="PDF file name")
    parser.add_argument("output_filename", help="Output JSON file name")
    parser.add_argument(
        "scale_factor", type=float, help="Scaling factor for image processing"
    )

    args = parser.parse_args()

    # Определяем пути для различных операционных систем и устанавливаем путь к Tesseract
    pdf_directory = Path(PDF_PATH)
    json_directory = Path(JSON_PATH)

    if platform.system() == "Linux":
        # Формируем пути к PDF и JSON файлам на основе аргументов
        pdf_path = pdf_directory / args.pdf_filename
        output_path = json_directory / args.output_filename
        pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
    elif platform.system() == "Windows":
        # Формируем пути к PDF и JSON файлам на основе аргументов
        pdf_path = pdf_directory / args.pdf_filename
        output_path = json_directory / args.output_filename
        pytesseract.pytesseract.tesseract_cmd = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        )
    else:
        print("Unsupported operating system")
        return

    # current_directory = Path.cwd()
    timestamp = str(int(time.time()))
    temp_path = Path(temp_directory) / timestamp

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
