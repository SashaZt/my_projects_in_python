import asyncio
import json
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from logger import logger
from playwright.async_api import async_playwright

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "easy.html"


def get_html():
    cookies = {
        "userID": "07C030CC-D134-4FF1-8A9F-5440DC1F7EE2",
        "_ga": "GA1.3.983105115.1745951658",
        "_gid": "GA1.3.1806991019.1746194698",
        "_gat_gtag_UA_11785560_3": "1",
        "__cflb": "0H28vij4HMF3vJqtdn5nRFw9cCEeUbcAeXHmAfHSr6Z",
        "_ga_1JG1K8B43N": "GS1.1.1746194697.7.1.1746194698.59.0.0",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        # 'cookie': 'userID=07C030CC-D134-4FF1-8A9F-5440DC1F7EE2; _ga=GA1.3.983105115.1745951658; _gid=GA1.3.1806991019.1746194698; _gat_gtag_UA_11785560_3=1; __cflb=0H28vij4HMF3vJqtdn5nRFw9cCEeUbcAeXHmAfHSr6Z; _ga_1JG1K8B43N=GS1.1.1746194697.7.1.1746194698.59.0.0',
    }

    response = requests.get(
        "https://easy.co.il/list/Maintenance-and-Management-Of-Buildings",
        cookies=cookies,
        headers=headers,
        timeout=30,
    )

    # Проверка кода ответа
    if response.status_code == 200:

        # Сохранение HTML-страницы целиком
        with open(output_html_file, "w", encoding="utf-8") as file:
            file.write(response.text)
        logger.info(f"Successfully saved {output_html_file}")
    else:
        logger.error(f"Failed to get HTML. Status code: {response.status_code}")
    # ПАГИНАЦИЯ ebay


def remove_at_type(data):
    """Рекурсивно удаляет ключи '@type' из словаря."""
    if isinstance(data, dict):
        # Создаем новый словарь без '@type'
        new_data = {k: remove_at_type(v) for k, v in data.items() if k != "@type"}
        return new_data
    elif isinstance(data, list):
        return [remove_at_type(item) for item in data]
    return data


# Функция для извлечения названия предприятия
def parse_company_name(soup):
    company_name_tag = soup.find(
        "p", class_="modal-title display-inline-block farmer-modal-name ng-binding"
    )
    if company_name_tag:
        return company_name_tag.text.strip()
    return None


# 1. Парсинг телефонных номеров
def parse_phone_numbers(soup):
    phone_data = []
    phone_rows = soup.find_all("tr", class_="beige-hover ng-scope ng-isolate-scope")

    for row in phone_rows:
        phone_dict = {}

        # Извлекаем номер телефона
        phone_link = row.find("a", class_="same-phone-width")
        if phone_link:
            phone_dict["phone_number"] = re.sub(
                r"\s+", " ", phone_link.get("data-content", "").strip()
            )

        # Извлекаем позицию
        position = row.find("span", class_="position-title")
        phone_dict["position"] = position.text.strip() if position else None

        # Извлекаем ФИО
        full_name = row.find("span", class_="phone-comment")
        phone_dict["full_name"] = (
            re.sub(r"\s+", " ", full_name.text.strip()) if full_name else None
        )

        phone_data.append(phone_dict)

    return phone_data


# 2. Парсинг email-таблицы
def parse_emails(soup):
    email_data = []
    email_rows = soup.find_all(
        "tr",
        class_="beige-hover ng-scope",
        attrs={"ng-repeat": "contact in contacts | filter: { name:'email' }"},
    )

    for row in email_rows:
        email_dict = {}

        # Извлекаем email
        email = row.find("span", class_="ng-binding")
        email_dict["email"] = email.text.strip() if email else None

        email_data.append(email_dict)

    return email_data


# 3. Парсинг дополнительной информации
def parse_additional_info(soup):
    info_dict = {}
    org_info = soup.find("div", class_="org-info-parent")

    if org_info:
        # Извлекаем директора
        director_div = org_info.find("div", {"ng-if": "org.director"})
        if director_div:
            director = director_div.find("div", class_="ng-binding")
            info_dict["director"] = director.text.strip() if director else None

        # Извлекаем ЭДРПОУ
        edrpou_div = org_info.find("div", {"ng-if": "org.erdpou"})
        if edrpou_div:
            edrpou = edrpou_div.find("div", class_="ng-binding")
            info_dict["edrpou"] = edrpou.text.strip() if edrpou else None

        # Извлекаем адрес
        address_div = org_info.find("div", {"ng-if": "org.address_label"})
        if address_div:
            address = address_div.find("div", class_="ng-binding")
            info_dict["address"] = address.text.strip() if address else None

        # Извлекаем КВЭД
        kved_div = org_info.find("div", {"ng-if": "org.description"})
        if kved_div:
            kved = kved_div.find("div", class_="ng-binding")
            info_dict["kved"] = kved.text.strip() if kved else None

    return info_dict


# Функция для разделения ФИО на части
def split_full_name(full_name):
    if not full_name:
        return None, None, None
    parts = full_name.split()
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1], None
    elif len(parts) == 1:
        return parts[0], None, None
    return None, None, None


# Функция для извлечения области, района и города/села из адреса
def parse_address(address):
    if not address:
        return None, None, None

    parts = address.split(",")
    if len(parts) < 3:
        return None, None, None

    # Область обычно после "Україна"
    region = None
    district = None
    locality = None

    for part in parts:
        part = part.strip()
        if "обл." in part:
            region = part
        elif "р-н" in part:
            district = part
        elif "село" in part or "місто" in part or "селище" in part:
            locality = part

    return region, district, locality


def get_breadcrumbList(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            # Получаем текст скрипта и проверяем его наличие
            script_text = script.string
            if not script_text or not script_text.strip():
                continue

            # Проверим, что это скрипт JSON-LD
            if "application/ld+json" not in script.get("type", ""):
                continue
            json_data = json.loads(script_text)
            # Проверяем, является ли это продуктом
            if isinstance(json_data, dict):
                # Проверяем тип - может быть строкой или списком типов
                product_type = json_data.get("@type")
                is_product = False

                if isinstance(product_type, str) and product_type == "BreadcrumbList":
                    is_product = True
                elif (
                    isinstance(product_type, list) and "BreadcrumbList" in product_type
                ):
                    is_product = True

                if is_product:
                    item_list = json_data.get("itemListElement", [])[-1]
                    name_category = item_list.get("name", "")
                    return name_category
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обработке скрипта: {str(e)}")


def scrap_html():

    # Список для хранения данных
    data = []
    # Множество для хранения всех уникальных ключей характеристик
    spec_keys = set()

    # Проходим по всем HTML-файлам в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

            try:
                soup = BeautifulSoup(content, "lxml")

                # Инициализируем словарь для данных
                product_data = {"filename": html_file.name}
                breadcrumb = get_breadcrumbList(soup)
                product_data["category"] = breadcrumb

                # 1. Извлекаем URL из <meta property="og:url">
                url_meta = soup.find("meta", {"property": "og:url"})
                product_data["url"] = url_meta.get("content", "") if url_meta else ""

                title_tag = soup.find("div", {"data-testid": "x-item-title"})
                product_data["title"] = (
                    title_tag.find("span").get_text(strip=True)
                    if title_tag and title_tag.find("span")
                    else ""
                )
                # 2. Извлекаем цену из <div class="x-price-primary">
                price_div = soup.find("div", {"class": "x-price-primary"})
                if price_div:
                    price_text = price_div.find(
                        "span", {"class": "ux-textspans"}
                    ).get_text(strip=True)
                    # Извлекаем числовое значение (например, "US $1,450.00" -> "1450.00")
                    price = "".join(
                        filter(lambda x: x.isdigit() or x == ".", price_text)
                    )
                    product_data["price"] = price
                else:
                    product_data["price"] = ""

                # 3. Извлекаем изображения (до 3) из <div class="ux-image-carousel-item image-treatment image">
                images = []
                image_divs = soup.find_all(
                    "div", {"class": "ux-image-carousel-item image-treatment image"}
                )
                for div in image_divs[:3]:  # Ограничиваем до 3 изображений
                    img = div.find("img")
                    if img:
                        src = img.get("data-zoom-src")
                        if src:
                            images.append(src)
                product_data["image_1"] = images[0] if len(images) > 0 else ""
                product_data["image_2"] = images[1] if len(images) > 1 else ""
                product_data["image_3"] = images[2] if len(images) > 2 else ""

                # 4. Извлекаем состояние товара
                condition_div = soup.find("div", {"class": "vim x-item-condition"})
                if condition_div:
                    condition_text = condition_div.find(
                        "span", {"data-testid": "ux-textual-display"}
                    )
                    product_data["condition"] = (
                        condition_text.get_text(strip=True) if condition_text else ""
                    )
                else:
                    product_data["condition"] = ""

                # 5. Извлекаем информацию о возврате
                returns_div = soup.find("div", {"data-testid": "x-returns-minview"})
                if not returns_div:
                    # Если не нашли по data-testid, пробуем поискать по классу как запасной вариант
                    returns_div = soup.find("div", {"class": "vim x-returns-minview"})

                if returns_div:
                    # Ищем все элементы с текстом внутри блока возвратов
                    returns_text = returns_div.find(
                        "div", {"class": "ux-labels-values__values-content"}
                    )
                    if returns_text:
                        # Собираем весь текст из дочерних элементов, соединяя пробелом
                        # (вместо запятой, чтобы текст читался более естественно)
                        returns_parts = []
                        for child in returns_text.find_all(["span", "button"]):
                            text = child.get_text(strip=True)
                            if text:
                                returns_parts.append(text)

                        # Соединяем все части текста
                        product_data["returns"] = " ".join(returns_parts)
                    else:
                        product_data["returns"] = ""
                else:
                    product_data["returns"] = ""
                # 6-7. Извлекаем информацию о доставке (Shipping и Delivery)
                shipping_container = soup.find(
                    "div", {"data-testid": "d-shipping-minview"}
                )
                if not shipping_container:
                    # Резервный поиск по классу
                    shipping_container = soup.find(
                        "div", {"class": "vim d-shipping-minview"}
                    )

                if shipping_container:
                    # Ищем Shipping внутри контейнера
                    shipping_block = shipping_container.find(
                        "div",
                        {
                            "data-testid": "ux-labels-values",
                            "class": lambda c: c and "ux-labels-values--shipping" in c,
                        },
                    )
                    if shipping_block:
                        shipping_content = shipping_block.find(
                            "div", {"class": "ux-labels-values__values-content"}
                        )
                        if shipping_content:
                            # Обрабатываем первую строку с ценой и методом доставки
                            first_line_parts = []
                            for span in shipping_content.select(
                                "div:first-child > span.ux-textspans"
                            ):
                                text = span.get_text(strip=True)
                                if text and not text.startswith("See details"):
                                    first_line_parts.append(text)

                            # Обрабатываем вторую строку с информацией о местоположении
                            location_text = ""
                            location_span = shipping_content.select_one(
                                "div:nth-child(2) > span.ux-textspans--SECONDARY"
                            )
                            if location_span:
                                location_text = location_span.get_text(strip=True)

                            # Собираем всю информацию о доставке
                            shipping_info = []
                            if first_line_parts:
                                shipping_info.append(" ".join(first_line_parts))
                            if location_text:
                                shipping_info.append(location_text)

                            # Ищем информацию о комбинированной доставке
                            combined_shipping = shipping_container.find(
                                "span",
                                string=lambda s: s and "Save on combined shipping" in s,
                            )
                            if combined_shipping:
                                shipping_info.append("Save on combined shipping")

                            product_data["shipping"] = ", ".join(shipping_info)
                        else:
                            product_data["shipping"] = ""
                    else:
                        product_data["shipping"] = ""

                    # Обработка информации о доставке (Delivery)
                    delivery_block = shipping_container.find(
                        "div", {"class": "ux-labels-values--deliverto"}
                    )

                    if delivery_block:
                        delivery_content_div = delivery_block.find(
                            "div", {"class": "ux-labels-values__values-content"}
                        )
                        if delivery_content_div:
                            delivery_info = []

                            # Первая строка - даты доставки
                            first_div = delivery_content_div.find("div")

                            if first_div:
                                delivery_text = ""

                                # Ищем основной текст и выделенные даты
                                main_spans = first_div.find_all(
                                    "span", {"class": "ux-textspans"}, recursive=False
                                )

                                # Собираем текст и даты
                                for span in main_spans:
                                    # Исключаем span-элементы, содержащие информационный всплывающий блок
                                    if "ux-textspans__custom-view" not in span.get(
                                        "class", []
                                    ) and not span.has_attr("role"):
                                        delivery_text += span.get_text(strip=True) + " "

                                if delivery_text.strip():
                                    delivery_info.append(delivery_text.strip())

                            # Вторая строка - примечание о сроках
                            second_div = (
                                delivery_content_div.find_all("div")[1]
                                if len(delivery_content_div.find_all("div")) > 1
                                else None
                            )
                            if second_div:
                                notes = []
                                for span in second_div.find_all(
                                    "span",
                                    {
                                        "class": lambda c: c
                                        and "ux-textspans--SECONDARY" in c
                                    },
                                ):
                                    notes.append(span.get_text(strip=True))

                                if notes:
                                    delivery_info.append(" ".join(notes))

                            # Третья строка - информация об отправке
                            third_div = (
                                delivery_content_div.find_all("div")[2]
                                if len(delivery_content_div.find_all("div")) > 2
                                else None
                            )
                            if third_div:
                                shipping_info = []

                                # Собираем текст из всех span элементов
                                for span in third_div.find_all(
                                    "span",
                                    {
                                        "class": lambda c: c
                                        and "ux-textspans--SECONDARY" in c
                                    },
                                ):
                                    shipping_info.append(span.get_text(strip=True))

                                # Собираем текст из всех ссылок
                                for link in third_div.find_all("a"):
                                    span = link.find(
                                        "span",
                                        {
                                            "class": lambda c: c
                                            and "ux-textspans--SECONDARY" in c
                                        },
                                    )
                                    if span:
                                        shipping_info.append(span.get_text(strip=True))

                                if shipping_info:
                                    delivery_info.append(" ".join(shipping_info))

                            # Собираем всю информацию в одну строку с разделителями
                            product_data["delivery"] = ", ".join(delivery_info)
                        else:
                            product_data["delivery"] = ""
                    else:
                        product_data["delivery"] = ""
                else:
                    product_data["shipping"] = ""
                    product_data["delivery"] = ""
                # 8. Извлекаем характеристики
                specifications = {}

                # Метод 1: Извлечение из x-prp-product-details (первый формат)
                specs_div = soup.find("div", {"class": "x-prp-product-details"})
                if specs_div:
                    spec_rows = specs_div.find_all(
                        "div", {"class": "x-prp-product-details_row"}
                    )
                    for row in spec_rows:
                        cols = row.find_all(
                            "div", {"class": "x-prp-product-details_col"}
                        )
                        for col in cols:
                            name = col.find(
                                "span", {"class": "x-prp-product-details_name"}
                            )
                            value = col.find(
                                "span", {"class": "x-prp-product-details_value"}
                            )
                            if name and value:
                                spec_name = name.get_text(strip=True)
                                spec_value = value.get_text(strip=True)
                                specifications[spec_name] = spec_value
                                # Добавляем ключ в множество всех ключей
                                spec_keys.add(spec_name)

                # Метод 2: Извлечение из vim x-about-this-item (второй формат)
                if not specifications:
                    about_item_div = soup.find(
                        "div", {"class": "vim x-about-this-item"}
                    )
                    if about_item_div:
                        spec_items = about_item_div.find_all(
                            "dl", {"class": "ux-labels-values"}
                        )
                        for item in spec_items:
                            name = item.find(
                                "dt", {"class": "ux-labels-values__labels"}
                            )
                            value = item.find(
                                "dd", {"class": "ux-labels-values__values"}
                            )
                            if name and value:
                                spec_name = name.get_text(strip=True)
                                spec_value = value.get_text(strip=True)
                                specifications[spec_name] = spec_value
                                # Добавляем ключ в множество всех ключей
                                spec_keys.add(spec_name)

                # Сохраняем характеристики как JSON-строку
                product_data["specifications"] = json.dumps(specifications)

                # Добавляем характеристики как отдельные поля в product_data
                for key, value in specifications.items():
                    product_data[key] = value

                # Добавляем данные в список
                data.append(product_data)

            except Exception as e:
                print(f"Ошибка при обработке {html_file.name}: {str(e)}")
                data.append(
                    {
                        "filename": html_file.name,
                        "title": "",
                        "url": "",
                        "price": "",
                        "image_1": "",
                        "image_2": "",
                        "image_3": "",
                        "condition": "",
                        "returns": "",
                        "shipping": "",
                        "delivery": "",
                    }
                )

    # Создаем DataFrame с учетом всех возможных ключей характеристик
    # Базовые колонки, которые есть у всех товаров
    base_columns = [
        "filename",
        "title",
        "category",
        "url",
        "price",
        "image_1",
        "image_2",
        "image_3",
        "condition",
        "returns",
        "shipping",
        "delivery",
    ]

    # Добавляем все уникальные ключи характеристик как отдельные колонки
    all_columns = base_columns + sorted(spec_keys)

    # Преобразуем данные в DataFrame, заполняя отсутствующие колонки пустыми строками
    df_data = []
    for item in data:
        row = {col: item.get(col, "") for col in all_columns}
        df_data.append(row)

    df = pd.DataFrame(df_data, columns=all_columns)
    df.to_csv("product_details.csv", index=False, encoding="utf-8", sep=";")

    print(f"Обработано {len(data)} файлов, данные сохранены в product_details.csv")


async def main():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False
        )  # Set headless=True in production

        # Create new context with optimizations
        context = await browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            permissions=["geolocation"],
            device_scale_factor=1.0,
            has_touch=True,
            ignore_https_errors=True,
        )

        # Disable loading of images, fonts and other media files
        await context.route(
            "**/*",
            lambda route, request: (
                route.abort()
                if request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_()
            ),
        )

        # Create new page
        page = await context.new_page()

        # Navigate to the website (replace with your target URL)
        await page.goto("https://www.tikleap.com/")  # Replace with your actual URL
        await asyncio.sleep(50)

        # Wait for the postal code element to appear and click it
        postal_code_button = await page.wait_for_selector(
            'span:text("Wpisz kod pocztowy")'
        )
        await postal_code_button.click()

        # Wait for the input field to appear
        postal_code_input = await page.wait_for_selector(
            'input[aria-describedby="hnf-postalcode-helper"]'
        )

        # Type the postal code
        await postal_code_input.fill("22-100")

        # Press Enter
        await postal_code_input.press("Enter")

        # Wait a moment to see the result (adjust as needed)
        await asyncio.sleep(5)

        # Close browser
        await browser.close()


if __name__ == "__main__":
    get_html()
    # scrap_html()
    # main_realoem()
    # get_html()
    # asyncio.run(main())
