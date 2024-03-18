cookies = {
        'LangId': '2',
        'MAXCOST': '0',
        'MINCOST': '0',
        'SIDS': '0',
        'avrsid': 'c2noes7uulnk00he5u1u96jcp5',
        'lst-cat': '',
        '_ga_HSTS5N7TNH': 'GS1.1.1692187785.1.0.1692187785.60.0.0',
        '_ga': 'GA1.1.1515260137.1692187785',
        '_gcl_au': '1.1.700059413.1692187785',
        '_fbp': 'fb.2.1692187785515.177623426',
    }

headers = {
        'authority': 'www.avtoradosti.com.ua',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'LangId=2; MAXCOST=0; MINCOST=0; SIDS=0; avrsid=c2noes7uulnk00he5u1u96jcp5; lst-cat=; _ga_HSTS5N7TNH=GS1.1.1692187785.1.0.1692187785.60.0.0; _ga=GA1.1.1515260137.1692187785; _gcl_au=1.1.700059413.1692187785; _fbp=fb.2.1692187785515.177623426',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://www.avtoradosti.com.ua/ua/katalog-tovara/avtolampy/p_1.html',
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
headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in cookies.items()])