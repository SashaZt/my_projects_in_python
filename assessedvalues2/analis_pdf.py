import pdfplumber
import matplotlib.pyplot as plt
import camelot
import tabula
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import pdfplumber
import pytesseract
import numpy as np
import matplotlib.pyplot as plt

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def anali_pdf():
    pdf_path = "pdf1.pdf"

    with pdfplumber.open(pdf_path) as pdf:
        first_page = pdf.pages[0]  # Работаем только со второй страницей, индексация с 0

        # vertical_lines = [330, 430]  # Пример координат X для вертикальных линий
        # horizontal_lines = [190, 199, 205, 213, 221, 233]  # Пример координат Y для горизонтальных линий

        # table_settings = {
        #     "vertical_strategy": "explicit",
        #     "explicit_vertical_lines": vertical_lines,
        #     "horizontal_strategy": "explicit",
        #     "explicit_horizontal_lines": horizontal_lines,
        # }
        # tables = first_page.extract_tables(table_settings)  # Передаем table_settings в метод

        # Если вы хотите визуализировать расположение таблиц на странице:
        image = first_page.to_image()
        image.debug_tablefinder()
        # image.debug_tablefinder(table_settings)
        image.save("analis.png")

        # # Вывод таблицы (или таблиц)
        # for table in tables:
        #     for row in table:
        #         print(row)


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
                225,
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


def visualize_page_layout():
    pdf_path = "pdf1.pdf"
    grid_step = 10
    page_number = 0
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]

        # Получаем текст и позиции слов на странице
        words = page.extract_words()

        # Визуализация разметки страницы с сеткой
        plt.figure(figsize=(20, 20))

        # Рисуем сетку
        for x in range(0, int(page.width), grid_step):
            plt.axvline(x, color="gray", linestyle="--", linewidth=0.5)
        for y in range(0, int(page.height), grid_step):
            plt.axhline(y, color="gray", linestyle="--", linewidth=0.5)

        # Рисуем текстовые блоки и их границы
        for word in words:
            x0, y0, x1, y1 = word["x0"], word["top"], word["x1"], word["bottom"]
            plt.plot([x0, x1], [y0, y0], "r-")  # Верхняя линия
            plt.plot([x0, x1], [y1, y1], "r-")  # Нижняя линия
            plt.plot([x0, x0], [y0, y1], "r-")  # Левая линия
            plt.plot([x1, x1], [y0, y1], "r-")  # Правая линия

            plt.text(x0, y0, word["text"], fontsize=8, color="blue")

        # Устанавливаем метки на шкале
        plt.xticks(range(0, int(page.width), grid_step))
        plt.yticks(range(0, int(page.height), grid_step))

        plt.xlim(0, page.width)
        plt.ylim(page.height, 0)  # Инвертируем ось Y для правильного отображения
        plt.title(f"Page {page_number + 1} Layout with {grid_step}px Grid")
        plt.xlabel("X (pixels)")
        plt.ylabel("Y (pixels)")
        plt.show()


def extract_tables_with_camelot():
    pdf_path = "pdf1.pdf"
    tables = camelot.read_pdf(pdf_path, pages="1", flavor="stream")

    for i, table in enumerate(tables):
        print(f"Таблица №{i + 1}:")
        print(table.df)
        print("\n")

    # Сохранение таблиц в CSV
    tables.export("tables.csv", f="csv", compress=True)


def extract_tables_with_tabula():
    pdf_path = "pdf1.pdf"

    # Задаем параметры для извлечения таблиц
    read_options = {
        "pages": "1",  # Страницы для извлечения
        "multiple_tables": True,  # Извлечение нескольких таблиц
        "guess": False,  # Отключить автоматическое распознавание границ
        "area": [
            50,
            50,
            800,
            600,
        ],  # Указать координаты области [top, left, bottom, right]
        "columns": [150, 300, 450],  # Указать позиции вертикальных границ колонок
        "stream": True,  # Использовать метод потока для извлечения
    }

    tables = tabula.read_pdf(pdf_path, **read_options)

    for i, table in enumerate(tables):
        print(f"Таблица №{i + 1}:")
        print(table)
        print("\n")

    # Сохранение таблиц в CSV
    tabula.convert_into(pdf_path, "tables.csv", output_format="csv", pages="1")


def perform_ocr_on_image():
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )
    image_path = "high_res_screenshot.png"
    # Открываем изображение
    image = Image.open(image_path)
    # Используем Tesseract для распознавания текста
    text = pytesseract.image_to_string(image)
    print("Распознанный текст:")
    print(text)


def enhance_pdf():
    contrast = 1.5
    saturation = 1.5
    pdf_path = "pdf1.pdf"
    output_pdf_path = "enhanced_pdf1.pdf"

    # Указываем путь к утилите pdftoppm
    poppler_path = r"C:\poppler\Library\bin"

    # Конвертируем страницы PDF в изображения
    images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)

    enhanced_images = []
    for img in images:
        # Преобразуем изображение в RGB
        img = img.convert("RGB")

        # Повышаем контрастность
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast)

        # Повышаем насыщенность
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(saturation)

        enhanced_images.append(img)

    # Сохраняем улучшенные изображения обратно в PDF
    enhanced_images[0].save(
        output_pdf_path, save_all=True, append_images=enhanced_images[1:]
    )


# def anali_pdf_02():
#     enhance_pdf()
#     pdf_path = "enhanced_pdf1.pdf"
#     with pdfplumber.open(pdf_path) as pdf:
#         for page_no, page in enumerate(pdf.pages):
#             vertical_lines_05 = [19, 45, 225, 330, 380, 435, 488, 505, 580]
#             horizontal_lines_05 = [215, 225, 237, 250, 263, 273, 288, 297, 470]

#             table_settings = {
#                 "vertical_strategy": "text",
#                 # "explicit_vertical_lines": vertical_lines_05,
#                 "horizontal_strategy": "text",
#                 # "explicit_horizontal_lines": horizontal_lines_05,
#                 "snap_tolerance": 3,
#                 "join_tolerance": 3,
#                 "edge_min_length": 10,
#                 "min_words_vertical": 1,
#                 "min_words_horizontal": 1,
#             }

#             tables = page.extract_tables(table_settings)

#             for table_no, table in enumerate(tables):
#                 print(f"Страница №{page_no + 1}, Таблица №{table_no + 1}:")
#                 for row in table:
#                     print(row)
#                 print("\n")


#             image = page.to_image(resolution=300)
#             image.debug_tablefinder(table_settings)
#             image.save(f"analis_page_{page_no + 1}.png")
def img_cs2():
    import cv2
    import pytesseract
    import numpy as np

    # Путь к Tesseract
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    )

    # Загрузка изображения
    image_path = "high_res_screenshot.png"
    image = cv2.imread(image_path)

    # Преобразование изображения в оттенки серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Применение бинарного порога
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # Указание областей распознавания
    # vertical_lines = [78, 210, 940, 1380, 1580, 1820, 2028, 2110]
    vertical_lines = [78, 2110]
    horizontal_lines = [900, 940, 990, 1040]

    # Функция для извлечения текста из заданной области
    def extract_text_from_area(image, x0, y0, x1, y1):
        roi = image[y0:y1, x0:x1]
        text = pytesseract.image_to_string(roi, lang="eng")
        return text

    # Проход по всем областям и извлечение текста
    for i in range(len(vertical_lines) - 1):
        for j in range(len(horizontal_lines) - 1):
            x0, x1 = vertical_lines[i], vertical_lines[i + 1]
            y0, y1 = horizontal_lines[j], horizontal_lines[j + 1]
            text = extract_text_from_area(gray, x0, y0, x1, y1)
            # print(f"Area ({x0},{y0}) - ({x1},{y1}): {text}")
            print(text)

    # Рисуем красные линии на изображении
    for x in vertical_lines:
        cv2.line(image, (x, 0), (x, image.shape[0]), (0, 0, 255), 2)
    for y in horizontal_lines:
        cv2.line(image, (0, y), (image.shape[1], y), (0, 0, 255), 2)

    # Сохраняем изображение с линиями
    output_image_path = "image_with_lines.png"
    cv2.imwrite(output_image_path, image)
    # cv2.imshow("Lines", image)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()


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


def extract_text_with_opencv():
    pdf_path = "pdf1.pdf"
    resolution = 300
    page_number = 0  # Номер страницы (начиная с 0)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]
        image = page.to_image(resolution=resolution).original

        # Преобразуем изображение в оттенки серого
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

        # Применяем пороговое преобразование для увеличения контрастности
        _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

        # Поиск контуров
        contours, _ = cv2.findContours(
            binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Проход по всем контурам и извлечение текста
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            roi = gray[y : y + h, x : x + w]
            text = pytesseract.image_to_string(roi, lang="eng")
            # print(f"Text from area ({x},{y}) - ({x+w},{y+h}): {text}")
            print(text)
        # Визуализация контуров на изображении
        cv2.drawContours(np.array(image), contours, -1, (0, 0, 255), 2)
        output_image_path = "image_with_contours.png"
        cv2.imwrite(output_image_path, cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR))
        print(f"Контуры сохранены: {output_image_path}")

        # Визуализация с использованием matplotlib
        fig, ax = plt.subplots(figsize=(20, 20))
        ax.imshow(cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR))

        plt.show()


def extract_text_and_visualize_lines():
    pdf_path = "pdf1.pdf"
    resolution = 300
    page_number = 0  # Номер страницы (начиная с 0)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_number]

        # Извлекаем текстовые блоки
        words = page.extract_words()

        # Извлекаем весь текст
        full_text = page.extract_text()
        print("Extracted Text:")
        print(full_text)

        # Создаем изображение страницы с указанным разрешением
        image = page.to_image(resolution=resolution).original

        # Преобразуем изображение в RGB
        image = image.convert("RGB")

        # Создаем фигуру для визуализации
        fig, ax = plt.subplots(1, 1, figsize=(20, 20))
        ax.imshow(image)

        # Визуализация текстовых блоков
        for word in words:
            x0, y0, x1, y1 = word["x0"], word["top"], word["x1"], word["bottom"]
            ax.add_patch(
                plt.Rectangle(
                    (x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor="red", linewidth=1
                )
            )
            ax.text(x0, y0, word["text"], fontsize=8, color="red")

        plt.show()


if __name__ == "__main__":
    # anali_pdf()
    # anali_pdf_02()
    # visualize_page_layout()
    # extract_tables_with_camelot()
    # extract_tables_with_tabula()

    # perform_ocr_on_image()
    save_high_resolution_screenshot()
    # img_cs2()
    # extract_text_and_visualize_lines()
    # extract_text_with_opencv()
