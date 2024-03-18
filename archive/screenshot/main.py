# from PIL import Image
# from PIL import ImageGrab
# import pytesseract
# import time
# from datetime import datetime
# import re
# import os
from PIL import Image
from PIL import ImageGrab
import pytesseract
import time
from datetime import datetime
import re
import os
from PIL import ImageEnhance

# def main():
    # # установка пути к Tesseract OCR в Windows
    # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    #
    # while True:
    #     # создание скриншота экрана
    #     screenshot = ImageGrab.grab()
    #
    #     # сохранение скриншота в файл
    #     current_time = datetime.now().strftime("%d.%m.%Y_%H_%M")
    #     filename_png = f"{current_time}.png"
    #     screenshot.save(filename_png)
    #
    #     # открытие скриншота
    #     image = Image.open(filename_png)
    #
    #     # установка области для распознавания текста
    #     text_area = (750, 100, 850, 1000)
    #
    #     # вырезание области изображения
    #     cropped_image = image.crop(text_area)
    #     # Сохраняем
    #     cropped_image.save("cropped_image.png")
    #
    #     # распознавание текста с помощью Tesseract OCR
    #     text = pytesseract.image_to_string(cropped_image, lang='rus', config='--psm 11 --oem 3 -c tessedit_char_whitelist=0123456789-')
    #
    #
    #     # сохранение распознанного текста в текстовый файл
    #     filename_txt = f"{current_time}.txt"
    #     with open(filename_txt, "w") as f:
    #         numbers = re.findall(r'\d{3}-\d{3}-\d{2}-\d{2}', text)
    #         for number in numbers:
    #             f.write(number + '\n')
    #
    #     # удаляем скриншот
    #     os.remove(filename_png)
    #
    #     # ожидание 5 минут
    #     time.sleep(300)


def main():
    # установка пути к Tesseract OCR в Windows
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # сохранение даты последней записи в файл
    last_write_date = datetime.now().strftime('%d.%m.%Y')

    while True:
        # создание скриншота экрана
        screenshot = ImageGrab.grab()

        # сохранение скриншота в файл
        current_time = datetime.now().strftime("%d.%m.%Y_%H_%M")
        filename_png = f"{current_time}.png"
        screenshot.save(filename_png)

        # открытие скриншота
        image = Image.open(filename_png)

        # установка области для распознавания текста
        text_area = (740, 100, 860, 1000)

        # вырезание области изображения
        cropped_image = image.crop(text_area)

        # преобразование изображения в черно-белый формат
        cropped_image = cropped_image.convert('L')

        # улучшение контрастности
        enhancer = ImageEnhance.Contrast(cropped_image)
        cropped_image = enhancer.enhance(
            3.0)  # можно изменять коэффициент контрастности, чтобы достичь лучшего результата

        # сохранение обработанного изображения
        cropped_image.save("processed_image.png")

        # распознавание текста с помощью Tesseract OCR
        text = pytesseract.image_to_string(cropped_image, lang='rus',
                                           config='--psm 11 --oem 3 -c tessedit_char_whitelist=0123456789-')

        # если дата последней записи не соответствует текущей дате,
        # то создаем новый файл и записываем туда новые значения
        if last_write_date != datetime.now().strftime('%d.%m.%Y'):
            filename_txt = f"{datetime.now().strftime('%d.%m.%Y')}.txt"
            with open(filename_txt, "w") as f:
                numbers = re.findall(r'\d{3}-\d{3}-\d{2}-\d{2}', text)
                for number in numbers:
                    f.write(number + '\n')
            last_write_date = datetime.now().strftime('%d.%m.%Y')
        else:
            # иначе дописываем новые значения в уже созданный файл
            filename_txt = f"{datetime.now().strftime('%d.%m.%Y')}.txt"
            with open(filename_txt, "a") as f:
                numbers = re.findall(r'\d{3}-\d{3}-\d{2}-\d{2}', text)
                for number in numbers:
                    f.write(number + '\n')
        # удаляем скриншоты
        # os.remove(filename_png)
        # os.remove("processed_image.png")

        # ожидание 5 минут
        time.sleep(300)

if __name__ == '__main__':
    main()
