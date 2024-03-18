import random
import requests
from bs4 import BeautifulSoup
import asyncio
import csv
import re
import os
from proxi import proxies
from requests.exceptions import RequestException

current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
html_path = os.path.join(temp_path, "html")
category_path = os.path.join(temp_path, "category")


def get_random_proxy():
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    return {
        'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
    }

def get_with_proxies(url, headers):
    try:
        proxies = get_random_proxy()
        response = requests.get(url, headers=headers, proxies=proxies)
        return response
    except RequestException:
        print(f"Проблема с прокси {proxies}. Пропускаем.")
        return None  # или возвращайте какое-либо значение по умолчанию

async def fetch_url(url, header):
    response = await asyncio.get_event_loop().run_in_executor(None, get_with_proxies, url, header)
    url_home = 'https://shop.olekmotocykle.com/'
    if response is not None:
        soup = BeautifulSoup(response.text, 'lxml')
        # Создаём пустой список для сохранения ссылок
        img_links = []

        # Используем find_all для поиска всех тегов <img> на странице,
        # у которых есть атрибут 'alt', содержащий '9'.
        # Функция lambda x: x and '9' in x гарантирует, что 'alt' не только существует, но и содержит '9'.
        regex_cart = re.compile('product-item.*')



        product_blocks = soup.find_all('div', class_=regex_cart)
        for block in product_blocks:
            # Ищем все изображения в блоке
            a = block.find('a', class_="product-link-ui")
            if a and a.has_attr('href'):
                img_links.append(f'{url_home}' + a['href'])  # Добавляем найденный href в список
        # # for img in soup.find_all('img', alt=lambda x: x and '9' in x):

        #     # Для каждого найденного тега <img> ищем ближайший предшествующий тег <a>.
        #     # Метод find_previous('a') возвращает ближайший выше по коду тег <a>.
        #     a = img.find_previous('a')
            
            
        #     # Проверяем, что тег <a> найден (a не является None) и у него есть атрибут 'href'.
        #     if a and 'href' in a.attrs:
        #         # Добавляем в список img_links полную ссылку, состоящую из какой-то базовой части 'url'
        #         # (предполагается, что это какой-то базовый URL, к которому нужно добавить относительную ссылку из 'href'),
        #         # и сами значения 'href' из тега <a>.
        #         img_links.append(f'{url_home}' + a['href'])

        # Возвращаем список ссылок
        return img_links
    else:
        return []

async def process_category(url, header, writer, unique_links):
    response = await asyncio.get_event_loop().run_in_executor(None, get_with_proxies, url, header)
    soup = BeautifulSoup(response.text, 'lxml')
    #Получаем пагинацию 
    span_tag = soup.find('span', {'class': 'page-amount-ui'})
    data_max_int = int(span_tag.text.split()[1]) if span_tag is not None else 1
    group = url.split('produkty/')[1].split(',')[0]
    tasks = []
    for i in range(1, data_max_int + 1):
        if i == 1:
            img_links = await fetch_url(url, header)
            for img_link in img_links:
                if img_link not in unique_links:
                    writer.writerow([img_link])
                    unique_links.add(img_link)
        else:
            tasks.append(fetch_url(f'{url}?pageId={i}', header))
    if tasks:
        img_links_list = await asyncio.gather(*tasks)
        for img_links in img_links_list:
            for img_link in img_links:
                if img_link not in unique_links:
                    writer.writerow([img_link])
                    unique_links.add(img_link)

async def main():
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
    filename_category = os.path.join(category_path, "category_product.csv")
    filename_url = os.path.join(category_path, "url.csv")
    with open(filename_category, newline='', encoding='utf-8') as files, open(filename_url, 'a', newline='', encoding='utf-8') as f:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        writer = csv.writer(f)
        tasks = []
        unique_links = set()
        for row in urls:
            
            url = row[0]
            tasks.append(process_category(url, header, writer, unique_links))

        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
