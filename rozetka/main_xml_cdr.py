import html
import re
import xml.etree.ElementTree as ET

import pandas as pd


def extract_xml_to_csv(
    xml_file, categories_csv="categories.csv", products_csv="products.csv"
):
    # Парсим XML файл
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Извлекаем информацию о магазине
    shop = root.find("shop")
    shop_name = shop.find("name").text
    shop_company = shop.find("company").text

    # Сохраняем информацию о магазине в отдельный конфиг
    shop_info = {"name": shop_name, "company": shop_company, "currencies": {}}

    # Извлекаем валюты
    currencies = shop.find("currencies")
    for currency in currencies.findall("currency"):
        currency_id = currency.get("id")
        currency_rate = currency.get("rate")
        shop_info["currencies"][currency_id] = currency_rate

    # Сохраняем информацию о магазине в JSON
    import json

    with open("shop_config.json", "w", encoding="utf-8") as f:
        json.dump(shop_info, f, ensure_ascii=False, indent=4)

    # Извлекаем категории
    categories_data = []
    categories = shop.find("categories")
    for category in categories.findall("category"):
        category_id = category.get("id")
        category_name = category.text
        category_rz_id = category.get("rz_id", "")

        categories_data.append(
            {"id": category_id, "name": category_name, "rz_id": category_rz_id}
        )

    # Создаем DataFrame для категорий и сохраняем в CSV
    categories_df = pd.DataFrame(categories_data)
    categories_df.to_csv(categories_csv, index=False, encoding="utf-8")
    print(f"Сохранено {len(categories_data)} категорий в файл {categories_csv}")

    # Извлекаем товары
    offers_data = []
    offers = shop.find("offers")

    for offer in offers.findall("offer"):
        offer_data = {
            "id": offer.get("id"),
            "available": "true" if offer.get("available") == "true" else "false",
        }

        # Извлекаем обязательные поля
        for field in ["price", "currencyId", "name", "categoryId"]:
            element = offer.find(field)
            offer_data[field] = element.text if element is not None else ""

        # Извлекаем количество на складе (может быть разный тег)
        stock_quantity = offer.find("stock_quantity")
        quantity_in_stock = offer.find("quantity_in_stock")

        if stock_quantity is not None:
            offer_data["stock_quantity"] = stock_quantity.text
        elif quantity_in_stock is not None:
            offer_data["stock_quantity"] = quantity_in_stock.text
        else:
            offer_data["stock_quantity"] = "0"

        # Извлекаем дополнительные поля
        for field in [
            "price_old",
            "oldprice",
            "price_promo",
            "vendor",
            "article",
            "vendorCode",
            "barcode",
            "url",
        ]:
            element = offer.find(field)
            if element is not None:
                offer_data[field] = element.text

        # Извлекаем украинскую версию названия, если есть
        name_ua = offer.find("name_ua")
        if name_ua is not None:
            offer_data["name_ua"] = name_ua.text

        # Извлекаем описание
        description = offer.find("description")
        if description is not None:
            # Извлекаем текст из CDATA секции
            desc_text = description.text

            # Если есть CDATA, извлекаем её содержимое
            if desc_text and "<![CDATA[" in desc_text:
                cdata_content = re.search(
                    r"<!\[CDATA\[(.*?)\]\]>", desc_text, re.DOTALL
                )
                if cdata_content:
                    offer_data["description"] = cdata_content.group(1)
            else:
                offer_data["description"] = desc_text if desc_text else ""

        # Извлекаем украинскую версию описания, если есть
        description_ua = offer.find("description_ua")
        if description_ua is not None:
            # Извлекаем текст из CDATA секции
            desc_ua_text = description_ua.text

            # Если есть CDATA, извлекаем её содержимое
            if desc_ua_text and "<![CDATA[" in desc_ua_text:
                cdata_content = re.search(
                    r"<!\[CDATA\[(.*?)\]\]>", desc_ua_text, re.DOTALL
                )
                if cdata_content:
                    offer_data["description_ua"] = cdata_content.group(1)
            else:
                offer_data["description_ua"] = desc_ua_text if desc_ua_text else ""

        # Извлекаем изображения
        pictures = offer.findall("picture")
        for i, picture in enumerate(pictures, start=1):
            if picture.text:
                offer_data[f"picture{i}"] = picture.text.strip()

        # Извлекаем параметры товара
        params = offer.findall("param")
        for i, param in enumerate(params, start=1):
            param_name = param.get("name", "")
            param_value = param.text or ""

            # Извлекаем содержимое CDATA, если есть
            if param_value and "<![CDATA[" in param_value:
                cdata_content = re.search(
                    r"<!\[CDATA\[(.*?)\]\]>", param_value, re.DOTALL
                )
                if cdata_content:
                    param_value = cdata_content.group(1)

            offer_data[f"param_name{i}"] = param_name
            offer_data[f"param_value{i}"] = param_value

            # Добавляем paramid и valueid, если есть
            paramid = param.get("paramid", "")
            if paramid:
                offer_data[f"param_paramid{i}"] = paramid

            valueid = param.get("valueid", "")
            if valueid:
                offer_data[f"param_valueid{i}"] = valueid

        offers_data.append(offer_data)

    # Создаем DataFrame для товаров и сохраняем в CSV
    offers_df = pd.DataFrame(offers_data)
    offers_df.to_csv(products_csv, index=False, encoding="utf-8")
    print(f"Сохранено {len(offers_data)} товаров в файл {products_csv}")

    return categories_df, offers_df


# Пример использования функции
if __name__ == "__main__":
    categories_df, offers_df = extract_xml_to_csv("export-2025-03-16_10-48-57.xml")

    # # Выводим первые несколько строк для проверки
    # print("\nПервые 5 категорий:")
    # print(categories_df.head())

    # print("\nПервые 5 товаров:")
    # print(offers_df.head())

    # print("\nСписок всех столбцов товаров:")
    # print(offers_df.columns.tolist())
