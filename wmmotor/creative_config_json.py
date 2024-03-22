import json

# Входные данные
cookies = {
    'weblogin[name]': 'kupujwpl%40gmail.com',
    'weblogin[save]': '1',
    'sid': '617c2022093e7c9e332fba1b709c10b9',
}

headers = {
    'authority': 'www.wmmotor.pl',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'weblogin[name]=kupujwpl%40gmail.com; weblogin[save]=1; sid=617c2022093e7c9e332fba1b709c10b9',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://www.wmmotor.pl/hurtownia/logowanie.php?ref=ZHJ6ZXdvLnBocA%3D%3D',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
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
