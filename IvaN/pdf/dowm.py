import time
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import requests

# Установка директорий для логов и данных
current_directory = Path.cwd()
pdf_files_directory = current_directory / "pdf"
data_directory = current_directory / "data"
configuration_directory = current_directory / "configuration"

pdf_files_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

output_txt_file = data_directory / "output.txt"
xlsx_result = data_directory / "result.xlsx"
file_proxy = configuration_directory / "proxy.txt"


def read_urls_from_txt(input_txt_file: str) -> List[str]:
    """Читает список URL из текстового файла.

    Args:
        input_txt_file (str): Путь к входному текстовому файлу.

    Returns:
        List[str]: Список URL-адресов.

    Raises:
        FileNotFoundError: Если файл не найден.
        IOError: Если файл пустой или произошла ошибка при чтении.
    """
    try:
        with open(input_txt_file, "r", encoding="utf-8") as file:
            urls = [
                line.strip() for line in file if line.strip()
            ]  # Убираем пустые строки и лишние пробелы
            return urls

    except FileNotFoundError:
        raise FileNotFoundError(f"Файл {input_txt_file} не найден.")

    except IOError as e:
        raise IOError(f"Ошибка при чтении файла {input_txt_file}: {e}")


def download_pdf():
    """
    Downloads a PDF file from the specified URL and saves it with the given filename.

    :param url: URL of the PDF file
    :param save_as: Filename to save the downloaded PDF as
    """
    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
        "Referer": "https://record.minjust.gov.kg/view/03001200410207",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    urls = read_urls_from_txt(output_txt_file)
    for inn in urls:
        output_pdf_file = pdf_files_directory / f"{inn}.pdf"
        url = f"https://record.minjust.gov.kg/register/api/v1/register/{inn}/record"
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses

            # Write the content to a file
            with open(output_pdf_file, "wb") as pdf_file:
                for chunk in response.iter_content(chunk_size=1024):
                    pdf_file.write(chunk)
            time.sleep(5)
            print(f"PDF successfully downloaded and saved as '{output_pdf_file}'.")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")


download_pdf()
