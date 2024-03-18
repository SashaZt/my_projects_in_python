import cloudscraper
from bs4 import BeautifulSoup


def main():
    """Рабочий парсер для обхода Cloudflare через requests"""
    import cloudscraper
    from bs4 import BeautifulSoup

    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    })
    # Данные для прокси
    PROXY_HOST = '37.233.3.100'
    PROXY_PORT = 9999
    PROXY_USER = 'proxy_alex'
    PROXY_PASS = 'DbrnjhbZ88'
    # proxies = {
    #     'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    #     'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
    # }
    proxies = {"http": f"http://{PROXY_HOST}:{PROXY_PORT}", f"https": f"http://{PROXY_HOST}:{PROXY_PORT}"}
    html = scraper.get("https://2ip.ua/ru/", proxies=proxies).content
    with open("c:\\salomon_pl\\html_product\\результат.html", "w", encoding="utf-8") as file:
        file.write(html.decode('utf-8'))

    #
    # # Настройка для requests чтобы использовать прокси
    # proxies = {
    #     'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
    #     'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
    # }
    # import requests
    # import urllib.parse
    # from bs4 import BeautifulSoup
    #
    # sa_key = '5762b6b89e9e4462baf572e921fade22'  # paste here
    # sa_api = 'https://api.scrapingant.com/v2/general'
    # qParams = {'url': 'https://combomed.ru/antigrippin-simziya', 'x-api-key': sa_key}
    # reqUrl = f'{sa_api}?{urllib.parse.urlencode(qParams)}'
    #
    # r = requests.get(reqUrl)
    # # print(r.text) # --> html
    # soup = BeautifulSoup(r.content, 'html.parser')
    # print(soup)




if __name__ == '__main__':
    main()
