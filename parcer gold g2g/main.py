import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Chrome 
from selenium.webdriver.chrome.service import Service 
from itertools import count

urls = ["https://www.g2g.com/categories/wow-classic-gold?sort=lowest_price&page=",
        "https://www.g2g.com/categories/new-world-coins?page="]
def scrape_offers(html_source):
    soup = BeautifulSoup(html_source, 'html.parser')
    offers = soup.find_all('div', class_='col-xs-12 col-sm-6 col-md-3')
    offer_list = []
    if len(offers) == 0:
        return False
    for offer in offers:
        name = re.sub(r'[\ \n]{2,}', '', offer.find("span").text)
        price_div = offer.find("div", class_="row items-baseline q-gutter-xs text-body1")
        price = float(re.sub(r'[\ \n]{2,}', '', price_div.select_one(":nth-child(2)").text))
        offer_list.append((name, price))

    return offer_list

class Scraper:
    def __init__(self) -> None:
        options = webdriver.ChromeOptions() 
        options.headless = True
        options.page_load_strategy = 'eager'
        options.add_argument("--log-level=3")
        chrome_path = 'C:\chromedriver.exe'
        chrome_service = Service(chrome_path) 
        self.driver = Chrome(options=options, service=chrome_service) 
        self.driver.set_page_load_timeout(30)
        self.urls = None
        self.html = None
    
    def set_urls(self, urls):
        self.urls = urls
        
    def get_urls(self):
        return self.urls
   
    def load_html(self):
        self.driver.get(self.url)
        time.sleep(10)

    def get_html(self):
        return self.driver.page_source

    def scrape_pages(self):
        for url in self.urls:
            for page_number in count(1):
                self.url = url + str(page_number)
                self.load_html()
                all_offers = scrape_offers(self.get_html())
                if all_offers == False:
                    print("No more elements found, ending the loop.")
                    break
                for (name, price) in all_offers:
                    print(name, price)

scraper = Scraper()
scraper.set_urls(urls)
scraper.scrape_pages()