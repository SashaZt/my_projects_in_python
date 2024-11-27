# import json

# import pdfplumber


# def extract_text_from_pdf(file_path):
#     """
#     Extracts text from a PDF file.

#     :param file_path: Path to the PDF file
#     :return: Extracted text as a string
#     """
#     try:
#         with pdfplumber.open(file_path) as pdf:
#             extracted_text = ""
#             for page_number, page in enumerate(pdf.pages, start=1):
#                 page_text = page.extract_text()
#                 if page_text:
#                     extracted_text += f"--- Page {page_number} ---\n"
#                     extracted_text += page_text + "\n\n"
#             return extracted_text
#     except FileNotFoundError:
#         return "The specified file was not found. Please check the file path."
#     except Exception as e:
#         return f"An error occurred: {e}"


# def extract_data_by_keys_with_values(extracted_text, keys):
#     """
#     Extracts values for the specified keys from the text.
#     Values are assumed to be on the next line after the key.

#     :param extracted_text: Extracted text from the PDF
#     :param keys: List of keys to look for in the text
#     :return: Dictionary containing keys and their corresponding values
#     """
#     data = {}
#     lines = extracted_text.split("\n")

#     for i, line in enumerate(lines):
#         # Clean up line for comparison
#         stripped_line = line.strip().rstrip(":")
#         if stripped_line in keys:
#             # Take the next line as the value, if available
#             value = lines[i + 1].strip() if i + 1 < len(lines) else None
#             data[stripped_line] = value

#     return data


# def save_to_json(data, output_file):
#     """
#     Saves the collected data to a JSON file.

#     :param data: Dictionary containing the data
#     :param output_file: Path to the JSON output file
#     """
#     with open(output_file, "w", encoding="utf-8") as json_file:
#         json.dump(data, json_file, ensure_ascii=False, indent=4)


# # Define keys to extract from the PDF
# keys_page_1 = [
#     "Алгачкы катталган күнү",
#     "Жетекчиси",
#     "ИСН",
#     "ИУЖКнын коду",
#     "Иш-аракетинин токтотулган күнү",
#     "Кайра катталган күнү",
#     "Каттоо номери",
#     "Каттоочу орган",
#     "Мамлекеттик тилде толук аталышы",
#     "Расмий тилде толук аталышы",
#     "Учурдагы статусу",
#     "Уюштуруучулардын/катышуучулардын, мүчөлөрдүн саны",
#     "Юридикалык дареги",
# ]

# keys_page_2 = [
#     "Дата первичной регистрации",
#     "Дата перерегистрации",
#     "ИНН",
#     "Код ОКПО",
#     "Количество учредителей/участников, членов",
#     "Полное фирменное наименование на государственном языке",
#     "Полное фирменное наименование на официальном языке",
#     "Регистрационный номер",
#     "Регистрация прекращения деятельности",
#     "Регистрирующий орган",
#     "Руководитель",
#     "Текущий статус",
#     "Юридический адрес",
# ]

# # Combine all keys
# all_keys = keys_page_1 + keys_page_2

# # Specify the path to your PDF file
# pdf_file_path = "record.pdf"

# # Extract text from the PDF
# extracted_text = extract_text_from_pdf(pdf_file_path)

# # Extract data by keys and their corresponding values
# if "--- Page" in extracted_text:
#     collected_data = extract_data_by_keys_with_values(extracted_text, all_keys)

#     # Save the collected data to a JSON file
#     output_json_file = "output_data.json"
#     save_to_json(collected_data, output_json_file)

#     print(f"Data successfully saved to {output_json_file}")
# else:
#     print("Failed to extract text or keys from the PDF.")


"""
Тестирую новый код

"""
import json
from pathlib import Path

import pdfplumber


def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file.

    :param file_path: Path to the PDF file
    :return: Extracted text as a string
    """
    try:
        with pdfplumber.open(file_path) as pdf:
            extracted_text = ""
            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += f"--- Page {page_number} ---\n"
                    extracted_text += page_text + "\n\n"
            return extracted_text
    except FileNotFoundError:
        return "The specified file was not found. Please check the file path."
    except Exception as e:
        return f"An error occurred: {e}"


def extract_data_by_keys_with_values(extracted_text, keys):
    """
    Extracts values for the specified keys from the text.
    Values are assumed to be on the next line after the key.

    :param extracted_text: Extracted text from the PDF
    :param keys: List of keys to look for in the text
    :return: Dictionary containing keys and their corresponding values
    """
    data = {}
    lines = extracted_text.split("\n")

    for i, line in enumerate(lines):
        # Clean up line for comparison
        stripped_line = line.strip().rstrip(":")
        if stripped_line in keys:
            # Take the next line as the value, if available
            value = lines[i + 1].strip() if i + 1 < len(lines) else None
            data[stripped_line] = value

    return data


def save_to_json(data, output_file):
    """
    Saves the collected data to a JSON file.

    :param data: Dictionary containing the data
    :param output_file: Path to the JSON output file
    """
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)


def process_all_pdfs(pdf_directory, keys, output_file):
    """
    Processes all PDF files in a directory, extracts data by keys, and saves the result to a JSON file.

    :param pdf_directory: Path to the directory containing PDF files
    :param keys: List of keys to extract from each PDF
    :param output_file: Path to the JSON output file
    """
    pdf_directory = Path(pdf_directory)
    all_data = []

    for pdf_file in pdf_directory.glob("*.pdf"):
        print(f"Processing: {pdf_file}")
        extracted_text = extract_text_from_pdf(pdf_file)

        if extracted_text:
            data = extract_data_by_keys_with_values(extracted_text, keys)
            # data["filename"] = pdf_file.name  # Include the filename for reference
            all_data.append(data)

    save_to_json(all_data, output_file)
    print(f"All data successfully saved to {output_file}")


# Define keys to extract from the PDF
keys_page_1 = [
    "Алгачкы катталган күнү",
    "Жетекчиси",
    "ИСН",
    "ИУЖКнын коду",
    "Иш-аракетинин токтотулган күнү",
    "Кайра катталган күнү",
    "Каттоо номери",
    "Каттоочу орган",
    "Мамлекеттик тилде толук аталышы",
    "Расмий тилде толук аталышы",
    "Учурдагы статусу",
    "Уюштуруучулардын/катышуучулардын, мүчөлөрдүн саны",
    "Юридикалык дареги",
]

keys_page_2 = [
    "Дата первичной регистрации",
    "Дата перерегистрации",
    "ИНН",
    "Код ОКПО",
    "Количество учредителей/участников, членов",
    "Полное фирменное наименование на государственном языке",
    "Полное фирменное наименование на официальном языке",
    "Регистрационный номер",
    "Регистрация прекращения деятельности",
    "Регистрирующий орган",
    "Руководитель",
    "Текущий статус",
    "Юридический адрес",
]

# Combine all keys
all_keys = keys_page_1 + keys_page_2

# Define the directory containing PDF files and the output JSON file
pdf_files_directory = Path("./pdf")  # Change to your directory path
output_json_file = "output_data.json"

# Process all PDFs and save the result
process_all_pdfs(pdf_files_directory, all_keys, output_json_file)
