import requests
import json
import os

# Создание временных папок
current_directory = os.getcwd()
temp_path = os.path.join(current_directory, "temp")
json_path = os.path.join(temp_path, "json")

# Создание директории, если она не существует
os.makedirs(temp_path, exist_ok=True)
os.makedirs(json_path, exist_ok=True)

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "dnt": "1",
    "origin": "https://www.g2g.com",
    "priority": "u=1, i",
    "referer": "https://www.g2g.com/",
    "sec-ch-ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

params = {
    "seo_term": "wow-classic-era-item",
    "q": "Arcanite Bar",
    "sort": "lowest_price",
    "page": "2",
    "page_size": "48",
    "currency": "USD",
    "country": "UA",
}
keyword = params["q"]
# url = "https://sls.g2g.com/offer/search"
# response = requests.get(url, params=params, headers=headers)
# json_data = response.json()
filename = os.path.join(json_path, f"0.json")
# with open(filename, "w", encoding="utf-8") as f:
#     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

client_name = "Allbestfory"
competitor_name = "CNLTeam"
# Условия для минимального и максимального процента разбежности
minimum_percentage = 1
maximum_percentage = 3

with open(filename, encoding="utf-8") as f:
    data = json.load(f)
datas_json = data["payload"]["results"]
all_datas = []
for data_json in datas_json:
    username = data_json["username"]
    unit_price = data_json["unit_price"]
    title = data_json["title"]
    offer_id = data_json["offer_id"]
    all_data = {
        "title": title,
        "offer_id": offer_id,
        "username": username,
        "unit_price": unit_price,
    }
    all_datas.append(all_data)


# Фильтрация данных для клиента и конкурента с учетом ключевого слова и уникального client_offer_id
client_data = {
    item["offer_id"]: item
    for item in all_datas
    if client_name in item["username"] and keyword in item["title"]
}
competitor_data = {
    item["offer_id"]: item
    for item in all_datas
    if competitor_name in item["username"] and keyword in item["title"]
}

# Сравнение цен
price_comparison = set()

for client_offer_id, client_item in client_data.items():
    for competitor_offer_id, competitor_item in competitor_data.items():
        if keyword in client_item["title"] and keyword in competitor_item["title"]:
            comparison = (
                client_item["title"],
                client_offer_id,
                client_item["unit_price"],
                competitor_item["unit_price"],
                (
                    "competitor"
                    if competitor_item["unit_price"] < client_item["unit_price"]
                    else "client"
                ),
            )
            price_comparison.add(comparison)

# Вывод результата
if price_comparison:
    for item in price_comparison:
        client_price = item[2]
        competitor_price = item[3]
        price_difference_percentage = round(
            (abs(client_price - competitor_price) / competitor_price) * 100, 2
        )
        if minimum_percentage <= price_difference_percentage <= maximum_percentage:
            print(
                {
                    "client_offer_id": item[1],
                    "client_price": client_price,
                    "competitor_price": competitor_price,
                    "cheaper": item[4],
                    "price_difference_percentage": price_difference_percentage,
                }
            )
else:
    print("Нет товаров с различием в цене между клиентом и конкурентом.")
