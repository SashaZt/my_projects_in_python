from botasaurus.browser import browser, Driver
import time
import re
import json
import pandas as pd

url = "https://www.x-kom.pl/g-2/c/159-laptopy-notebooki-ultrabooki.html"


@browser
def scrape_heading_task(driver: Driver, data):
    # Visit the Omkar Cloud website
    driver.get(url)
    time.sleep(10)
    # Извлечь все элементы с данным XPath
    # Извлечь все элементы с данным селектором
    elements = driver.select_all("a[data-testid='star-rating-link']")

    # Получить href атрибуты этих элементов
    hrefs = [element.get_attribute("href") for element in elements]

    # Создать JSON-структуру
    result = {}
    base_url = "https://www.x-kom.pl/"
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

    with open("all_href.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    print("Результаты сохранены в all_href.json")

    # Retrieve the heading element's text
    page_html = driver.page_html
    #  Сохраните HTML-код в файл
    with open("page.html", "w", encoding="utf-8") as f:
        f.write(page_html)


def parsing_html():

    # Открываем файл и читаем его содержимое
    with open("page.html", "r", encoding="utf-8") as file:
        html_content = file.read()

    # Используем регулярное выражение для поиска JSON после window.__INITIAL_STATE__['app'] =
    match = re.search(
        r"window\.__INITIAL_STATE__\['app'\]\s*=\s*({.*?});", html_content, re.DOTALL
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


def parsing_json():
    # Открываем файл и читаем его содержимое
    with open("data.json", "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)

    # Открываем файл и читаем его содержимое
    with open("all_href.json", "r", encoding="utf-8") as href_file:
        href_data = json.load(href_file)

    # Извлечение данных из products
    products_data = json_data.get("products", {})
    extracted_data = []
    for product_id, product_details in products_data.items():
        product_info = {
            "producerCode": product_details.get("producerCode"),
            "id": product_details.get("id"),
            "name": product_details.get("name"),
            "price": product_details.get("price"),
            "availabilityStatus": product_details.get("availabilityStatus"),
            "parentCategoryName": product_details.get("category", {}).get(
                "parentCategoryName"
            ),
            "url": href_data.get(product_id, {}).get(
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
    scrape_heading_task()
    parsing_html()
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
