from requests_html import HTMLSession
from bs4 import BeautifulSoup

header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
}

url = 'https://linguist.ua/angliycka_mova'
s = HTMLSession()


def get_data(url):
    r = s.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    return soup


def get_next_page(soup):
    page = soup.find('ul', {'class': 'pagination'})
    next_pages = page.find_all('li')[-1].find('a')['href']
    print(next_pages)


soup = get_data(url)
print(get_next_page(soup))
