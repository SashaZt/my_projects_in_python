import bs4
import time
import re
import json
import cloudscraper
from bs4 import BeautifulSoup
import os

def main():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        # 'Cookie': 'form_key=Yv9mTf1bQx5qEH2r; PHPSESSID=1feea8e2974359c3cfd2632e35bd4a17; _pxhd=s8-ny9JSej4MU3SwnyRd9S8v8RZnIJJnbAaNEtm3DDxizC/zipZrWOoXbs2Y5sSmWMOkadBE3RpcwQA/kDlkZQ==:yApEOv-5kHz3xj0AvXPQrhPpFRCAQWylay/DJ5a2GvVgJL0JNsC/7CPnhWVFSef3q066c2w8M0Uz25XE4xMpqpF-4qRFldYfSko4hEIbofk=; UUID=e0629043-ff2a-41c9-985d-d271f3e0fb51; OptanonConsent=isGpcEnabled=0&datestamp=Wed+May+24+2023+12^%^3A47^%^3A37+GMT^%^2B0300+(^%^D0^%^92^%^D0^%^BE^%^D1^%^81^%^D1^%^82^%^D0^%^BE^%^D1^%^87^%^D0^%^BD^%^D0^%^B0^%^D1^%^8F+^%^D0^%^95^%^D0^%^B2^%^D1^%^80^%^D0^%^BE^%^D0^%^BF^%^D0^%^B0^%^2C+^%^D0^%^BB^%^D0^%^B5^%^D1^%^82^%^D0^%^BD^%^D0^%^B5^%^D0^%^B5+^%^D0^%^B2^%^D1^%^80^%^D0^%^B5^%^D0^%^BC^%^D1^%^8F)&version=202302.1.0&isIABGlobal=false&hosts=&genVendors=V8^%^3A0^%^2CV28^%^3A0^%^2CV18^%^3A0^%^2CV10^%^3A0^%^2CV4^%^3A0^%^2CV26^%^3A0^%^2CV12^%^3A0^%^2CV19^%^3A0^%^2CV11^%^3A0^%^2CV21^%^3A0^%^2CV22^%^3A0^%^2CV23^%^3A0^%^2CV7^%^3A0^%^2CV2^%^3A0^%^2CV25^%^3A0^%^2CV16^%^3A0^%^2CV14^%^3A0^%^2CV9^%^3A0^%^2CV27^%^3A0^%^2CV3^%^3A0^%^2CV13^%^3A0^%^2CV15^%^3A0^%^2CV6^%^3A0^%^2CV24^%^3A0^%^2CV5^%^3A0^%^2CV17^%^3A0^%^2C&consentId=4df5be68-cae1-45bd-9f32-a60e71262328&interactionCount=1&landingPath=NotLandingPage&groups=C0001^%^3A1^%^2CC0003^%^3A1^%^2CC0002^%^3A1^%^2CC0004^%^3A1; pxcts=02d81152-fa18-11ed-955b-44504c784759; _pxvid=016fb9c1-fa18-11ed-9fb2-522cb1e0961f; geoIp_country_code=^%^7B^%^22country_code^%^22^%^3A^%^22PL^%^22^%^7D; _px2=eyJ1IjoiMDI5MjEyYzAtZmExOC0xMWVkLTljYWYtMGQ2MDgzYTM4NjlhIiwidiI6IjAxNmZiOWMxLWZhMTgtMTFlZC05ZmIyLTUyMmNiMWUwOTYxZiIsInQiOjE2ODQ5MjE5NTYxMDcsImgiOiJhNmMwODE2M2Y5ZmYzY2EwMGQ0MTEzMWEzNGIxN2JmYzY4M2YxNTVkOTAwY2VlNTAyYTZmZGRkZTM1YzVjZmQ4In0=; OptanonAlertBoxClosed=2023-05-24T09:47:37.536Z; AMCV_DFBF2C1653DA80920A490D4B^%^40AdobeOrg=179643557^%^7CMCMID^%^7C65575658457533855045850372181627544039^%^7CMCAID^%^7CNONE^%^7CMCOPTOUT-1684928861s^%^7CNONE^%^7CvVersion^%^7C5.5.0; s_ecid=MCMID^%^7C65575658457533855045850372181627544039; AMCVS_DFBF2C1653DA80920A490D4B^%^40AdobeOrg=1; at_check=true; mbox=session^#69d3dbd9083045f082671c0978c46545^#1684923522; s_cc=true; _ga_Y9PJ3VZ8E4=GS1.1.1684921661.1.1.1684921661.60.0.0; _ga=GA1.1.831945971.1684921661; _gcl_au=1.1.1607385794.1684921661; _ga_Q3HF4EKNG8=GS1.1.1684921661.1.0.1684921661.0.0.0; _cs_c=0; _cs_cvars=^%^7B^%^7D; _cs_id=b6812439-e872-a182-fbdb-a1541d8e871a.1684921661.1.1684921661.1684921661.1.1719085661596; _cs_s=1.T.0.1684923461597; FPLC=5U1jlHWSw68HBizyLnUA8tFjLlj3SU8NatrrZII4dAKzTuan4gVmaEZTAy3O7T4lyvgq9Ccvep^%^2FwpsUcd0keDt1DdtpLfMz4McS8S^%^2Bw9sOJ^%^2BMjasB6Gmrf9744GWmw^%^3D^%^3D; FPID=FPID2.2.8R5Xrz7uQH637YWAsSq6SD6Hri6jd0b8SOMc^%^2BrIRISk^%^3D.1684921661',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }
    import cloudscraper
    import csv
    from bs4 import BeautifulSoup

    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False

    })
    # scraper = cloudscraper.create_scraper(
    #     request_kwargs={'verify': False, 'headers': headers, 'captcha': {'bypass': True}})
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
    r = scraper.get("https://www.salomon.com/pl-pl/shop-emea/product/alphacross-blast-j.html#color=45726") #, proxies=proxies
    html = r.content
    soup = BeautifulSoup(html, 'lxml')
    script_tag = soup.find('script', {'type': 'application/ld+json'})
    json_data = json.loads(script_tag.string)
    url_one_photo = json_data['image']
    base_url = url_one_photo.split('_')[0]
    print(base_url)


    alls_photo = set()  # Используем множество для хранения уникальных значений
    # try:
    #     photos_01 = soup.find('div', {'data-slider-variant': 'product-page-images'})
    # except:
    #     pattern = re.compile(r"swiper-slide.*")
    #     photos_01 = soup.find('div', class_=pattern)
    data_srcset_list = []
    alls_photo = set()  # Используем множество для хранения уникальных значений
    pattern = re.compile(r"data-srcset=\"(.*?)\"")
    sources = soup.find_all('source')
    for source in sources:
        match = re.search(pattern, str(source))
        if match:
            data_srcset = match.group(1)
            if data_srcset and re.search(base_url, data_srcset):
                url_photo = data_srcset.split('.png')[0] + '.png'
                alls_photo.add(url_photo)  # Добавляем значение в множество
    for photo in alls_photo:
        print(photo)


    #         print(data_srcset)
    #         data_srcset_list.append(data_srcset)
    #
    #
    #
    # # print(data_srcset_list)
    # print(base_url)
    # # pattern = re.compile(re.escape(base_url) + r".*")
    alls_photo = set()  # Используем множество для хранения уникальных значений
    # unique_urls = set()
    # for item in data_srcset_list:
    #     matches = re.findall(pattern, item)
    #     unique_urls.update(matches)
    # list_urls = list(unique_urls)


    unique_urls = list(set(list_urls))
    for s in unique_urls:
        print(s)
        if s and re.search(base_url, s):
                url_photo = s.split('.png')[0] + '.png'
                alls_photo.add(url_photo)  # Добавляем значение в множество

    for photo in alls_photo:
        print(photo)

    # print(unique_urls)



    if list_urls and re.search(base_url, list_urls):
        url_photo = list_urls.split('.png')[0] + '.png'
        alls_photo.add(url_photo)  # Добавляем значение в множество
    alls_photo = list(alls_photo)
    for photo in alls_photo:
        print(photo)


    # print(base_url)
    # print(data_srcset_list)

    """ПРОВЕРИТЬ НА ДРУГИХ ССЫЛКАХ"""





    # print(soup)



    #
    # elements = soup.find_all("li", class_=pattern)
    # # print(elements)
    # # Выводим найденные элементы
    # alls_photo = set()  # Используем множество для хранения уникальных значений
    # # # print(elements)
    # #
    # # for element in photos_01:
    # #     if isinstance(element, bs4.element.Tag):
    # #         sources = element.find_all('source')
    # #         for source in sources:
    # #             data_srcset_value = source.get('data-srcset')
    # #             if data_srcset_value and re.search(base_url, data_srcset_value):
    # #                     url_photo = data_srcset_value.split('.png')[0] + '.png'
    # #                     alls_photo.add(url_photo)  # Добавляем значение в множество
    # #
    # # # Преобразуем множество в список
    # alls_photo = list(alls_photo)
    # #
    # # # Выводим список уникальных значений
    # for photo in alls_photo:
    #     print(photo)
    #
    # filename = f"c:\\salomon_pl\\html_product\\резултат.html"
    # with open(filename, "w", encoding='utf-8') as f:
    #     f.write(html.decode('utf-8'))



    # soup = BeautifulSoup(html, 'lxml')
    # all_col = int(soup.find('div', class_='segmented-product-list_total').text.replace('Produkty: ', "").strip())
    # col_range = all_col // 10
    # urls_product = []
    # for i in range(1, col_range + 1):
    #     time.sleep(5)
    #     url = f"https://www.salomon.com/pl-pl/shop-emea/men/shoes.html?p={i}"
    #     request = scraper.get(url).content #, proxies=proxies
    #     soup = BeautifulSoup(request, 'lxml')
    #     url_product = soup.find_all('a', attrs={'ref': 'linkHead'})
    #     for u in url_product:
    #         if "https://www.salomon.com/pl-pl/shop-emea/product" in u['href']:
    #             urls_product.append(u['href'])
    #
    # with open(f"url.csv", "w", newline="", encoding='utf-8') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerows([[url] for url in urls_product])
    # print(urls_product)


    # with open("c:\\salomon_pl\\html_product\\результат.html", "w", encoding="utf-8") as file:
    #     file.write(html.decode('utf-8'))

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
