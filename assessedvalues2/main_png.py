from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


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


def extract_text_from_image(image_path, crop_area):
    """
    Извлекает текст из определенной области изображения и сохраняет изображения.

    :param image_path: Путь к изображению
    :param crop_area: Область обрезки (left, upper, right, lower)
    """
    # Открываем изображение
    image = Image.open(image_path)

    # Обрезаем изображение до заданной области
    cropped_image = image.crop(crop_area)

    # Улучшаем обрезанное изображение
    cropped_image = enhance_image(cropped_image)

    # Сохраняем обрезанное изображение для визуализации
    cropped_image_path = "cropped_image.png"
    cropped_image.save(cropped_image_path)
    print(f"Обрезанное изображение сохранено как {cropped_image_path}")

    # Рисуем прямоугольник на оригинальном изображении для визуализации
    draw = ImageDraw.Draw(image)
    draw.rectangle(crop_area, outline="red", width=2)
    outlined_image_path = "outlined_image.png"
    image.save(outlined_image_path)
    print(
        f"Изображение с нарисованной областью обрезки сохранено как {outlined_image_path}"
    )

    # Извлекаем текст с помощью Tesseract OCR
    custom_config = r"--oem 3 --psm 6"
    text = pytesseract.image_to_string(cropped_image, config=custom_config, lang="eng")

    # Выводим извлеченный текст
    print("Извлеченный текст из указанной области:")
    print(text)


if __name__ == "__main__":
    image_path = "high_res_screenshot.png"  # Укажите путь к вашему изображению
    # Задайте координаты области обрезки (left, upper, right, lower)
    crop_area = (220, 990, 750, 1050)  # Пример координат
    extract_text_from_image(image_path, crop_area)
