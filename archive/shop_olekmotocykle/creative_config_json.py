import json

# Входные данные
cookies = {
    "cf_clearance": "hwEFoNcsY1lLS7x9XV79Bp4BW1s9tGFJfPdiesc2xjE-1716198933-1.0.1.1-nWcSZ780s4r1McH1SFDBY.Jes0s_WstGQMCb1MUJlt2yDE5m8L46eRTGGHizpVP4jTPJKl3y1lHZXO_CK7wDgA",
    "_clck": "9hbfrd%7C2%7Cflx%7C0%7C1589",
    "isMobileDevice": "0",
    ".cdneshopsid": "+U+PZuJY8Jq+7hIjsDuRjeSCqz5E9WKDAqjYxQtfjo0yFG5Wo0xj8lZbh2quZHlWN1r+QU17aJWydjAahQ|003",
    "LastSeenProducts": "",
    "lastCartId": "-1",
    "_gid": "GA1.2.415830457.1716198964",
    "_gat_gtag_UA_232962489_1": "1",
    "_gat_UA-232962489-1": "1",
    "_clsk": "vubf6h%7C1716199396757%7C2%7C1%7Cw.clarity.ms%2Fcollect",
    "_ga_YBF7Q20GFD": "GS1.1.1716198932.6.1.1716199395.0.0.0",
    "_ga": "GA1.1.2029087977.1716198964",
}

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    # 'cookie': 'cf_clearance=hwEFoNcsY1lLS7x9XV79Bp4BW1s9tGFJfPdiesc2xjE-1716198933-1.0.1.1-nWcSZ780s4r1McH1SFDBY.Jes0s_WstGQMCb1MUJlt2yDE5m8L46eRTGGHizpVP4jTPJKl3y1lHZXO_CK7wDgA; _clck=9hbfrd%7C2%7Cflx%7C0%7C1589; isMobileDevice=0; .cdneshopsid=+U+PZuJY8Jq+7hIjsDuRjeSCqz5E9WKDAqjYxQtfjo0yFG5Wo0xj8lZbh2quZHlWN1r+QU17aJWydjAahQ|003; LastSeenProducts=; lastCartId=-1; _gid=GA1.2.415830457.1716198964; _gat_gtag_UA_232962489_1=1; _gat_UA-232962489-1=1; _clsk=vubf6h%7C1716199396757%7C2%7C1%7Cw.clarity.ms%2Fcollect; _ga_YBF7Q20GFD=GS1.1.1716198932.6.1.1716199395.0.0.0; _ga=GA1.1.2029087977.1716198964',
    "dnt": "1",
    "priority": "u=0, i",
    "referer": "https://shop.olekmotocykle.com/produkty/akcesoria-motocyklowe-i-atv,2,1498",
    "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"125.0.6422.61"',
    "sec-ch-ua-full-version-list": '"Google Chrome";v="125.0.6422.61", "Chromium";v="125.0.6422.61", "Not.A/Brand";v="24.0.0.0"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
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
