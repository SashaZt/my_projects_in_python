import csv
import os
import time
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from openai import OpenAI
from playwright.sync_api import sync_playwright

# Замените на ваш ключ API OpenAI
# os.environ["OPENAI_API_KEY"] = "YOUR_API_KEY"

# Инициализация клиента

# Инициализация клиента OpenAI


# Инициализация клиента OpenAI
client = OpenAI(api_key=api_key)


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
            html_filename = f"{website_name}.html"
            with open(html_filename, "w", encoding="utf-8") as html_file:
                html_file.write(html_content)

            # Парсим HTML с помощью BeautifulSoup и сохраняем текст
            soup = BeautifulSoup(html_content, "html.parser")
            text_content = soup.get_text(separator="\n")
            txt_filename = f"{website_name}.txt"
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

        # Формируем запрос к модели, добавляя инструкцию
        # question = (
        #     f"Проанализируй сайт {site}, который находится в файле '{file_path}', который я разпарсил со страницы: \n"
        #     f"Сайт - категории через запятую на русском языке, если другой язык переведи пожалуйста, (например: 001success.net - Бизнес, Финансы, Маркетинг). "
        #     f"Никаких дополнительных пояснений или комментариев не нужно, просто перечисли категории на русском языке."
        #     f"\n\n{text_content}"
        # )
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
    # Пример использования
    sites = [
        "007soccerpicks.net",
        "1.zt.ua",
        "100.kr.ua",
        "1000goals.com",
        "1000ventures.com",
        "1001hry.org",
        "1001idea.net",
        "1001tunisie.com",
        "100babytips.com",
        "100breakingnews.com",
    ]
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
                answer = ask_openai_from_file(txt_file, site)
                writer.writerow([site, answer])
                print(f"Ответ для {site} записан в файл {csv_filename}")
            else:
                print(f"Сайт {site} пропущен из-за ошибки при получении контента.")

# # Функция для запроса к модели GPT
# def ask_openai(question):
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o",  # Используемая модель
#             messages=[{"role": "user", "content": question}],
#             max_tokens=150,
#         )
#         answer = response.choices[0].message.content.strip()
#         return answer
#     except Exception as e:
#         return f"Ошибка при запросе к API: {e}"

# while True:
#     # Использование функции для запроса к OpenAI
#     site = "001success.net"
# sites = [
#     "007soccerpicks.net",
#     "1.zt.ua",
#     "100.kr.ua",
#     "1000goals.com",
#     "1000ventures.com",
#     "1001hry.org",
#     "1001idea.net",
#     "1001tunisie.com",
#     "100babytips.com",
#     "100breakingnews.com",
# ]
# for site in sites:
#         user_question = (
# f"Проанализируй сайт {site}  онлайн и ответь только в формате: "
# f"Сайт - категории через запятую (например: 001success.net - Бизнес, Финансы, Маркетинг). "
# f"Никаких дополнительных комментариев."
#         )
#         answer = ask_openai(user_question)
#         print(answer)
#     break  # Завершение while
