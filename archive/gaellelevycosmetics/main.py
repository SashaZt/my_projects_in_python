import os
from bs4 import BeautifulSoup
import re
import requests
import csv


def get_requests():
    import requests

    cookies = {
        'data-timeout': 'false||false',
        'tk_or': '%22%22',
        'tk_r3d': '%22%22',
        'tk_lr': '%22%22',
        'wp-wpml_current_language': 'en',
    }

    headers = {
        'authority': 'gaellelevycosmetics.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'data-timeout=false||false; tk_or=%22%22; tk_r3d=%22%22; tk_lr=%22%22; wp-wpml_current_language=en',
        'dnt': '1',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    response = requests.get(
        'https://gaellelevycosmetics.com/en/shop-3/page/1/?s=dermalosophy&post_type=product&per_page=24',
        cookies=cookies,
        headers=headers, )
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    if os.path.exists('url_products.csv'):
        os.remove('url_products.csv')
    with open('url_products.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        urls = soup.find_all('h3', attrs={'class': 'wd-entities-title'})
        for i in urls:
            url = i.find('a').get("href")
            writer.writerow([url])
        next_page = soup.find('a', attrs={'class': 'next page-numbers'}).get('href')
        if next_page:
            response_next_page = requests.get(
                next_page,
                cookies=cookies,
                headers=headers, )
            src_next_page = response_next_page.text
            soup_next_page = BeautifulSoup(src_next_page, 'lxml')
            urls = soup_next_page.find_all('h3', attrs={'class': 'wd-entities-title'})
            for i in urls:
                url = i.find('a').get("href")
                writer.writerow([url])


def parsing():
    cookies = {
        'data-timeout': 'false||false',
        'tk_or': '%22%22',
        'tk_r3d': '%22%22',
        'tk_lr': '%22%22',
        'wp-wpml_current_language': 'en',
    }

    headers = {
        'authority': 'gaellelevycosmetics.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'data-timeout=false||false; tk_or=%22%22; tk_r3d=%22%22; tk_lr=%22%22; wp-wpml_current_language=en',
        'dnt': '1',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    with open('url_products.csv', newline='',
              encoding='utf-8') as files:
        csv_reader = list(csv.reader(files, delimiter=' ', quotechar='|'))
        with open(f'data_test.csv', "w", errors='ignore', encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=",", lineterminator="\r", quoting=csv.QUOTE_ALL)
            headers_csv = ('', '', '', '', '',)
            writer.writerow(headers_csv)
            for url in csv_reader:
                datas = []
                response = requests.get(url[0], cookies=cookies, headers=headers, )
                src = response.text
                soup = BeautifulSoup(src, 'lxml')

                url_img = soup.find('div', attrs={'class': 'zoom woocommerce-product-gallery__image'}).find('img').get(
                    'src')
                new_url_img = re.sub(r'(.webp).*', r'\1', url_img)

                link_tag = soup.find("link", {"rel": "alternate", "type": "application/json"})
                href = link_tag['href'] if link_tag else None

                response = requests.get(href, cookies=cookies, headers=headers, )
                json_data = response.json()
                title = json_data['title']['rendered'].replace(' &#', ' ')
                desc = json_data['excerpt']['rendered']
                soup_desc = BeautifulSoup(desc, 'lxml')
                text_only_desc = soup_desc.get_text().replace('\n', ' ').replace('\r', ' ')

                content = json_data['content']['rendered']
                soup_content = BeautifulSoup(content, 'lxml')
                text_only_content = soup_content.get_text().replace('\n', ' ').replace('\r', ' ')
                trs = soup.find_all('tr', class_='woocommerce-product-attributes-item')
                size = ''
                for tr in trs:
                    if 'Size' in tr.find('span').text.strip():
                        size = tr.find('p').text.strip()
                datas = [
                    [title, text_only_desc, text_only_content, size, new_url_img]
                ]

                writer.writerows(datas)


if __name__ == '__main__':
    get_requests()
    parsing()
