import time
import  csv
import requests
from bs4 import BeautifulSoup
import json
header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"}
def main():
    # # Загрузка HTML-кода страницы
    # url = 'https://www.ctrs.com.ua/'
    # response = requests.get(url, headers=header)
    # soup = BeautifulSoup(response.text, 'lxml')
    # script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
    # json_data = json.loads(script_tag.contents[0])
    # category_urls = []
    # category = json_data['props']['pageProps']['layout']['categories']
    # for i in category:
    #     url = 'https://www.ctrs.com.ua' + i['url']
    #     category_urls.append(url)
    # with open(f'category_urls.csv', 'w', newline='', encoding='utf-8') as csvfile:
    #     writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
    #     writer.writerow(category_urls)
    # print("Все категории собраны")
    with open(f'category_urls.csv', newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        categoriesTree_url = []
        for url in urls:
            print(url[0])
            response = requests.get(url[0], headers=header)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
            else:
                print(f"Ошибка по ссылке {url[0]}")
                continue
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            json_data = json.loads(script_tag.contents[0])
            # try:
            if 'categoriesTree' in json_data['props']['pageProps']['data']:
                categoriesTree = json_data['props']['pageProps']['data']['categoriesTree']
                for ct in categoriesTree[1:]:
                    url_ct = ct['items']
                    for i in url_ct:
                        categoriesTree_url.append(i['url'])
            elif 'categories' in json_data['props']['pageProps']:
                categoriesTree = json_data['props']['pageProps']['categories']
                for ct in categoriesTree:
                    url_ct = ct['items']
                    for i in url_ct:
                        categoriesTree_url.append(i['url'])
            elif 'products' in json_data['props']['pageProps']['data']:
                product_list = []
                reviews_list = []
                for i in json_data['props']['pageProps']['data']['products']:

                    product_dict = {
                        "reviews": reviews_list
                    }
                    all_reviews = []
                    if i['reviews']['rating'] > 0:
                        url_product = 'https://www.ctrs.com.ua'+ i['url']
                        response = requests.get(url_product, headers=header)
                        soup = BeautifulSoup(response.text, 'lxml')
                        script_tag = soup.find_all('script', {'type': 'application/ld+json'})
                        json_data = json.loads(script_tag[2].text)
                        name_product = json_data['name'].replace("/", "_")
                        all_reviews = json_data['review']

                        for r in all_reviews:
                            raiting = r['reviewRating']['ratingValue']
                            author = r['author']['name']
                            descript = r['reviewBody'].replace("\n", "")
                            all_reviews.append({
                                "rating": raiting,
                                "author": author,
                                "description": descript
                            })
                            # Создаем словарь с ключом "reviews"
                        result = {
                            "reviews": all_reviews
                        }

                        print(result)

                        # Добавляем словарь в список

                        #
                        # # product_dict = {"reviews": reviews_list}
                        # # product_dict = {"name": name_product, "reviews": reviews_list}
                        # # reviews_dict = {"reviews": reviews_list}
                        # # product_dict = {"name": name_product, **reviews_dict}
                        # # Добавление словаря в список продуктов
                        # # product_list.append(product_dict)
                        # # Сохранение списка продуктов в JSON-файл
                        # with open(f'json/{name_product}.json', 'w', encoding='utf-8') as f:
                        #     json.dump(product_list, f, ensure_ascii=False, indent=4)
                        # print(name_product)
                        # # with open(f"test.json", "w", encoding='utf-8') as f:
                        # #     json.dump(json_data, f, indent=4, ensure_ascii=False)
                else:
                    print(url[0])
            # except:
            #     print(url[0])


    #     with open(f'categoriesTree_url.csv', 'w', newline='', encoding='utf-8') as csvfile:
    #         writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
    #         writer.writerow(categoriesTree_url)
    # product_list = []

    # with open(f'categoriesTree_url.csv', newline='', encoding='utf-8') as files:
    #     urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
    #     products = []
    #     for url in urls:
    #         time.sleep(1)
    #         print(url[0])
    #         response = requests.get(url[0], headers=header)
    #         json_data = response.json()
    #         items = json_data['data']['facetObject']['items']
    #         for i in items:
    #             if i['reviews']['rating']:
    #                 products.append('https://www.ctrs.com.ua' + i['url'])
    #     with open(f'products.csv', 'w', newline='', encoding='utf-8') as csvfile:
    #         writer = csv.writer(csvfile, delimiter='\n', quotechar='|')
    #         writer.writerow(products)
    # with open(f'products.csv', newline='', encoding='utf-8') as files:
    #     urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
    #     for url in urls:
    #         time.sleep(1)
    #         response = requests.get(url[0], headers=header)
    #         soup = BeautifulSoup(response.text, 'lxml')
    #         script_tag = soup.find_all('script', {'type': 'application/ld+json'})
    #         json_data = json.loads(script_tag[2].text)
    #         name_product = json_data['name']
    #         all_reviews = json_data['review']
    #         reviews_list = []
    #         for r in all_reviews:
    #             raiting = r['reviewRating']['ratingValue']
    #             author = r['author']['name']
    #             descript = r['reviewBody'].replace("\n", "")
    #             review_dict = {"raiting": raiting, "author": author, "descript": descript}
    #             reviews_list.append(review_dict)
    #
    #         product_dict = {"reviews": reviews_list}
    #         # product_dict = {"name": name_product, "reviews": reviews_list}
    #         # reviews_dict = {"reviews": reviews_list}
    #         # product_dict = {"name": name_product, **reviews_dict}
    #         # Добавление словаря в список продуктов
    #         product_list.append(product_dict)
    #         # Сохранение списка продуктов в JSON-файл
    #         with open(f'json/{name_product}.json', 'w', encoding='utf-8') as f:
    #             json.dump(product_list, f, ensure_ascii=False, indent=4)
    #         print(name_product)
    #         # with open(f"test.json", "w", encoding='utf-8') as f:
    #         #     json.dump(json_data, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()
