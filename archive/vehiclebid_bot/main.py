import json

import cloudscraper
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Нажатие клавиш

# Для работы webdriver____________________________________________________
# Для работы с драйвером селениум по Хром необходимо эти две строчки

useragent = UserAgent()


def save_link_all_product(url):
    header = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent": f"{useragent.random}"
    }
    # Обход защиты cloudflare
    session = requests.Session()
    session.proxies = {
        'http': 'http://80.77.34.218:9999',
        'https': 'http://80.77.34.218:9999',
    }
    scraper = cloudscraper.create_scraper(sess=session, delay=10, browser="chrome")
    content = scraper.get(url, headers=header)
    # Обход защиты cloudflare
    soup = BeautifulSoup(content.text, 'lxml')

    car_dict = []

    # Получаем таблицу всех товаров
    table = soup.find('div', attrs={'class': 'chakra-stack css-owjkmg'}).find_all('a')
    # Получаем список всех url на карточки
    for item in table:
        url_cart = item.find('img').get('src')
        name_cart = item.find('div', attrs={'class': 'chakra-card__body css-1idwstw'}).find('h2', attrs={
            'class': 'chakra-heading css-18j379d'}).text
        all_tag_p_cart = item.find('div', attrs={'class': 'chakra-card__body css-1idwstw'}).find_all('p', attrs={
            'class': 'chakra-text css-0'})
        try:
            vin_cart = all_tag_p_cart[0].text
        except:
            vin_cart = "Not win_code"
        try:
            lot_cart = item.find('div', attrs={'class': 'chakra-card__body css-1idwstw'}).find('p', attrs={
                'class': 'chakra-text css-wt5l11'}).text
        except:
            lot_cart = "Not lot"
        try:
            speed_cart = all_tag_p_cart[1].text
        except:
            speed_cart = "Not lot"
        try:
            data_cart = all_tag_p_cart[2].text
        except:
            data_cart = "Not date"
        try:
            price_cart = item.find('div', attrs={'class': 'chakra-card__body css-1idwstw'}).find('span', attrs={
                'class': 'chakra-badge css-osfzth'}).text
        except:
            price_cart = "Not price"

        car_dict.append({
            'url_cart': url_cart,
            'name_cart': name_cart,
            'vin_cart': vin_cart,
            'lot_cart': lot_cart,
            'data_cart': data_cart,
            'speed_cart': speed_cart,
            'price_cart': price_cart

        })
    with open("card.json", 'w') as file:
        json.dump(car_dict, file, indent=4, ensure_ascii=False)


def parsing_product():
    pass


if __name__ == '__main__':
    # print("Вставьте ссылку")
    # url = input()
    save_link_all_product('https://vehiclebid.info/ru/search?page=4002')
