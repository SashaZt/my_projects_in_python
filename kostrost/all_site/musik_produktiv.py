import json
from pathlib import Path

from bs4 import BeautifulSoup
from config.logger import logger

current_directory = Path.cwd()
config_directory = current_directory / "config"
json_data_directory = current_directory / "json_data"
html_directory = current_directory / "html_pages" / "www.musik-produktiv.com"
output_file = json_data_directory / "www.musik-produktiv.com.json"


# Предполагается, что product_json — это список словарей, как в вашем примере
def extract_product_data(data):
    try:
        # Если data — строка, парсим её как JSON
        if isinstance(data, str):
            data = json.loads(data)

        # Находим первый элемент с "@type": "Product"
        product_json = next(
            (item for item in data if item.get("@type") == "Product"), None
        )
        if not product_json:
            raise ValueError("Продукт не найден в JSON")

        # Извлечение title
        title = product_json.get("name")
        if not title:
            raise ValueError("Название продукта не найдено")

        # Извлечение других полей
        price = product_json.get("offers", {}).get("price")
        sku = product_json.get("sku")

        all_data = {
            "title": title,
            "price": float(price) if price else None,
            "availability": "availability",
            "article_number": sku,
        }

        return all_data

    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при извлечении данных: {e}")
        return None


def pars_htmls():
    logger.info(f"Обрабатываем директорию: {html_directory}")
    all_data = []

    # Проверяем наличие HTML-файлов
    html_files = list(html_directory.glob("*.html"))

    # Обрабатываем каждый HTML-файл
    for html_file in html_files:
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML
        soup = BeautifulSoup(content, "lxml")
        scripts = soup.find_all("script", type="application/ld+json")

        if not scripts:
            logger.warning(
                f"В файле {html_file.name} не найдено скриптов с типом application/ld+json"
            )
            continue
        availability_tag = soup.find("div", class_="mp-availability").find("b")
        availability = availability_tag.text.strip() if availability_tag else None
        logger.info(f"Доступность: {availability}")
        price = soup.find("div", attrs={"class": "font-s"}).text.strip()
        logger.info(f"Цена: {price}")

        # Перебираем все скрипты JSON-LD
        for script in scripts:
            try:
                # Получаем текст скрипта и проверяем его наличие
                script_text = script.string

                # Извлекаем данные основного продукта
                main_product = extract_product_data(script_text)
                if main_product:
                    main_product["availability"] = availability
                    main_product["price"] = price.replace(" zł", "")
                    all_data.append(main_product)

                    break
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                # Или можно использовать print:
                logger.info(f"Ошибка парсинга JSON: {e}")
        else:
            logger.error("Product JSON не найден.")

    # Сохраняем данные в JSON
    if all_data:

        with output_file.open("w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Данные сохранены в {output_file}")

    return all_data


if __name__ == "__main__":
    parsed_data = pars_htmls()
    logger.info(f"Обработано файлов: {len(parsed_data)}")
