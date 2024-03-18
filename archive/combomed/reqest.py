import cloudscraper
import csv
import os

def process_url(url):
    scraper = cloudscraper.create_scraper(browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    })
    try:
        name_file = url.split('/')[-1]
        file_name = f"{name_file}.html"
        if os.path.exists(os.path.join('data', file_name)):
            return
        html = scraper.get(url).content
        with open(os.path.join('data', file_name), "wb") as fl:
            fl.write(html)
    except:
        pass

def save_html():
    with open('url.csv', newline='', encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        urls = [url[0] for url in csv_reader]
        for url in urls:
            process_url(url)
            time.sleep(1)  # добавляем задержку в 1 секунду

if __name__ == '__main__':
    save_html()
