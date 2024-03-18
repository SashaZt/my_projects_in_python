import requests
import cloudscraper
cookies = {
    '_ga': 'GA1.2.1489364981.1691669137',
    '_gid': 'GA1.2.1219165774.1691669137',
    '_ga_42S2YTNE7Q': 'GS1.2.1691669137.1.0.1691669137.0.0.0',
    'svt-buyers': '2fad7e5212f4c19f9f58e825bef32e82baa53818',
}

headers = {
    'authority': 'www.vaurioajoneuvo.fi',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    # 'cookie': '_ga=GA1.2.1489364981.1691669137; _gid=GA1.2.1219165774.1691669137; _ga_42S2YTNE7Q=GS1.2.1691669137.1.0.1691669137.0.0.0; svt-buyers=2fad7e5212f4c19f9f58e825bef32e82baa53818',
    'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
}
scraper = cloudscraper.create_scraper()
response = scraper.get('https://www.vaurioajoneuvo.fi/', cookies=cookies, headers=headers)
print(response.text)
