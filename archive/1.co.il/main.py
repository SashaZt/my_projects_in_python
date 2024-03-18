from bs4 import BeautifulSoup
import csv
import glob
import requests
import time

PROXY_HOST = '37.233.3.100'
PROXY_PORT = 9999
PROXY_USER = 'proxy_alex'
PROXY_PASS = 'DbrnjhbZ88'
# proxies = {
#     'http': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}',
#     'https': f'http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}'
# }
proxies = {"http": f"http://{PROXY_HOST}:{PROXY_PORT}", f"https": f"http://{PROXY_HOST}:{PROXY_PORT}"}
cookies = {
        'bnc-uuid': 'c55fa7e1-c6ad-43e7-9b01-cffae9a20990',
        'sajssdk_2015_cross_new_user': '1',
        'userPreferredCurrency': 'RUB_USD',
        'BNC_FV_KEY': '339bf87af6eaa1a78944cd47a292915fa7913bae',
        'BNC_FV_KEY_EXPIRE': '1685119051036',
        'fiat-prefer-currency': 'EUR',
        'OptanonAlertBoxClosed': '2023-05-26T10:37:42.863Z',
        'source': 'referral',
        'campaign': 'freelancehunt.com',
        'changeBasisTimeZone': '',
        'sensorsdata2015jssdkcross': '%7B%22distinct_id%22%3A%2218857a28bbb1a8e-0acd14b802cf3-26031a51-2304000-18857a28bbc1e56%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E5%BC%95%E8%8D%90%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Ffreelancehunt.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTg4NTdhMjhiYmIxYThlLTBhY2QxNGI4MDJjZjMtMjYwMzFhNTEtMjMwNDAwMC0xODg1N2EyOGJiYzFlNTYifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218857a28bbb1a8e-0acd14b802cf3-26031a51-2304000-18857a28bbc1e56%22%7D',
        'lang': 'ru-ua',
        'futures-layout': 'pro',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Fri+May+26+2023+21%3A00%3A33+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202211.1.0&isIABGlobal=false&hosts=&consentId=4e91d8ef-d242-4502-a07b-fe97597e9ff1&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1&geolocation=NL%3BNH&AwaitingReconsent=false',
    }

headers = {
        'authority': 'www.binance.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'cache-control': 'no-cache',
        # 'cookie': 'bnc-uuid=c55fa7e1-c6ad-43e7-9b01-cffae9a20990; sajssdk_2015_cross_new_user=1; userPreferredCurrency=RUB_USD; BNC_FV_KEY=339bf87af6eaa1a78944cd47a292915fa7913bae; BNC_FV_KEY_EXPIRE=1685119051036; fiat-prefer-currency=EUR; OptanonAlertBoxClosed=2023-05-26T10:37:42.863Z; source=referral; campaign=freelancehunt.com; changeBasisTimeZone=; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%2218857a28bbb1a8e-0acd14b802cf3-26031a51-2304000-18857a28bbc1e56%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E5%BC%95%E8%8D%90%E6%B5%81%E9%87%8F%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Ffreelancehunt.com%2F%22%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMTg4NTdhMjhiYmIxYThlLTBhY2QxNGI4MDJjZjMtMjYwMzFhNTEtMjMwNDAwMC0xODg1N2EyOGJiYzFlNTYifQ%3D%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%2218857a28bbb1a8e-0acd14b802cf3-26031a51-2304000-18857a28bbc1e56%22%7D; lang=ru-ua; futures-layout=pro; OptanonConsent=isGpcEnabled=0&datestamp=Fri+May+26+2023+21%3A00%3A33+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202211.1.0&isIABGlobal=false&hosts=&consentId=4e91d8ef-d242-4502-a07b-fe97597e9ff1&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0004%3A1%2CC0002%3A1&geolocation=NL%3BNH&AwaitingReconsent=false',
        'dnt': '1',
        'pragma': 'no-cache',
        'referer': 'https://freelancehunt.com/',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }
def get_requests():
    with open('C:\\scrap_tutorial-master\\1.co.il\\url.csv', newline='', encoding='utf-8') as file:
        urls = list(csv.reader(file, delimiter=' ', quotechar='|'))

        coun = 0
        for url in urls:
            time.sleep(5)
            response = requests.get(url[0], cookies=cookies, headers=headers)  # Используйте индекс 0, чтобы получить URL из списка
            src = response.text
            soup = BeautifulSoup(src, 'lxml')
            telephone_company = soup.find('li', attrs={'itemprop': 'telephone'})
            if telephone_company is not None and telephone_company.text.startswith("05"):
                with open(f"c:\\data_1.co.il\\data_{coun}.html", "w", encoding='utf-8') as file:
                    file.write(response.text)
                    coun +=1
            else:
                with open(f"C:\\scrap_tutorial-master\\1.co.il\\bad_url.csv", "a", newline="", encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(url)  # Используйте writerow для записи одной строки в CSV
                continue
            print(coun)
def parsing():
    with open('url.csv', newline='', encoding='utf-8') as file:
        urls = list(csv.reader(file, delimiter=' ', quotechar='|'))

    data = []
    folders_html = [r"c:\data_1.co.il\*.html"]
    for file in folders_html:
        files_json = glob.glob(file)
        for item in files_json:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            name_company = soup.find('h1', attrs={'class': 'entry-title'}).text
            category_company = soup.find('div', attrs={'id': 'main'}).find_all('p')[2].find('a').text
            address_company = soup.find('li', attrs={'itemprop': 'address'}).text
            telephone_company = soup.find('li', attrs={'itemprop': 'telephone'}).text
            data.append([name_company, category_company, address_company, telephone_company])
        # print(name_company, category_company, address_company, telephone_company)
    with open('data.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Category', 'Address', 'Telephone'])  # Записываем заголовки столбцов
        writer.writerows(data)  # Записываем данные

    print("Данные успешно записаны в файл data.csv.")


if __name__ == '__main__':
    get_requests()
    parsing()