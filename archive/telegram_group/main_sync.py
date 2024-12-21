import csv
import os
import random
import re
import time
from datetime import datetime

from telethon.errors import SessionPasswordNeededError
from telethon.sync import TelegramClient

api_id = "29172008"  # Замените на ваш API_ID
api_hash = "0d9f3518bc77ce87ddb339f50357d49d"  # Замените на ваш API_HASH
phone = "+380961456209"  # Замените на ваш номер телефона
username = "https://t.me/milirud_official"  # Замените на вашу ссылку на группу (например, 'https://t.me/joinchat/AAAAAFf4hjtpr6eDZ-bjFg')

client = TelegramClient(phone, api_id, api_hash)

client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    try:
        client.sign_in(phone, input("Enter the code: "))
    except SessionPasswordNeededError:
        client.sign_in(password="")

# Получение информации о группе
entity = client.get_entity(username)
messages = client.iter_messages(entity)
with open(f"data.csv", "w", errors="ignore", encoding="utf-8") as file_csv:
    writer = csv.writer(file_csv, delimiter=",", lineterminator="\r")
    writer.writerow(
        (
            "Handle",
            "Title",
            "Body(HTML)",
            "Vendor",
            "Type",
            "Tags",
            "Published",
            "Option1" "Name",
            "Option1" "Value",
            "Option2 Name",
            "Option2 Value",
            "Option3 Name",
            "Option3 Value",
            "Variant SKU",
            "Variant Grams",
            "Variant Inventory Tracker",
            "Variant Inventory Qty",
            "Variant Inventory Policy",
            "Variant Fulfillment Service",
            "Variant Price",
            "Variant Compare At Price",
            "Variant Requires Shipping",
            "Variant Taxable",
            "Variant Barcode",
            "Image Src",
            "Image Alt Text",
            "Gift Card",
            "Google Shopping/MPN",
            "Google Shopping/Age Group",
            "Google Shopping/Gender",
            "Google Shopping/Google Product Category",
            "SEO Title, SEO Description",
            "Google Shopping/AdWords Grouping",
            "Google Shopping/AdWords Labels",
            "Google Shopping/Condition",
            "Google Shopping/Custom Product",
            "Google Shopping/Custom Label 0",
            "Google Shopping/Custom Label 1",
            "Google Shopping/Custom Label 2",
            "Google Shopping/Custom Label 3",
            "Google Shopping/Custom Label 4",
            "Variant Image",
            "Variant Weight Unit",
        )
    )
for message in messages:

    target_date = datetime.strptime("15.05.2023", "%d.%m.%Y")

    if message.text:
        pause_time = random.uniform(60, 70)
        lines = message.text.split("\n")
        if len(lines) >= 8 and re.match(
            r"^МРРЦ:", lines[-1]
        ):  # Проверяем, что последняя строка начинается с "МРРЦ:"
            print(message.id)
            print(message.date)
            # print(message.text)
            name_photo = lines[0].replace("Арт ", "art")
            Title = lines[1]
            Body_HTML = ", ".join(
                lines[2:-1]
            )  # Объединяем все строки, кроме первой, второй и последней, с помощью запятой
            Variant_SKU = lines[0]
            price = lines[-1]
            Variant_Price = re.findall(r"\d+", price)[0]
            if message.photo:  # Если в сообщении есть фото
                filename = f"photo/{message.id}_{name_photo}.jpg"
                if not os.path.isfile(filename):  # Если файл не существует
                    try:
                        client.download_media(message.photo, filename)
                    except Exception as e:
                        print(f"Не удалось скачать медиафайл. Ошибка: {e}")
            data = [
                message.id,
                Title,
                Body_HTML,
                "Greenzda",
                "Clothing",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                Variant_SKU,
                "",
                "",
                "100",
                "deny",
                "manual",
                Variant_Price,
                "",
                "",
                "",
                "",
                f"https://cdn.shopify.com/s/files/1/0699/5620/6899/files/{message.id}_{name_photo}.jpg",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
            print(data)
            with open(f"data.csv", "a", errors="ignore", encoding="utf-8") as file:
                writer = csv.writer(file, delimiter=",", lineterminator="\r")
                writer.writerow((data))
        print(f"Пауза в {pause_time}")
        time.sleep(pause_time)
