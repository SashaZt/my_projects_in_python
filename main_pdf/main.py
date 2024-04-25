# https://github.com/UB-Mannheim/tesseract/wiki
import pdfplumber
import pytesseract
from pytesseract import Output
import os
from PIL import Image, ImageFilter, ImageEnhance
import cv2
import numpy as np
import pandas as pd
from io import StringIO


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def enhance_image(img):
    # Проверяем количество каналов в изображении
    if img.mode == "RGB":
        # Конвертируем в градации серого, если изображение цветное
        gray = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2GRAY)
    else:
        # Если изображение уже в градациях серого, используем его напрямую
        gray = np.array(img)
    # Применяем пороговое значение для бинаризации изображения
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    # Конвертируем обратно в PIL Image для дальнейшей обработки
    return Image.fromarray(binary)


def correct_skew(image_path):
    # Открываем изображение
    img = Image.open(image_path)
    # Улучшаем качество изображения через предварительную обработку
    img = enhance_image(img)
    # Используем pytesseract для определения угла наклона
    osd = pytesseract.image_to_osd(img, output_type=Output.DICT)
    # Получаем угол наклона
    skew_angle = osd["rotate"]
    # Поворачиваем изображение для коррекции наклона
    rotated = img.rotate(-1 * skew_angle, expand=True)
    # При желании применяем фильтр увеличения резкости
    sharpened = rotated.filter(ImageFilter.SHARPEN)
    # Сохраняем скорректированное и улучшенное изображение
    corrected_image_path = "corrected_" + os.path.basename(image_path)
    sharpened.save(corrected_image_path)
    return corrected_image_path


def save_pdf_pages_as_images(pdf_path, dpi=300):
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Извлекаем страницу как изображение с высоким DPI
            im = page.to_image(resolution=dpi)
            # Сохраняем страницу как изображение с высоким качеством
            image_path = f"page_{i}.png"
            im.save(image_path, format="PNG")


def rotate_img():
    # Загрузить изображение РАБОЧЕЕ
    image = cv2.imread("page_0.png", 0)

    # Загрузить изображение

    # Повернуть изображение на 90 градусов против часовой стрелки
    image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    # Выполнить обнаружение границ
    edges = cv2.Canny(image, 50, 150, apertureSize=3)

    # Выполнить преобразование Хафа для поиска линий на изображении
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    # Инициализировать список для хранения углов
    angles = []

    # Пройти по каждой линии
    for rho, theta in lines[0]:
        # Преобразовать уравнение линии в форму y = mx + b
        m = -np.cos(theta) / np.sin(theta)
        b = rho / np.sin(theta)

        # Вычислить угол линии и преобразовать его в градусы
        angle = np.arctan(m)
        angle = np.degrees(angle)

        # Добавить угол в список углов
        angles.append(angle)

    # Вычислить средний угол
    mean_angle = np.mean(angles)

    # Повернуть изображение для коррекции наклона
    height, width = image.shape
    center = (width // 2, height // 2)
    matrix = cv2.getRotationMatrix2D(center, mean_angle, 1)
    corrected_image = cv2.warpAffine(image, matrix, (width, height))

    # Сохранить скорректированное изображение
    cv2.imwrite("corrected_image.jpg", corrected_image)

    # Вывести сообщение об успешном выполнении
    print(
        "Изображение было успешно скорректировано и сохранено как corrected_image.jpg"
    )


def convert_image_to_pdf():
    input_image_path = "corrected_image.jpg"
    output_pdf_path = "corrected_image.pdf"
    image = Image.open(input_image_path)
    if image.mode != "RGB":
        image = image.convert("RGB")
    image.save(output_pdf_path, "PDF", resolution=100.0)


def paring_pdf():
    output_pdf_path = "corrected_image.pdf"
    with pdfplumber.open(output_pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                print(table)


def anali_pdf():
    import re

    input_image_path = "corrected_image.jpg"
    image = Image.open(input_image_path)

    # установка области для распознавания текста

    first_text_area = (180, 730, 3300, 870)
    second_text_area = (180, 870, 3300, 975)
    # text_area = (160, 580, 3300, 1500)

    # вырезание области изображения
    cropped_image = image.crop(second_text_area)
    # преобразование изображения в черно-белый формат
    cropped_image = cropped_image.convert("L")

    # улучшение контрастности
    enhancer = ImageEnhance.Contrast(cropped_image)
    # можно изменять коэффициент контрастности, чтобы достичь лучшего результата
    cropped_image = enhancer.enhance(4.0)
    # Удаление шума (медианный фильтр)
    cropped_image = cropped_image.filter(ImageFilter.MedianFilter(3))

    # Сглаживание (фильтр Гаусса)
    # cropped_image = cropped_image.filter(
    #     ImageFilter.GaussianBlur(radius=1)
    # )  # Отрегулируйте радиус размытия по своему усмотрению
    # сохранение обработанного изображения
    cropped_image.save("processed_image.png")
    cropped_image = Image.open("processed_image.png")

    # Распознавание текста с помощью Tesseract OCR
    bw = cropped_image.convert("1")
    custom_config = '--oem 3 --psm 10 -c tessedit_char_whitelist="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789, .!?@#$%^&*()_-+=[]{};:\'"'

    text = pytesseract.image_to_string(bw, lang="eng", config=custom_config)

    text_split = text.split()
    # row_00 = f"{text_split[0]} {text_split[1]}"
    # row_01 = text_split[2]
    # row_02 = f"{text_split[3]} {text_split[4]}"
    # row_03 = text_split[5]
    # row_04 = text_split[6]
    # row_05 = text_split[7]
    # row_06 = text_split[8]
    # row_07 = text_split[9]
    # row_08 = text_split[10]

    # all_rows = [row_00, row_01, row_02, row_03, row_04, row_05, row_06, row_07]
    print(text_split)


def extract_text_from_pdf():
    import re

    # Load the image from file
    image = Image.open("corrected_image.jpg")

    # Use pytesseract to do OCR on the image
    text = pytesseract.image_to_string(image)
    # Разделим текст на строки
    lines = text.strip().split("\n")

    # Заголовки для DataFrame возьмем из первой строки
    # Используем регулярные выражения для разделения слов в заголовках, где они разделены пробелами
    headers = re.split(r"\s{2,}", lines[0])

    # Теперь обработаем каждую строку после заголовков
    data = []
    for line in lines[1:]:
        # Очищаем и разделяем каждую строку на столбцы, предполагая, что два и более пробелов разделяют столбцы
        row = re.split(r"\s{2,}", line)
        if row:  # проверка на случай пустых строк
            data.append(row)

    # Создаем DataFrame
    df = pd.DataFrame(data, columns=headers)

    # Теперь у нас есть DataFrame `df`, который можно записать в CSV, как показано в предыдущем ответе

    # Чтобы убедиться, что код работает правильно, покажем первые строки DataFrame
    df.head()
    print(df)
    # # Assuming `text` is a string containing CSV formatted data
    # data = StringIO(text)

    # # Use pandas to read the CSV data
    # df = pd.read_csv(data, sep=r"\s+", engine="python")

    # # Now `df` is a pandas DataFrame that holds the data in tabular format
    # # Сохранение DataFrame в файл CSV
    # df.to_csv("output.csv", index=False, encoding="utf-8")


def split_headers(header_string):
    import re

    # Сначала очистим строку от частей, которые не нужны
    header_string = header_string.replace(
        "Start Cont Annualised Comm Init Commission Commission | Still to |", ""
    )
    header_string = header_string.replace("\n", " ")

    # Сделаем точные замены, чтобы разделить заголовки
    headers_corrected = re.sub(
        r"Client and Policy Date", "Client and Policy, StartDate", header_string
    )
    headers_corrected = re.sub(
        r"Freq Contribution", "CommFreq, Annualised Contribution", headers_corrected
    )
    headers_corrected = re.sub(r"Rate Prd", "Comm Init Rate Prd", headers_corrected)
    headers_corrected = re.sub(
        r"Issued Earned", "CommissionIssued, CommissionEarned", headers_corrected
    )
    headers_corrected = re.sub(
        r"Pay Remarks", "Still toPay, Remarks", headers_corrected
    )

    # Разделяем строку на список по запятой
    headers = [header.strip() for header in headers_corrected.split(",")]

    return headers


# Исходный текст заголовков
text = "Start Cont Annualised Comm Init Commission Commission | Still to | Client and Policy Date Freq Contribution Rate Prd Issued Earned Pay Remarks"

# Разделение на заголовки
headers = split_headers(text)

# Вывод результатов

if __name__ == "__main__":
    #     # save_pdf_pages_as_images("example.pdf")
    #     # rotate_img()
    #     # convert_image_to_pdf()
    anali_pdf()


# # Функция для определения угла наклона текста на изображении с помощью Hough Transform
# def get_skew_angle(cv_image):
#     # Переводим изображение в градации серого
#     gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
#     # Применяем фильтр Canny для обнаружения краёв
#     edges = cv2.Canny(gray, 50, 150, apertureSize=3)
#     # Применяем преобразование Хафа для поиска линий
#     lines = cv2.HoughLinesP(
#         edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10
#     )

#     # Вычисляем угол наклона каждой линии
#     angles = []
#     for line in lines:
#         x1, y1, x2, y2 = line[0]
#         angle = np.arctan2(y2 - y1, x2 - x1) * (180 / np.pi)
#         angles.append(angle)

#     # Фильтруем углы, чтобы убрать "шум" и находим средний угол
#     median_angle = np.median(angles)
#     print(median_angle)
#     return median_angle


# # # Функция для коррекции угла наклона изображения
# def correct_skew(cv_image, angle):
#     # Получаем размеры изображения
#     height, width = cv_image.shape[:2]
#     # Вычисляем центр изображения
#     center = (width // 2, height // 2)

#     # Выполняем поворот вокруг центра изображения
#     M = cv2.getRotationMatrix2D(center, angle, 1.0)
#     corrected_img = cv2.warpAffine(
#         cv_image,
#         M,
#         (width, height),
#         flags=cv2.INTER_CUBIC,
#         borderMode=cv2.BORDER_REPLICATE,
#     )

#     return corrected_img


# # Загружаем изображение
# image = cv2.imread("corrected_temp_page_0.png")

# # Определяем угол наклона
# skew_angle = get_skew_angle(image)

# # Переворачиваем изображение горизонтально
# flipped_image = cv2.flip(image, 1)

# # Выравниваем изображение по уровню
# (h, w) = flipped_image.shape[:2]
# center = (w // 2, h // 2)

# # Вращаем изображение вокруг центра
# rotation_matrix = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
# rotated_image = cv2.warpAffine(flipped_image, rotation_matrix, (w, h))

# # Сохраняем выровненное изображение
# cv2.imwrite("aligned_image.jpg", rotated_image)
