from selectolax.parser import HTMLParser
import json
import glob
import os
import re
import pandas as pd


current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
all_hotels = os.path.join(temp_path, "all_hotels")
hotel_path = os.path.join(temp_path, "hotel")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(all_hotels, exist_ok=True)
os.makedirs(hotel_path, exist_ok=True)


def parsing_group():
    # Указываем путь к папке с файлами
    folder = os.path.join(hotel_path, "*.html")
    files_html = glob.glob(folder)
    all_datas = []
    for item in files_html:
        match = re.search(r"(\d+)\.html$", item)
        if match:
            number = match.group(1)
            url = f"https://catalog.weidmueller.com/catalog/Start.do?localeId=ru&ObjectID=group{number}"

        with open(item, encoding="utf-8") as file:
            src = file.read()

        parser = HTMLParser(src)
        # Extract all the text from the element
        breadcrumb_div = parser.css(".newBreadcrumb")
        texts = [node.text(strip=True) for node in breadcrumb_div]

        # Join the texts with commas
        result = ", ".join(texts)

        img_src = None
        td_elements = parser.css('td[style="text-align: right;"]')
        if td_elements:
            img_tag = td_elements[0].css_first("img")
            if img_tag:
                img_src_node = img_tag.attributes["src"]
                img_src = f"https://catalog.weidmueller.com{img_src_node}"
            else:
                img_src = "No img"
        else:
            print("No td element with the specified style found.")

        # Find the td element with the specified class and id
        td_element = parser.css_first("td.text#SVGroupDescription")

        text_content = ""
        if td_element:
            text_content = (
                td_element.text()
                .replace("\n", " ")
                .replace("\r", " ")
                .replace("<br />", " ")
                .replace("<br>", " ")
                .strip()
            )
            # Remove extra spaces
            text_content = re.sub(" +", " ", text_content)

        datas = {
            "1 - URL": url,
            "2 - вхождение группы": result,
            "3 - Описание группы": text_content,
            "4 - ссылка на изображение для этой группы": img_src,
        }
        all_datas.append(datas)

    # Convert the list of dictionaries to a pandas DataFrame
    df = pd.DataFrame(all_datas)

    # Save the DataFrame to a CSV file with a semicolon separator
    df.to_csv("parsing_group.csv", index=False, encoding="utf-8", sep=";")


def parsing_products():
    # Указываем путь к папке с файлами
    folder = os.path.join(all_hotels, "*.html")
    files_html = glob.glob(folder)
    all_datas = []
    for item in files_html:
        match = re.search(r"(\d+)\.html$", item)
        if match:
            number = match.group(1)
            url = f"https://catalog.weidmueller.com/catalog/Start.do?localeId=ru&ObjectID={number}"
        with open(item, encoding="utf-8") as file:
            src = file.read()
        parser = HTMLParser(src)
        # Extract all the text from the element
        breadcrumb_div = parser.css(".newBreadcrumb")
        texts = [node.text(strip=True) for node in breadcrumb_div]
        # Find the div element with the specified class
        div_element = parser.css_first("div.zoomWrapper")

        # Extract the 'data-zoom-image' attribute from the img tag inside this div element
        img_src = None
        if div_element:
            img_tag = div_element.css_first("img")
            if img_tag:
                data_zoom_image = img_tag.attributes.get("data-zoom-image")
                img_src = f"https://catalog.weidmueller.com{data_zoom_image}"
            else:
                img_src = "No img"
        else:
            img_src = "No img"
            print("No div element with the specified class found.")
        # Join the texts with commas
        result = ", ".join(texts)
        # Find the table rows
        rows = parser.css("table.products.tabview.noTopMargin tr")

        data_dict = {}
        count = 0

        # Iterate through each row and extract key-value pairs
        for row in rows:
            if count >= 5:
                break
            key_td = row.css_first("td.myListLable")
            value_td = row.css_first("td.myListValue")

            if key_td and value_td:
                key = key_td.text(strip=True)
                value = value_td.text(strip=True).replace(
                    "\u00a0", " "
                )  # Replace non-breaking spaces with regular spaces
                data_dict[key] = value
                count += 1

        datas = {
            "1 - URL": url,
            "2 - вхождение группы": result,
            "3- Ссылка на ОСНОВНОЕ изображение": img_src,
        }
        # Add the data_dict to datas
        datas.update(data_dict)

        all_datas.append(datas)

    # Optionally, save all_datas to a CSV file
    df = pd.DataFrame(all_datas)
    df.to_csv("parsing_products.csv", index=False, encoding="utf-8", sep=";")


if __name__ == "__main__":
    # parsing_group()
    parsing_products()
