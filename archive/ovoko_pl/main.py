from botasaurus.browser import browser, Driver, Wait
import time
import re
import json
import pandas as pd
import os
import glob

current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
html_path = os.path.join(temp_path, "html")
json_path = os.path.join(temp_path, "json")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(html_path, exist_ok=True)
os.makedirs(json_path, exist_ok=True)


@browser
def get_first_page(driver: Driver, data):
    # Посетить веб-сайт
    for url in range(2):
        url = (
            "https://ovoko.pl/szukaj?man_id=3&cmc=1&cm=36&mfi=3,1,36;&prs=1&page={url}"
        )
        driver.get(url)
        time.sleep(50)
        # # Найти кнопку с точным текстом "W porządku"
        # button = driver.get_element_with_exact_text("W porządku", wait=Wait.SHORT)

        # # Проверить, что кнопка найдена, и кликнуть по ней
        # if button:
        #     button.click()
        # page_html = driver.page_html
        # # Используем регулярное выражение для поиска JSON после window.__INITIAL_STATE__['app'] =
        # match = re.search(
        #     r"window\.__INITIAL_STATE__\['app'\]\s*=\s*({.*?});", page_html, re.DOTALL
        # )

        # if match:
        #     json_str = match.group(1)
        #     try:
        #         json_data = json.loads(json_str)
        #         # Сохраняем извлеченный JSON в файл
        #         with open("data.json", "w", encoding="utf-8") as json_file:
        #             json.dump(json_data, json_file, ensure_ascii=False, indent=4)
        #         print("JSON успешно извлечен и сохранен в файл data.json")
        #     except json.JSONDecodeError as e:
        #         print("Ошибка декодирования JSON:", e)
        # else:
        #     print("JSON не найден.")
        # total_pages = (
        #     json_data.get("listing", {}).get("paginationState", {}).get("totalPages")
        # )
        # result = {}
        # for page in range(1, total_pages + 1):  # Assuming pages start from 1
        #     driver.get(f"{url}?page={page}")
        #     time.sleep(2)
        #     # Найти кнопку с точным текстом "W porządku"
        #     button = driver.get_element_with_exact_text("W porządku", wait=Wait.SHORT)

        #     # Проверить, что кнопка найдена, и кликнуть по ней
        #     if button:
        #         button.click()
        #     elements = driver.select_all("a[data-testid='star-rating-link']")

        #     # Получить href атрибуты этих элементов
        #     hrefs = [element.get_attribute("href") for element in elements]

        #     # Создать JSON-структуру
        #     base_url = "https://www.x-kom.pl"
        #     for href in hrefs:
        #         # Удалить часть #Opinie из URL
        #         cleaned_href = re.sub(r"#Opinie.*", "", href)
        #         # Добавить префикс base_url
        #         full_url = base_url + cleaned_href
        #         # Извлечь числовую часть из URL
        #         match = re.search(r"p/(\d+)-", cleaned_href)
        #         if match:
        #             id_number = match.group(1)
        #             result[id_number] = {"url": full_url}

        #     # Сохраните HTML-код в файл
        #     filename = os.path.join(html_path, f"{page:02d}.html")
        #     page_html = driver.page_html
        #     with open(filename, "w", encoding="utf-8") as f:
        #         f.write(page_html)
        # with open("all_href.json", "w", encoding="utf-8") as f:
        #     json.dump(result, f, ensure_ascii=False, indent=4)
        # print("Результаты сохранены в all_href.json")


if __name__ == "__main__":
    get_first_page()
