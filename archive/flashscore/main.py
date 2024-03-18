from bs4 import BeautifulSoup
import csv
import glob
import cloudscraper
import cloudscraper.exceptions
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
    'OptanonAlertBoxClosed': '2023-05-30T06:15:32.732Z',
    'eupubconsent-v2': 'CPskrcgPskrcgAcABBENDGCgAP7AAH7AAChQJGtf_X__b2_j-_7_f_t0eY1P9_7_v-0zjhfdl-8N2f_X_L8X52M7vF36pq4KuR4ku3LBIQVlHOHcDUmw6okVryPsbk2cr7NKJ7PEmnMbO2dYGH9_n13T-ZKY7___f__z_v-v________7-3f3__p___-2_e_V_99zfn9_____9vP___9v-_9_3gAAAAAAAAAAAAD4JGgEmGrcQBcmWOBNtGEEKIEYVhIVAKACigGEogMIGVwU7K4CfWESAFAKAJwIgQ4AoyYBAAAJAEhEAEgR4IBAABAIAAQAKhEIACNgEFgBYCAQACgOhYgRQBCBIQZEREQpAQFSJBQT2VCCUH-hphCHWWAFAo_4qEBGsgYrAiEhYOQ4IkBLxZIHmCAAAAAAAAAAAAABIA4SAEADQBeYqACAvMZABAXmOgCAA0ADMAMoBeZCAEAGYAZRKAGAGYAZQC8ykAQAGgAZgBlALzA.f9gAD9gAAAAA',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Tue+May+30+2023+12%3A37%3A01+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202210.1.0&isIABGlobal=false&hosts=&consentId=42364a9c-5775-4f2c-b962-0997d7b28c1d&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CSTACK8%3A1%2CSTACK13%3A1&geolocation=UA%3B18&AwaitingReconsent=false',
}

headers = {
    'authority': 'www.flashscore.ua',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'OptanonAlertBoxClosed=2023-05-30T06:15:32.732Z; eupubconsent-v2=CPskrcgPskrcgAcABBENDGCgAP7AAH7AAChQJGtf_X__b2_j-_7_f_t0eY1P9_7_v-0zjhfdl-8N2f_X_L8X52M7vF36pq4KuR4ku3LBIQVlHOHcDUmw6okVryPsbk2cr7NKJ7PEmnMbO2dYGH9_n13T-ZKY7___f__z_v-v________7-3f3__p___-2_e_V_99zfn9_____9vP___9v-_9_3gAAAAAAAAAAAAD4JGgEmGrcQBcmWOBNtGEEKIEYVhIVAKACigGEogMIGVwU7K4CfWESAFAKAJwIgQ4AoyYBAAAJAEhEAEgR4IBAABAIAAQAKhEIACNgEFgBYCAQACgOhYgRQBCBIQZEREQpAQFSJBQT2VCCUH-hphCHWWAFAo_4qEBGsgYrAiEhYOQ4IkBLxZIHmCAAAAAAAAAAAAABIA4SAEADQBeYqACAvMZABAXmOgCAA0ADMAMoBeZCAEAGYAZRKAGAGYAZQC8ykAQAGgAZgBlALzA.f9gAD9gAAAAA; OptanonConsent=isGpcEnabled=0&datestamp=Tue+May+30+2023+12%3A37%3A01+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202210.1.0&isIABGlobal=false&hosts=&consentId=42364a9c-5775-4f2c-b962-0997d7b28c1d&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1%2CSTACK8%3A1%2CSTACK13%3A1&geolocation=UA%3B18&AwaitingReconsent=false',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://freelancehunt.com/',
    'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'cross-site',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
}
scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    })
# def get_requests():
#     craper_get = scraper.get('https://www.flashscore.ua/team/victoriano-arenas/jeLHXPej/results/', cookies=cookies, headers=headers).content
#     # response = requests.get('https://www.flashscore.ua/team/victoriano-arenas/jeLHXPej/results/', cookies=cookies, headers=headers)  # Используйте индекс 0, чтобы получить URL из списка
#     filename = f"C:\\scrap_tutorial-master\\flashscore\\data_.html"
#     with open(filename, "w", encoding='utf-8') as f:
#         f.write(craper_get.decode('utf-8'))
# # src = response.text
# #     soup = BeautifulSoup(src, 'lxml')
# #     with open(f"C:\\scrap_tutorial-master\\flashscore\\data_.html", "w", encoding='utf-8') as file:
# #         file.write(response.text)
#
# def parsing():
#     with open('url.csv', newline='', encoding='utf-8') as file:
#         urls = list(csv.reader(file, delimiter=' ', quotechar='|'))
#
#     data = []
#     folders_html = [r"c:\data_1.co.il\*.html"]
#     for file in folders_html:
#         files_json = glob.glob(file)
#         for item in files_json:
#             with open(item, encoding="utf-8") as file:
#                 src = file.read()
#             soup = BeautifulSoup(src, 'lxml')
#             name_company = soup.find('h1', attrs={'class': 'entry-title'}).text
#             category_company = soup.find('div', attrs={'id': 'main'}).find_all('p')[2].find('a').text
#             address_company = soup.find('li', attrs={'itemprop': 'address'}).text
#             telephone_company = soup.find('li', attrs={'itemprop': 'telephone'}).text
#             data.append([name_company, category_company, address_company, telephone_company])
#         # print(name_company, category_company, address_company, telephone_company)
#     with open('data.csv', 'w', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         writer.writerow(['Name', 'Category', 'Address', 'Telephone'])  # Записываем заголовки столбцов
#         writer.writerows(data)  # Записываем данные
#
#     print("Данные успешно записаны в файл data.csv.")
#
#
# if __name__ == '__main__':
#     get_requests()
#     # parsing()






import time
import re
import undetected_chromedriver
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
import csv


def get_undetected_chromedriver():
    # Обход защиты
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--proxy-server=45.14.174.253:80")
    # chrome_options.add_argument('--ignore-certificate-errors')
    # chrome_options.add_argument('--ignore-ssl-errors')
    # chrome_options.add_argument('--disable-extensions')
    # chrome_options.add_argument('--disable-dev-shm-usage')
    # chrome_options.add_argument('--no-sandbox')
    # chrome_options.add_argument('--disable-setuid-sandbox')
    # driver = webdriver.Chrome(options=chrome_options)
    driver = undetected_chromedriver.Chrome(options=chrome_options)

    return driver


def process_url():
    url = 'https://www.flashscore.ua/team/victoriano-arenas/jeLHXPej/results/'
    driver = get_undetected_chromedriver()
    driver.maximize_window()
    driver.get(url)
    time.sleep(5)
    try:
        button_cookies = driver.find_element(By.XPATH, '//button[@id="onetrust-accept-btn-handler"]').click()
    except:
        return
    more_ = False
    while not more_:
        try:
            driver.find_element(By.XPATH, '//a[@class="event__more event__more--static"]').click()
            driver.execute_script("window.scrollBy(0,document.body.scrollHeight)")
            time.sleep(1)
        except:
            break
    time.sleep(5)
    with open(f"C:\\scrap_tutorial-master\\flashscore\\data_.html", "w", encoding='utf-8') as file:
        file.write(driver.page_source)

def parsing():
    with open('data.csv', "w", errors='ignore', encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";", lineterminator="\r")
        writer.writerow(("Дата", 'Команда "А"', 'Команда "Б"', 'Счет "А"', 'Счет "Б"'))
        with open('C:\\scrap_tutorial-master\\flashscore\\data_.html', encoding="utf-8") as file:
            src = file.read()
        soup = BeautifulSoup(src, 'lxml')
        results = soup.find_all('div', attrs={'class': 'event__match event__match--static event__match--twoLine'})
        for i in results:
            datas = []
            # print(i)
            re_home_comand = re.compile('event__participant event__participant--home.*')
            re_guests_comand = re.compile('event__participant event__participant--away.*')
            home_comand = i.find('div', attrs={'class': re_home_comand}).text
            guests_comand = i.find('div', attrs={'class': re_guests_comand}).text
            home_score = i.find('div', attrs={'class': 'event__score event__score--home'}).text
            guests_score = i.find('div', attrs={'class': 'event__score event__score--away'}).text
            data_games = i.find('div', attrs={'class': 'event__time'}).text
            datas.append([data_games, home_comand, guests_comand, home_score, guests_score])
            writer.writerows(datas)
            # print( data_games, home_comand, guests_comand, home_score, guests_score)


if __name__ == '__main__':
    # process_url()
    parsing()