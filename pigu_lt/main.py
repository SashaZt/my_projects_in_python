from bs4 import BeautifulSoup
from pathlib import Path
import json
import re

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)


def parse_html():
    extracted_data = []

    # Пройтись по каждому HTML файлу в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

        # Парсим HTML с помощью BeautifulSoup
        soup = BeautifulSoup(content, "lxml")
        price, currency = get_price(soup)
        if price is not None:
            price = float(price)  # Преобразуем в float
            if price.is_integer():  # Проверяем, является ли число целым
                price = int(price)
        rating, reviews_count = get_reviews_and_ratings(soup)
        if rating is not None:
            rating = float(rating)  # Преобразуем в float
            if rating.is_integer():  # Проверяем, является ли число целым
                rating = int(rating)
        if reviews_count is not None:
            reviews_count = float(reviews_count)  # Преобразуем в float
            if reviews_count.is_integer():  # Проверяем, является ли число целым
                reviews_count = int(reviews_count)
        all_data = {
            "success": True,
            "url":get_url(soup),
            "id":get_product_id(soup),
            "category_path":get_breadcrumbs(soup),
            "price": price,
            "currency": currency,
            "brand": get_brand(soup),
            "title":get_product_name(soup),
            "rating": rating, 
            "reviews_count": reviews_count,
            "Photos":get_all_photos(soup),
            "Description":get_description(soup),
            "specifications":get_specifications(soup),
            "reviews":get_reviews(soup),
            "offers":get_seller_offers(soup),
            "delivery_options":get_delivery_options(soup)
            

        }
        extracted_data.append(all_data)
    with open("extracted_data.json", "w", encoding="utf-8") as json_file:
        json.dump(extracted_data, json_file, indent=4, ensure_ascii=False)
def get_url(soup):
    """
    Извлекает URL из элемента <meta property="og:url"> на странице.
    """
    meta_tag = soup.find("meta", property="og:url")
    return meta_tag["content"] if meta_tag and "content" in meta_tag.attrs else None
def get_product_id(soup):
    """
    Извлекает Prekės ID из таблицы на странице.
    """
    # Находим строку таблицы, где указано "Prekės ID:"
    row = soup.find("tr", text=lambda t: t and "Prekės ID:" in t)
    if row:
        # Ищем значение в соседней ячейке <td>
        value_cell = row.find_next("td")
        if value_cell:
            return int(value_cell.text.strip())  # Преобразуем в число
    return None


def get_breadcrumbs(soup):
    category_path = []
    breadcrumb_elements = soup.select('ul#breadCrumbs li')
    for elem in breadcrumb_elements:
        name = elem.select_one('span[itemprop="name"]').text.strip()
        link = elem.select_one('a[itemprop="item"]')['href']
        category_path.append({'name': name, 'link': link})
    return category_path

def get_price(soup):
    currency_map = {
        '€': 'EUR',
        'PLN': 'PLN',
        '$': 'USD',
        # Добавляйте другие валюты по мере необходимости
    }
    price_container = soup.select_one('.c-price.h-price--xx-large, .c-price.h-price--xx-large.h-price--new, .c-price.h-price--xx-large.h-price')
    price = None
    currency = None
    if price_container:
        # Извлекаем основную часть цены
        main_price = ''.join(price_container.find(string=True, recursive=False).split())
        # Извлекаем дробную часть
        fractional_price = price_container.select_one('sup').text.strip() if price_container.select_one('sup') else '00'
        # Извлекаем валюту
        currency = price_container.select_one('small').text.strip() if price_container.select_one('small') else ''
        # Форматируем цену
        price = f"{main_price}.{fractional_price}"
        currency = currency_map.get(currency)  # Если нет в словаре, оставить оригинал
        return price, currency
    return None

def get_brand(soup):
    brand_element = soup.select_one('.c-product__brand')
    if brand_element:
        brand_name = brand_element.text.strip()
        brand_link = brand_element['href']
        return brand_name
        # return {'name': brand_name, 'link': brand_link}
    return None

def get_product_name(soup):
    product_name = soup.select_one('h1.c-product__name')
    return product_name.text.strip() if product_name else None

def get_reviews_and_ratings(soup):
    reviews_section = soup.select_one('.c-product__reviews')
    if reviews_section:
        # Извлекаем рейтинг
        rating = reviews_section.select_one('.c-rating span').text.strip()
        # Извлекаем количество отзывов, убирая скобки
        reviews_count = reviews_section.select_one('a[href*="#reviews"] span').text.strip().replace('(', '').replace(')', '')
        return rating, reviews_count
    return None

def get_all_photos(soup):
    photos = []
    photo_elements = soup.select('.c-product-gallery__view-inner img')
    for photo in photo_elements:
        original_url = photo['src']
        thumbnail_url = original_url.replace('reference', 'small')
        alt_text = photo.get('alt', '')
        photos.append({
            "original": original_url,
            "thumbnail": thumbnail_url,
            "alt": alt_text
        })
    return photos

def get_description(soup):
    description_element = soup.select_one('#product-description .c-product__description-container')
    # Извлекаем текстовые теги внутри найденного div
    tags = description_element.find_all(["h1", "h2", "p", "b", "ul", "li", "img"])
    if description_element:
        # Преобразуем все теги в строки и объединяем их через join
        return "".join(str(tag) for tag in tags)
    return None
def get_specifications(soup):
    specifications = {}
    # Находим таблицу со спецификациями
    table_rows = soup.select('div[widget-attachpoint="collapsible"] table tbody tr')
    for row in table_rows:
        # Извлекаем заголовок и значение
        key_cell = row.select_one('td:nth-child(1)')
        value_cell = row.select_one('td:nth-child(2)')
        
        if key_cell and value_cell:
            key = key_cell.text.strip().replace(':', '')  # Убираем двоеточие
            value_links = value_cell.select('a')
            
            # Если в значении есть ссылки, собираем их текст
            if value_links:
                value = ', '.join(link.text.strip() for link in value_links)
            else:
                value = value_cell.text.strip()
            
            specifications[key] = value
    
    return {"Parametry": specifications}
def get_reviews(soup):
    reviews = []
    # Ищем все элементы с классом c-review
    review_elements = soup.select('.c-review')
    for review in review_elements:
        # Извлекаем текст отзыва
        text = review.select_one('.c-review__content p').text.strip() if review.select_one('.c-review__content p') else ''
        # Считаем количество активных звезд для определения рейтинга
        score = len(review.select('.c-rating.s-is-active .c-icon--star-full.s-is-active'))
        # Извлекаем дату отзыва
        date = review.select_one('.c-review__date').text.strip() if review.select_one('.c-review__date') else ''
        # Добавляем данные отзыва в список
        reviews.append({
            "text": text,
            "score": score,
            "date": date
        })
    return {"reviews": reviews}
def get_seller_offers(soup):
    offers = []
    # Ищем все блоки с информацией о продавцах
    seller_elements = soup.select('.c-seller-offer')
    for seller in seller_elements:
        # Название продавца
        seller_name = seller.select_one('.c-seller-offer__seller a')
        seller_name = seller_name.text.strip() if seller_name else 'Не указан'

        # Рейтинг продавца
        rating = seller.select_one('.c-seller-offer__seller-rating')
        rating = float(rating.text.strip()) if rating else None

        # Количество отзывов
        reviews_text = seller.select_one('.c-seller-offer__reviews')
        reviews_count = int(re.search(r'\d+', reviews_text.text).group()) if reviews_text else 0

        # Цена
        price_element = seller.select_one('.c-price.h-price--large')
        if price_element:
            euros = price_element.contents[0].strip()  # Основная часть цены (евро)
            cents = price_element.select_one('sup').text.strip() if price_element.select_one('sup') else '00'
            price = float(f"{euros}.{cents}")
        else:
            price = None

        # Валюта
        currency = price_element.select_one('small').text.strip() if price_element and price_element.select_one('small') else '€'

        # Добавляем собранные данные
        offers.append({
            "seller": seller_name,
            "rating": rating,
            "reviews_count": reviews_count,
            "price": price,
            # "currency": currency,
        })
    return offers

def get_delivery_options(soup):
    """
    Извлекает информацию о вариантах доставки из HTML.
    """
    delivery_options = []
    
    # Находим все блоки с классом c-delivery-types__type
    delivery_elements = soup.select(".c-delivery-types__type")
    for element in delivery_elements:
        # Локация доставки
        location_element = element.select_one(".c-delivery-types__date p")
        location = location_element.text.strip() if location_element else "Не указано"

        # Дата доставки
        date_element = location_element.find_next("p") if location_element else None
        delivery_date = date_element.text.strip() if date_element else "Не указана"

        # Цена доставки
        price_element = element.select_one(".c-price.h-price--small")
        if price_element:
            euros = price_element.contents[0].strip()
            cents = price_element.select_one("sup").text.strip() if price_element.select_one("sup") else "00"
            price = float(f"{euros}.{cents}")
        else:
            price = None

        # Добавляем данные в список
        delivery_options.append({
            "location": location,
            "delivery_date": delivery_date,
            "price": price,
        })
    
    return delivery_options


if __name__ == '__main__':
    parse_html()
