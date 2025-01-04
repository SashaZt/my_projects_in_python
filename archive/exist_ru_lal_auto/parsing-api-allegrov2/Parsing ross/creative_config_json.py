import json

# Входные данные
cookies = {
    'PHPSESSID': 'fhpr2g3lnbouagne3ahm17fan4',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'Connection': 'keep-alive',
    # 'Cookie': 'PHPSESSID=fhpr2g3lnbouagne3ahm17fan4',
    'DNT': '1',
    'Referer': 'https://lal-auto.ru/?action=catalog_price_view&code=713000500&id_currency=1&cross_advance=0&cross_advance=1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

# Формирование словаря для сохранения в JSON
config_data = {
    "headers": headers,
    "cookies": cookies
}

# Запись в JSON-файл
with open('config.json', 'w', encoding='utf-8') as f:
    json.dump(config_data, f, ensure_ascii=False, indent=4)

print("Config file 'config.json' has been created successfully.")
