from pdf2image import convert_from_path
from PIL import Image, ImageEnhance
import pytesseract
from fpdf import FPDF

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\poppler\Library\bin"


def enhance_image(image, contrast=1.5, saturation=1.5):
    # Преобразуем изображение в RGB
    img = image.convert("RGB")

    # Повышаем контрастность
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast)

    # Повышаем насыщенность
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(saturation)

    return img


def perform_ocr(image):
    # Преобразуем изображение в текст с помощью Tesseract OCR
    text = pytesseract.image_to_string(image, lang="eng")
    return text


def save_text_to_pdf(text, output_pdf_path):
    # Создаем PDF-документ и добавляем текст
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Добавляем шрифт FreeSerif, поддерживающий Юникод
    pdf.add_font("FreeSerif", "", "FreeSerif.ttf")
    pdf.set_font("FreeSerif", size=12)

    max_width = pdf.w - pdf.l_margin - pdf.r_margin

    # Разделяем текст на строки и добавляем их в PDF
    for line in text.split("\n"):
        words = line.split()
        for word in words:
            # Если слово слишком длинное, разбиваем его
            while pdf.get_string_width(word) > max_width:
                # Найдем максимальную длину, которая впишется в строку
                split_index = 1
                while pdf.get_string_width(word[:split_index]) < max_width:
                    split_index += 1
                # Отправим первую часть слова в PDF
                pdf.cell(0, 10, word[: split_index - 1], ln=True)
                # Оставшуюся часть слова оставим для дальнейшей обработки
                word = word[split_index - 1 :]
            # Отправим слово или оставшуюся его часть в PDF
            pdf.cell(0, 10, word, ln=True)

    pdf.output(output_pdf_path)


def enhance_pdf_and_perform_ocr():
    pdf_path = "pdf1.pdf"
    output_pdf_path = "enhanced_pdf1.pdf"

    # Конвертируем страницы PDF в изображения
    images = convert_from_path(pdf_path, dpi=300, poppler_path=poppler_path)

    all_text = ""
    for img in images:
        # Повышаем качество изображения
        enhanced_img = enhance_image(img)

        # Выполняем OCR на улучшенном изображении
        text = perform_ocr(enhanced_img)
        all_text += text + "\n\n"

    # Сохраняем результаты OCR в новый PDF
    save_text_to_pdf(all_text, output_pdf_path)


if __name__ == "__main__":
    enhance_pdf_and_perform_ocr()
