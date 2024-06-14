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


urls = [
    "https://www.x-kom.pl/g-2/c/159-laptopy-notebooki-ultrabooki.html",
    "https://www.x-kom.pl/g-5/c/345-karty-graficzne.html",
    "https://www.x-kom.pl/g-5/c/11-procesory.html",
    "https://www.x-kom.pl/g-5/c/14-plyty-glowne.html",
]


@browser
def get_first_page(driver: Driver, data):
    # Посетить веб-сайт
    for url in urls[:1]:
        driver.get(url)
        time.sleep(5)
        # Найти кнопку с точным текстом "W porządku"
        button = driver.get_element_with_exact_text("W porządku", wait=Wait.SHORT)

        # Проверить, что кнопка найдена, и кликнуть по ней
        if button:
            button.click()
        page_html = driver.page_html
        # Используем регулярное выражение для поиска JSON после window.__INITIAL_STATE__['app'] =
        match = re.search(
            r"window\.__INITIAL_STATE__\['app'\]\s*=\s*({.*?});", page_html, re.DOTALL
        )

        if match:
            json_str = match.group(1)
            try:
                json_data = json.loads(json_str)
                # Сохраняем извлеченный JSON в файл
                with open("data.json", "w", encoding="utf-8") as json_file:
                    json.dump(json_data, json_file, ensure_ascii=False, indent=4)
                print("JSON успешно извлечен и сохранен в файл data.json")
            except json.JSONDecodeError as e:
                print("Ошибка декодирования JSON:", e)
        else:
            print("JSON не найден.")
        total_pages = (
            json_data.get("listing", {}).get("paginationState", {}).get("totalPages")
        )
        result = {}
        for page in range(1, total_pages + 1):  # Assuming pages start from 1
            driver.get(f"{url}?page={page}")
            time.sleep(2)
            # Найти кнопку с точным текстом "W porządku"
            button = driver.get_element_with_exact_text("W porządku", wait=Wait.SHORT)

            # Проверить, что кнопка найдена, и кликнуть по ней
            if button:
                button.click()
            elements = driver.select_all("a[data-testid='star-rating-link']")

            # Получить href атрибуты этих элементов
            hrefs = [element.get_attribute("href") for element in elements]

            # Создать JSON-структуру
            base_url = "https://www.x-kom.pl"
            for href in hrefs:
                # Удалить часть #Opinie из URL
                cleaned_href = re.sub(r"#Opinie.*", "", href)
                # Добавить префикс base_url
                full_url = base_url + cleaned_href
                # Извлечь числовую часть из URL
                match = re.search(r"p/(\d+)-", cleaned_href)
                if match:
                    id_number = match.group(1)
                    result[id_number] = {"url": full_url}

            # Сохраните HTML-код в файл
            filename = os.path.join(html_path, f"{page:02d}.html")
            page_html = driver.page_html
            with open(filename, "w", encoding="utf-8") as f:
                f.write(page_html)
        with open("all_href.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
        print("Результаты сохранены в all_href.json")


def parsing_htmls():
    folder = os.path.join(html_path, "*.html")

    files_html = glob.glob(folder)
    for item in files_html:
        # Открываем файл и читаем его содержимое
        with open(item, "r", encoding="utf-8") as file:
            html_content = file.read()

        # Используем регулярное выражение для поиска JSON после window.__INITIAL_STATE__['app'] =
        match = re.search(
            r"window\.__INITIAL_STATE__\['app'\]\s*=\s*({.*?});",
            html_content,
            re.DOTALL,
        )

        if match:
            json_str = match.group(1)
            try:
                json_data = json.loads(json_str)
                # Сохраняем извлеченный JSON в файл
                json_name = item.split("\\")[-1].replace(".html", "")
                filename = os.path.join(json_path, f"{json_name}.json")
                with open(filename, "w", encoding="utf-8") as json_file:
                    json.dump(json_data, json_file, ensure_ascii=False, indent=4)
                print(f"Cохранен в файл {filename}")
            except json.JSONDecodeError as e:
                print("Ошибка декодирования JSON:", e)
        else:
            print("JSON не найден.")


def parsing_json():
    # Открываем файл и читаем его содержимое
    with open("all_href.json", "r", encoding="utf-8") as href_file:
        href_data = json.load(href_file)
    folder = os.path.join(json_path, "*.json")

    files_json = glob.glob(folder)
    extracted_data = []
    for item in files_json:
        # Открываем файл и читаем его содержимое
        with open(item, "r", encoding="utf-8") as json_file:
            json_data = json.load(json_file)
        total_pages = (
            json_data.get("listing", {}).get("paginationState", {}).get("totalPages")
        )

        # Извлечение всех ID из recommendedCategory
        recommended_ids = set()
        products_lists = json_data.get("productsLists", {})
        for key, value in products_lists.items():
            if key.startswith("recommendedCategory"):
                for item in value:
                    recommended_ids.add(item.get("id"))

        # Извлечение данных из products
        products_data = json_data.get("products", {})

        for product_id, product_details in products_data.items():
            if product_id not in recommended_ids:
                product_info = {
                    "Kod producenta": product_details.get("producerCode"),
                    "Kod x-kom": product_details.get("id"),
                    "name": product_details.get("name"),
                    "price": product_details.get("price"),
                    "Avalible Status": product_details.get("availabilityStatus"),
                    "Typ": product_details.get("category", {}).get(
                        "parentCategoryName"
                    ),
                    "Link": href_data.get(product_id, {}).get(
                        "url"
                    ),  # Добавление URL из href_data
                }
                extracted_data.append(product_info)

    # Сохранение извлеченных данных в новый JSON файл
    with open("extracted_data.json", "w", encoding="utf-8") as output_file:
        json.dump(extracted_data, output_file, ensure_ascii=False, indent=4)

    print("Извлеченные данные успешно сохранены в файл extracted_data.json")


def json_to_excel(json_file, excel_file):
    # Открываем файл и читаем его содержимое
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Преобразуем данные в DataFrame
    df = pd.DataFrame(data)

    # Записываем DataFrame в Excel файл
    df.to_excel(excel_file, index=False)

    print(f"Данные успешно сохранены в файл {excel_file}")


if __name__ == "__main__":
    # get_first_page()
    # parsing_htmls()
    # scrape_heading_task()
    # parsing_html()
    parsing_json()
    json_to_excel("extracted_data.json", "output_data.xlsx")


# @request
# def scrape_heading_task(request: Request, data):
#     # Visit the Omkar Cloud website
#     response = request.get(url)
#     time.sleep(5)
#     print(response.status_code)
#     html_ru = response.text
#     with open("html.html", "w", encoding="utf-8") as f:
#         f.write(html_ru)


# # Initiate the web scraping task
# scrape_heading_task()
