import json

import cv2
import pytesseract

# Укажите путь к исполняемому файлу Tesseract, если он не добавлен в PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_image(image_path, coordinates):
    image = cv2.imread(image_path)
    x, y, w, h = coordinates["x"], coordinates["y"], coordinates["w"], coordinates["h"]
    cropped_image = image[y : y + h, x : x + w]

    # Преобразуем в оттенки серого
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

    # Увеличиваем контрастность
    enhanced = cv2.equalizeHist(gray)

    # Адаптивная бинаризация
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Увеличиваем масштаб изображения
    resized = cv2.resize(binary, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    return resized


def save_cropped_image(image_path, coordinates_json, output_path):
    """
    Вырезает область изображения, указанную в coordinates_json, и сохраняет её.
    """
    with open(coordinates_json, "r") as f:
        coordinates = json.load(f)

    image = cv2.imread(image_path)
    x, y, w, h = coordinates["x"], coordinates["y"], coordinates["w"], coordinates["h"]
    cropped_image = image[y : y + h, x : x + w]

    # Сохраняем вырезанное изображение
    cv2.imwrite(output_path, cropped_image)
    print(f"Вырезанное изображение сохранено в {output_path}")


def extract_date_from_image_with_saved_coordinates(image_path, coordinates_json):
    with open(coordinates_json, "r") as f:
        coordinates = json.load(f)

    preprocessed_image = preprocess_image(image_path, coordinates)
    # Распознаем текст
    text = pytesseract.image_to_string(
        preprocessed_image, config="--psm 7 -c tessedit_char_whitelist=0123456789-"
    )

    return text


image_path = "first_frame.png"
coordinates_json = "coordinates.json"
output_cropped_path = "cropped_image.png"

# Сохранение вырезанного изображения
save_cropped_image(image_path, coordinates_json, output_cropped_path)


# # Распознавание текста с использованием сохранённых координат
# recognized_text = extract_date_from_image_with_saved_coordinates(
#     image_path, coordinates_json
# )
# print("Распознанный текст:", recognized_text)


# # Увеличьте контраст изображения
# enhancer = ImageEnhance.Contrast(image)
# image = enhancer.enhance(2.0)  # Увеличение контраста в два раза

# # Преобразуйте изображение в черно-белое для улучшения распознавания
# image = image.convert("L")  # Конвертация в оттенки серого

# # Используйте pytesseract для распознавания текста
# text = pytesseract.image_to_string(image)

# text = pytesseract.image_to_string(image, config=custom_config)
# # Выведите распознанный текст
# print("Распознанный текст:", text)

# import cv2
# import numpy as np
# import pytesseract
# from PIL import Image, ImageEnhance

# # Указание пути к Tesseract
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# # Загрузка изображения
# image_path = "cropped_image.png"
# image = Image.open(image_path)

# # Конвертация в формат, подходящий для OpenCV
# open_cv_image = np.array(image)
# open_cv_image = open_cv_image[:, :, ::-1].copy()

# # Создание маски для черного текста
# _, black_mask = cv2.threshold(
#     cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY), 245, 255, cv2.THRESH_BINARY_INV
# )

# # Применение маски к изображению
# black_text = cv2.bitwise_and(open_cv_image, open_cv_image, mask=black_mask)

# # Применение бинаризации по Оцу
# gray = cv2.cvtColor(black_text, cv2.COLOR_BGR2GRAY)
# thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

# # Конвертация обратно в PIL Image для распознавания
# image_black_text = Image.fromarray(thresh)
# custom_config = r"--oem 3 --psm 7 tessedit_char_whitelist=0123456789-"

import re

# # Распознавание текста
# text_black = pytesseract.image_to_string(image_black_text, config=custom_config)
# print("Распознанный черный текст:", text_black)
import cv2
import numpy as np
import pytesseract
from PIL import Image

# Указание пути к Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def recognize_white_text(image_path):
    """
    Распознаёт белый текст на изображении.
    """
    img = Image.open(image_path)

    # Преобразование в grayscale и бинаризация
    gray = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Конфигурация для Tesseract
    custom_config = r"--oem 3 --psm 6 tessedit_char_whitelist=0123456789-"

    # Распознавание текста
    text = pytesseract.image_to_string(Image.fromarray(thresh), config=custom_config)
    return text.strip()


def recognize_black_text(image_path):
    """
    Распознаёт чёрный текст на изображении.
    """
    image = Image.open(image_path)

    # Конвертация в формат OpenCV
    open_cv_image = np.array(image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()

    # Создание маски для чёрного текста
    _, black_mask = cv2.threshold(
        cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY), 245, 255, cv2.THRESH_BINARY_INV
    )

    # Применение маски к изображению
    black_text = cv2.bitwise_and(open_cv_image, open_cv_image, mask=black_mask)

    # Преобразование в grayscale и бинаризация
    gray = cv2.cvtColor(black_text, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Конвертация обратно в PIL Image
    image_black_text = Image.fromarray(thresh)
    custom_config = r"--oem 3 --psm 7 tessedit_char_whitelist=0123456789-"

    # Распознавание текста
    text = pytesseract.image_to_string(image_black_text, config=custom_config)
    return text.strip()


def extract_digits_and_dashes(white_text, black_text):
    """
    Извлекает только цифры и дефисы из объединённого текста.
    """
    # Объединяем белый и чёрный текст
    combined_text = f"{white_text}{black_text}"

    # Извлекаем только цифры и дефисы
    filtered_text = "".join(re.findall(r"[0-9-]+", combined_text))
    return filtered_text


def combine_texts(image_path):
    """
    Распознаёт текст и извлекает только цифры и дефисы.
    """
    white_text = recognize_white_text(image_path)
    print(white_text)
    black_text = recognize_black_text(image_path)
    print(black_text)
    return extract_digits_and_dashes(white_text, black_text)


# Путь к изображению
image_path = "cropped_image.png"

# Распознавание и извлечение только цифр и дефисов
final_text = combine_texts(image_path)
print("Объединённый текст:", final_text)
