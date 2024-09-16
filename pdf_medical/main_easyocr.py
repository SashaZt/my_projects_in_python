import easyocr
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from pathlib import Path


# Функция для масштабирования области
def scale_crop_area(crop_area, scale_factor):
    # Убедимся, что crop_area имеет 4 элемента
    if len(crop_area) != 4:
        raise ValueError(
            "crop_area должен содержать ровно 4 элемента: (left, top, right, bottom)"
        )
    return tuple(int(coord * scale_factor) for coord in crop_area)


# Функция для улучшения изображения
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


# Создаем объект EasyOCR Reader
reader = easyocr.Reader(["en", "ru"], gpu=False)

# Ваши области обрезки
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
    "66_1": [(108, 2605, 130, 2643)],
    "66_2": [(130, 2605, 310, 2643)],
    "66_3": [(310, 2605, 340, 2643)],
    "66a_1": [(342, 2602, 366, 2645)],
    "66a_2": [(366, 2602, 540, 2645)],
    "66a_3": [(540, 2602, 572, 2645)],
    "66b_1": [(580, 2600, 605, 2645)],
    "66b_2": [(605, 2602, 780, 2645)],
    "66b_3": [(780, 2602, 805, 2645)],
    "66c_1": [(810, 2600, 840, 2645)],
    "66c_2": [(840, 2602, 1010, 2645)],
    "66c_3": [(1010, 2602, 1040, 2645)],
    "66d_1": [(1050, 2600, 1070, 2645)],
    "66d_2": [(1070, 2602, 1250, 2645)],
    "66d_3": [(1250, 2602, 1272, 2645)],
    "66e_1": [(1280, 2602, 1305, 2645)],
    "66e_2": [(1305, 2602, 1485, 2645)],
    "66e_3": [(1485, 2602, 1508, 2645)],
    "66f_1": [(1510, 2600, 1545, 2645)],
    "66f_2": [(1545, 2600, 1713, 2645)],
    "66f_3": [(1713, 2600, 1740, 2645)],
    "66g_1": [(1748, 2600, 1775, 2645)],
    "66g_2": [(1775, 2602, 1945, 2645)],
    "66g_3": [(1945, 2602, 1975, 2645)],
    "66h_1": [(1980, 2600, 2010, 2645)],
    "66h_2": [(2010, 2602, 2175, 2645)],
    "66h_3": [(2175, 2602, 2210, 2645)],
    "66i": [(2238, 2603, 2460, 2645)],
    "66k_1": [(105, 2650, 133, 2680)],
    "66k_2": [(133, 2650, 310, 2680)],
    "66k_3": [(310, 2650, 335, 2680)],
    "66l_1": [(340, 2650, 370, 2690)],
    "66l_2": [(370, 2650, 545, 2690)],
    "66l_3": [(545, 2650, 570, 2690)],
    "66m_1": [(575, 2650, 605, 2690)],
    "66m_2": [(603, 2650, 775, 2690)],
    "66m_3": [(775, 2650, 805, 2690)],
    "66n_1": [(810, 2650, 840, 2690)],
    "66n_2": [(840, 2650, 1010, 2690)],
    "66n_3": [(1010, 2650, 1040, 2690)],
    "66p_1": [(1045, 2650, 1070, 2690)],
    "66p_2": [(1070, 2650, 1242, 2690)],
    "66p_3": [(1242, 2650, 1270, 2690)],
    "66o_1": [(1280, 2650, 1300, 2690)],
    "66o_2": [(1300, 2650, 1480, 2690)],
    "66o_3": [(1480, 2650, 1505, 2690)],
    "66q_1": [(1510, 2650, 1540, 2690)],
    "66q_2": [(1540, 2650, 1715, 2690)],
    "66q_3": [(1715, 2650, 1740, 2690)],
    "66r_1": [(1745, 2650, 1775, 2690)],
    "66r_2": [(1775, 2650, 1950, 2690)],
    "66r_3": [(1950, 2650, 1975, 2690)],
    "66s_1": [(1985, 2650, 2010, 2690)],
    "66s_2": [(2010, 2650, 2183, 2690)],
    "66s_3": [(2183, 2650, 2210, 2690)],
    "66t": [(2215, 2650, 2465, 2690)],
    "69": [(190, 2700, 380, 2745)],
    "76": [(1800, 2750, 2080, 2795)],
    "76last": [(1605, 2805, 2055, 2840)],
    "76first": [(2145, 2805, 2380, 2840)],
    "81a": [(838, 2950, 890, 2985)],
    "81b": [(900, 2950, 1180, 2988)],
}

# Путь к изображению и к временному каталогу для сохранения обрезанных изображений
image_path = "high_res_screenshot.png"
temp_path = Path("cropped_images")  # Создадим директорию для временных изображений
temp_path.mkdir(exist_ok=True)

# Открываем изображение
image = Image.open(image_path)

# Масштабируемый коэффициент (если нужно масштабировать координаты)
scale_factor = 1  # Измените, если нужно масштабировать

all_texts = {}

# Пример использования функции split_on_capitals
for key, areas in crop_areas.items():
    for i, crop_area in enumerate(areas):

        # Масштабируем каждый список
        scaled_area = scale_crop_area(crop_area, scale_factor)

        # Обрезаем изображение до заданной области
        cropped_image = image.crop(scaled_area)

        # Улучшаем обрезанное изображение
        cropped_image = enhance_image(cropped_image)

        # Сохраняем обрезанное изображение для визуализации
        filename_cropped_image = temp_path / f"cropped_image_{key}_{i+1}.png"
        cropped_image.save(filename_cropped_image)

        # Распознаем текст на обрезанном изображении
        result = reader.readtext(str(filename_cropped_image))

        # Выводим результат
        cleaned_text = [text for (_, text, _) in result]
        print(f"Результат для области {key}: {cleaned_text}")

        # Рисуем прямоугольник на оригинальном изображении для визуализации
        draw = ImageDraw.Draw(image)
        draw.rectangle(scaled_area, outline="red", width=2)

        # Сохраняем результаты
        if key not in all_texts:
            all_texts[key] = []
        all_texts[key].extend(cleaned_text)

# Сохраняем оригинальное изображение с выделенными областями
image.save("image_with_boxes.png")

# Выводим результаты всех областей
print("Все распознанные тексты:", all_texts)
