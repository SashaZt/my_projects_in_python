import json
from pathlib import Path

from bs4 import BeautifulSoup
from config.logger import logger

current_directory = Path.cwd()
config_directory = current_directory / "config"
html_directory = current_directory / "html_pages" / "guitarcenter.pl"


def extract_product_data(data):

    title = data.find("h1", attrs={"itemprop": "name"})
    if title is not None:
        title = title.text.strip()
    price = data.find("td", attrs={"itemprop": "price"}).get("content")
    gtin13 = data.find("meta", attrs={"itemprop": "gtin13"}).get("content")

    # Извлечение доступности по частичному совпадению классов
    def has_tahoma_alignleft(tag):
        return (
            tag.name == "p"
            and "tahoma13" in tag.get("class", [])
            and "alignleft" in tag.get("class", [])
        )

    availability_tag = data.find(has_tahoma_alignleft)
    availability = None
    if availability_tag:
        availability = availability_tag.text.strip().split("\n")[0].strip()
    else:
        logger.warning("Тег с доступностью не найден")

    all_data = {
        "title": title,
        "price": price,
        "article_number": gtin13,
        "availability": availability,
    }
    return all_data


def pars_htmls():
    logger.info(f"Обрабатываем директорию: {html_directory}")
    all_data = []

    # Проверяем наличие HTML-файлов
    html_files = list(html_directory.glob("*.html"))

    # Обрабатываем каждый HTML-файл
    for html_file in html_files:
        try:
            with html_file.open(encoding="utf-8") as file:
                content = file.read()

            # Парсим HTML
            soup = BeautifulSoup(content, "lxml")
            result = extract_product_data(soup)

            if result:
                logger.info(f"Собранные данные из {html_file.name}: {result}")
                all_data.append(result)
            else:
                logger.warning(f"Не удалось извлечь данные из {html_file.name}")

        except UnicodeDecodeError as e:
            logger.error(f"Ошибка кодировки в файле {html_file.name}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обработке файла {html_file.name}: {e}")

    # Сохраняем данные в JSON
    if all_data:
        output_file = current_directory / "guitarcenter_data.json"
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Данные сохранены в {output_file}")

    return all_data


if __name__ == "__main__":
    parsed_data = pars_htmls()
    logger.info(f"Обработано файлов: {len(parsed_data)}")
