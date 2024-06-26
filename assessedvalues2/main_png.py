from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
import pytesseract
import pdfplumber

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Улучшает качество
def save_high_resolution_screenshot():
    pdf_path = "pdf1.pdf"
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


def extract_text_from_image():
    image_path = "high_res_screenshot.png"  # Укажите путь к вашему изображению
    # Задайте координаты областей обрезки (left, upper, right, lower)
    crop_areas = [
        (75, 900, 200, 1900),
        (220, 900, 750, 1900),
        (945, 900, 1355, 1900),
        (1390, 900, 1560, 1900),
        (1730, 900, 1800, 1900),
        (1850, 900, 2100, 1900),
        (2130, 900, 2385, 1900),
        (2410, 900, 2465, 1900),
    ]
    # crop_areas = [(2410, 900, 2465, 1900)]

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
        all_texts.append(f"Текст из области {i+1}:\n{text}")

    # Сохраняем изображение с нарисованной областью обрезки
    outlined_image_path = "outlined_image.png"
    image.save(outlined_image_path)
    # Выводим извлеченный текст из всех областей
    for text in all_texts:
        print(text)


def anali_pdf_02():
    # enhance_pdf()
    pdf_path = "pdf1.pdf"
    # pdf_path = "enhanced_pdf1.pdf"
    with pdfplumber.open(pdf_path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            # Настройки для обнаружения таблиц
            vertical_lines_01 = [18, 192]
            vertical_lines_02 = [370, 599]
            vertical_lines_03 = [25, 580]
            vertical_lines_04 = [20, 600]

            horizontal_lines_01 = [
                15,
                25,
                40,
                51,
                63,
                76,
                88,
            ]
            horizontal_lines_02 = [
                15,
                28,
                40,
                51,
                63,
            ]
            horizontal_lines_03 = [
                62,
                75,
                90,
            ]
            horizontal_lines_04 = [100, 110, 120, 132, 160, 180]
            vertical_lines_05 = [18, 50, 200, 600]
            horizontal_lines_05 = [
                216,
                240,
                300,
            ]
            # Стратегии могут быть: "lines", "text", "explicit"
            table_settings = {
                "vertical_strategy": "explicit",
                "explicit_vertical_lines": vertical_lines_05,
                "horizontal_strategy": "explicit",
                "explicit_horizontal_lines": horizontal_lines_05,
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


if __name__ == "__main__":

    extract_text_from_image()
