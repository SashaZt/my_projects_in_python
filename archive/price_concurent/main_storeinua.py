import requests
from bs4 import BeautifulSoup
header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}
def main():
    # url = 'https://storeinua.com/ua/apple-all-uk/iphone/iphone-14-pro-max/apple-iphone-14-pro-max-1tb-space-black-dual-esim-mq923-ua.html'
    # response = requests.get(url)
    #
    # with open('example.html', 'w', encoding='utf-8') as f:
    #     f.write(response.text)
    with open('example.html', 'r', encoding='utf-8') as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')
    price_tag = soup.find('div', {'class': 'h2 m-0 text-nowrap product-price-new'})
    price = price_tag.text.strip().replace('\xa0', '').replace("₴", "")
    print(price)

if __name__ == '__main__':
    main()
