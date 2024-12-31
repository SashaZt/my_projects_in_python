import json
import re
import shutil
from datetime import datetime
from pathlib import Path

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
    custom_config = r"--oem 3 --psm 7 tessedit_char_whitelist=0123456789-"

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


def save_cropped_image(image_path, coordinates_json, output_path):
    """
    Вырезает область изображения, указанную в coordinates_json, и сохраняет её.
    """
    with open(coordinates_json, "r", encoding="utf-8") as f:
        coordinates = json.load(f)

    image = cv2.imread(image_path)
    x, y, w, h = coordinates["x"], coordinates["y"], coordinates["w"], coordinates["h"]
    cropped_image = image[y : y + h, x : x + w]

    # Сохраняем вырезанное изображение
    cv2.imwrite(output_path, cropped_image)
    print(f"Вырезанное изображение сохранено в {output_path}")


def extract_correct_date(white_text, black_text):
    """
    Берёт часть текста до дефиса из white_text и часть текста после дефиса из black_text.
    """
    # Извлекаем первую часть из white_text
    white_part = white_text.split("-")[0] if "-" in white_text else white_text

    # Извлекаем вторую часть из black_text
    black_part = black_text.split("-")[-1] if "-" in black_text else black_text

    # Формируем итоговый текст
    return f"{white_part}-{black_part}"


def combine_texts(image_path):
    """
    Распознаёт текст и извлекает корректный формат даты.
    """
    white_text = recognize_white_text(image_path)
    print("Белый текст:", white_text)

    black_text = recognize_black_text(image_path)
    print("Чёрный текст:", black_text)

    return extract_correct_date(white_text, black_text)


def extract_first_frame(video_path, output_image_path):
    cap = cv2.VideoCapture(video_path)
    success, frame = cap.read()
    if success:
        cv2.imwrite(output_image_path, frame)
    cap.release()


def create_folder_and_move_file(text, year="2024", file_path="hiv00231.mp4"):
    """
    Создаёт папку на основе текста в формате DD-MM и перемещает файл в эту папку.
    :param text: Текст в формате DD-MM (например, '13-12').
    :param year: Год, который будет добавлен к имени папки.
    :param file_path: Путь к файлу, который нужно переместить.
    """
    try:
        # Преобразуем текст в формат даты (день-месяц)
        date_obj = datetime.strptime(text, "%d-%m")
        folder_name = date_obj.strftime(f"%d.%m.{year}")

        # Создаём папку
        folder_path = Path(folder_name)
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Папка '{folder_path}' успешно создана.")

        # Перемещаем файл в созданную папку
        file_to_move = Path(file_path)
        if file_to_move.exists():
            destination = folder_path / file_to_move.name
            shutil.move(str(file_to_move), str(destination))
            print(f"Файл '{file_to_move.name}' перемещён в папку '{folder_path}'.")
        else:
            print(f"Файл '{file_to_move}' не найден.")
    except ValueError as e:
        print(f"Ошибка преобразования текста в дату: {e}")
    except Exception as e:
        print(f"Ошибка при перемещении файла: {e}")


def split_coordinates(coordinates):
    """
    Делит указанные координаты на две части по ширине.
    :param coordinates: Словарь с координатами (x, y, w, h).
    :return: Две области координат.
    """
    mid_x = coordinates["x"] + coordinates["w"] // 2

    # Первая часть (левая область)
    first = {
        "x": coordinates["x"],
        "y": coordinates["y"],
        "w": coordinates["w"] // 2,
        "h": coordinates["h"],
    }

    # Вторая часть (правая область)
    second = {
        "x": mid_x,
        "y": coordinates["y"],
        "w": coordinates["w"] // 2,
        "h": coordinates["h"],
    }
    return first, second


def recognize_text_by_type(image_path, coordinates, text_type):
    """
    Распознаёт текст из области на основе указанного типа (белый или чёрный).
    :param image_path: Путь к изображению.
    :param coordinates: Координаты области (x, y, w, h).
    :param text_type: Тип текста ('white' или 'black').
    :return: Распознанный текст.
    """
    image = cv2.imread(image_path)
    x, y, w, h = coordinates["x"], coordinates["y"], coordinates["w"], coordinates["h"]
    cropped_image = image[y : y + h, x : x + w]

    # Преобразуем в grayscale
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

    if text_type == "white":
        # Для белого текста: бинаризация обычным способом
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    elif text_type == "black":
        # Для чёрного текста: инверсия и бинаризация
        inverted = cv2.bitwise_not(gray)
        thresh = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    else:
        raise ValueError("Неверный тип текста: укажите 'white' или 'black'.")

    # Конфигурация Tesseract
    custom_config = r"--oem 3 --psm 7 tessedit_char_whitelist=0123456789-"

    # Распознаём текст
    text = pytesseract.image_to_string(Image.fromarray(thresh), config=custom_config)
    return text.strip()


def process_two_areas(image_path, coordinates, area_types):
    """
    Обрабатывает две области изображения на основе их типов.
    :param image_path: Путь к изображению.
    :param coordinates: Координаты для разделения на две области.
    :param area_types: Список типов текста для каждой области (например, ['white', 'black']).
    :return: Тексты из обеих областей.
    """
    # Делим координаты на две области
    first_area, second_area = split_coordinates(coordinates)

    # Распознаём текст в первой области
    first_text = recognize_text_by_type(image_path, first_area, area_types[0])
    print(first_text)
    # if first_text == "(9-":
    #     first_text = "09"
    print(f"Текст из первой области ({area_types[0]}): {first_text}")

    # Распознаём текст во второй области
    second_text = recognize_text_by_type(image_path, second_area, area_types[1])
    print(second_text)
    # if second_text == "la" or "17":
    #     second_text = "12"
    print(f"Текст из второй области ({area_types[1]}): {second_text}")

    return first_text, second_text


if __name__ == "__main__":
    video_path = "hiv00009.mp4"
    output_image_path = "first_frame.png"
    # coordinates_json = "coordinates.json"
    # image_path = "cropped_image.png"
    extract_first_frame(video_path, output_image_path)

    # save_cropped_image(output_image_path, coordinates_json, image_path)
    # # Путь к изображению

    # # Распознавание и извлечение корректного текста
    # final_text = combine_texts(image_path)
    # create_folder_and_move_file(final_text, file_path=video_path)

    # print("Объединённый текст:", final_text)
    coordinates = {"x": 60, "y": 61, "w": 163, "h": 59}  # Ваши координаты
    area_types = [
        "white",
        "white",
    ]  # Типы текста: первая область - белая, вторая - чёрная
    # Обработка двух областей
    first_text, second_text = process_two_areas(
        output_image_path, coordinates, area_types
    )

    # Объединение текста в нужный формат
    final_text = f"{first_text.split('-')[0]}-{second_text.split('-')[-1]}"
    print("Итоговый текст:", final_text)
    create_folder_and_move_file(final_text, file_path=video_path)
