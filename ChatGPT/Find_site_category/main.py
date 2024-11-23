import csv
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI
from playwright.sync_api import sync_playwright

# Путь к папкам
current_directory = Path.cwd()
data_directory = current_directory / "data"
files_directory = current_directory / "files"

data_directory.mkdir(parents=True, exist_ok=True)
files_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
# Инициализация клиента OpenAI
env_path = os.path.join(os.getcwd(), "configuration", ".env")
load_dotenv(env_path)
api_key = os.getenv("API_KEY")
client = OpenAI(api_key=api_key)


def read_cities_from_csv(input_csv_file: str) -> List[str]:
    """Читает список URL из столбца 'url' CSV-файла.

    Args:
        input_csv_file (str): Путь к входному CSV-файлу.

    Returns:
        List[str]: Список URL-адресов из столбца 'url'.

    Raises:
        ValueError: Если файл не содержит столбца 'url'.
        FileNotFoundError: Если файл не найден.
        pd.errors.EmptyDataError: Если файл пустой.
    """
    try:
        df = pd.read_csv(input_csv_file)

        if "url" not in df.columns:
            raise ValueError("Входной файл не содержит столбца 'url'.")

        urls = df["url"].dropna().tolist()  # Удаляем пустые значения, если они есть
        return urls

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Файл {input_csv_file} не найден.") from e
    except pd.errors.EmptyDataError as e:
        raise pd.errors.EmptyDataError(f"Файл {input_csv_file} пустой.") from e


# Функция для получения контента сайта и сохранения в HTML и TXT
def get_website_content(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )  # Открываем браузер не в фоновом режиме
        page = browser.new_page()
        try:
            page.goto(
                url, timeout=10000, wait_until="networkidle"
            )  # Устанавливаем таймаут на 10 секунд
            time.sleep(2)
            # Проверяем, если загрузился тег body, переходим дальше
            if page.locator("body").is_visible():
                pass

            # Получаем HTML контент страницы
            html_content = page.content()

            # Сохраняем HTML в файл
            website_name = url.split("//")[-1].split("/")[0]
            html_filename = files_directory / f"{website_name}.html"
            with open(html_filename, "w", encoding="utf-8") as html_file:
                html_file.write(html_content)

            # Парсим HTML с помощью BeautifulSoup и сохраняем текст
            soup = BeautifulSoup(html_content, "html.parser")
            text_content = soup.get_text(separator="\n")
            txt_filename = files_directory / f"{website_name}.txt"
            with open(txt_filename, "w", encoding="utf-8") as txt_file:
                txt_file.write(text_content)

            browser.close()
            return html_filename, txt_filename
        except Exception as e:
            print(f"Ошибка при обработке сайта {url}: {e}")
            browser.close()
            return None, None


# Функция для отправки текста из файла в GPT модель с инструкцией
def ask_openai_from_file(file_path, site):
    try:
        # Читаем содержимое текстового файла
        with open(file_path, "r", encoding="utf-8") as file:
            text_content = file.read()

        question = (
            f"Проанализируй сайт {site}, который находится в файле '{file_path}', который я разпарсил со страницы: \n"
            f"Сайт - категории через запятую на русском языке, если другой язык переведи пожалуйста, (например: 001success.net - Бизнес, Финансы, Маркетинг). "
            f"Никаких дополнительных пояснений или комментариев не нужно, просто перечисли категории на русском языке."
            f"\n\n{text_content}"
        )

        # Создаем запрос к модели OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Или "gpt-4", в зависимости от задачи
            messages=[{"role": "user", "content": question}],
            max_tokens=150,
        )

        # Получаем ответ
        answer = response.choices[0].message.content.strip()
        return answer
    except Exception as e:
        return f"Ошибка при запросе к API: {e}"


if __name__ == "__main__":
    sites = read_cities_from_csv(output_csv_file)
    csv_filename = "site_analysis_results.csv"

    # Запись результатов в один CSV файл
    with open(csv_filename, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        writer.writerow(["Сайт", "Категории"])

        for site in sites:
            # Добавляем https://, если его нет в URL
            if not urlparse(site).scheme:
                site = "https://" + site

            html_file, txt_file = get_website_content(site)
            if html_file and txt_file:
                html_file.unlink()  # Удаляем файл

                answer = ask_openai_from_file(txt_file, site)
                writer.writerow([site, answer])
                print(f"Ответ для {site} записан в файл {csv_filename}")
            else:
                print(f"Сайт {site} пропущен из-за ошибки при получении контента.")
