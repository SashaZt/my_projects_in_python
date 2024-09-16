import csv
import docx


# Функция для извлечения текста и ссылок из DOCX файла
def extract_text_and_links(docx_file):
    doc = docx.Document(docx_file)
    extracted_data = []

    for paragraph in doc.paragraphs:
        text = paragraph.text
        for run in paragraph.runs:
            if "HYPERLINK" in run.text:
                text += f' [URL: "{run.text}"]'
        extracted_data.append(text)

    # Объединяем весь текст в одну строку
    combined_text = " ".join(extracted_data).strip()
    return combined_text


# Путь к вашим файлам DOCX
docx_file1 = "https_01.docx"
# docx_file2 = "файл2.docx"

# Извлекаем текст и ссылки из обоих файлов
combined_text1 = extract_text_and_links(docx_file1)
# combined_text2 = extract_text_and_links(docx_file2)

# Объединяем содержимое обоих файлов в одну строку
final_combined_text = f"{combined_text1}"

# Записываем в CSV файл в одну строку
csv_file_path = "output.csv"
with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow([final_combined_text])

print(f"Данные сохранены в {csv_file_path}")
