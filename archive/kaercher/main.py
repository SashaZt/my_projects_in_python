from bs4 import BeautifulSoup
import csv
import os
import glob
import json
import requests
import random
import time
from proxi import proxies

cookies = {
    'at_check': 'true',
    'KRECOSESS': '169078961029312166//2715a0bbce853670723d40b0e3144037',
    'KSESS_10': '0735c94d-dc22-4acc-bc12-85e5c43f4bb0',
    '_gcl_au': '1.1.213151273.1690789610',
    '__adal_ses': '*',
    '__adal_ca': 'so%3Ddirect%26me%3Dnone%26ca%3Ddirect%26co%3D%28not%2520set%29%26ke%3D%28not%2520set%29',
    '__adal_cw': '1690789610386',
    '_fbp': 'fb.1.1690789610431.1527424073',
    'sa-user-id': 's%253A0-9154e4d5-7bc8-51fc-6fdb-b683047bd37c.z%252FNmLRonInc7WkdhO78U3vflc%252FxS6wwlZfTh8qaPXo4',
    'sa-user-id-v2': 's%253AkVTk1XvIUfxv27aDBHvTfJJ4uQQ.sZ3NpI%252FU7L4tB5e5HzVZdVcCz1CeDWFkyzuGw23WIxw',
    'sa-user-id-v3': 's%253AAQAKIMdwE-MaP1reSnCrbY_1JD_GIh-5CdqHferSNzqCRnE3EAEYAyDqzZ2mBjABOgStDEWrQgS-dctg.%252BdOoEA6uR0gKO9vF6q0cQ4scvsnWiYKh%252BZ6uOXSmFOY',
    '_gid': 'GA1.2.2015236943.1690789610',
    '_gat_gtag_UA_134334172_1': '1',
    'ln_or': 'eyIyNjQ5MTM3IjoiZCJ9',
    's_ecid': 'MCMID%7C86833230213200813150366199748371698242',
    'AMCVS_29510C0F53DB0E6F0A490D45%40AdobeOrg': '1',
    '__syn_authorization': 'Bearer 655ACCFC-CD87-5563-6501-DCBB1C9CBAAC',
    '__syn_app_key': '713422b48c063d06a4888251a5147991',
    'BVBRANDID': '3ed4c352-4e8c-44fb-adef-c95697f8b155',
    'BVBRANDSID': 'e9d25f58-1dfb-4b36-ac63-8beb90ced443',
    'AMCV_29510C0F53DB0E6F0A490D45%40AdobeOrg': '179643557%7CMCIDTS%7C19570%7CMCMID%7C86833230213200813150366199748371698242%7CMCAID%7CNONE%7CMCOPTOUT-1690796810s%7CNONE%7CMCAAMLH-1691394410%7C6%7CMCAAMB-1691394410%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCSYNCSOP%7C411-19577%7CvVersion%7C5.5.0',
    's_vnum': '1722325611180%26vn%3D1',
    's_invisit': 'true',
    'gdslv_s': 'First%20Visit',
    's_heroteaser': 'None',
    'gpv_pmkls': 'Guest',
    's_cc': 'true',
    'BVImplengland': '15770_15_0',
    '__adal_id': '8657a2cf-95d8-4d4c-8c73-e525f6684d53.1690789610.1.1690789612.1690789610.5d5f5850-ea66-4950-9687-56905d201997',
    '_uetsid': '6898df202f7611eeb85ec107fad36a7f',
    '_uetvid': '6898f8802f7611eebae2636e28001451',
    'mbox': 'session#1ca0c56a86e74ea8a244c702058af829#1690791473|PC#1ca0c56a86e74ea8a244c702058af829.37_0#1754034413',
    '_ga_MVHY9P0ZBN': 'GS1.1.1690789610.1.1.1690789612.58.0.0',
    '_ga': 'GA1.1.1421999186.1690789610',
    'paypal-offers--view-count-credit': '2',
    'gpv_ppid': '41709',
    'gpv_ppname': 'GB%3A10%7C%7C41709%3AUK%20-%20United%20Kingdom%20%28Live%29',
    'gdslv': '1690789612720',
    's_ppvl': 'GB%253A10%257C%257C84170%253AGlass%2520Cleaning%2520Concentrate%2520500ml%252062957950%2C13%2C13%2C1051%2C1920%2C1051%2C1920%2C1200%2C1%2CP',
    's_getNewRepeat': '1690789612721-New',
    'gpv_pfm': 'None',
    's_sq': '%5B%5BB%5D%5D',
    's_ppv': 'GB%253A10%257C%257C41709%253AUK%2520-%2520United%2520Kingdom%2520%2528Live%2529%2C37%2C34%2C1051%2C1266%2C1051%2C1920%2C1200%2C1%2CP',
}

headers = {
    'authority': 'www.kaercher.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru',
    'cache-control': 'no-cache',
    # 'cookie': 'at_check=true; KRECOSESS=169078961029312166//2715a0bbce853670723d40b0e3144037; KSESS_10=0735c94d-dc22-4acc-bc12-85e5c43f4bb0; _gcl_au=1.1.213151273.1690789610; __adal_ses=*; __adal_ca=so%3Ddirect%26me%3Dnone%26ca%3Ddirect%26co%3D%28not%2520set%29%26ke%3D%28not%2520set%29; __adal_cw=1690789610386; _fbp=fb.1.1690789610431.1527424073; sa-user-id=s%253A0-9154e4d5-7bc8-51fc-6fdb-b683047bd37c.z%252FNmLRonInc7WkdhO78U3vflc%252FxS6wwlZfTh8qaPXo4; sa-user-id-v2=s%253AkVTk1XvIUfxv27aDBHvTfJJ4uQQ.sZ3NpI%252FU7L4tB5e5HzVZdVcCz1CeDWFkyzuGw23WIxw; sa-user-id-v3=s%253AAQAKIMdwE-MaP1reSnCrbY_1JD_GIh-5CdqHferSNzqCRnE3EAEYAyDqzZ2mBjABOgStDEWrQgS-dctg.%252BdOoEA6uR0gKO9vF6q0cQ4scvsnWiYKh%252BZ6uOXSmFOY; _gid=GA1.2.2015236943.1690789610; _gat_gtag_UA_134334172_1=1; ln_or=eyIyNjQ5MTM3IjoiZCJ9; s_ecid=MCMID%7C86833230213200813150366199748371698242; AMCVS_29510C0F53DB0E6F0A490D45%40AdobeOrg=1; __syn_authorization=Bearer 655ACCFC-CD87-5563-6501-DCBB1C9CBAAC; __syn_app_key=713422b48c063d06a4888251a5147991; BVBRANDID=3ed4c352-4e8c-44fb-adef-c95697f8b155; BVBRANDSID=e9d25f58-1dfb-4b36-ac63-8beb90ced443; AMCV_29510C0F53DB0E6F0A490D45%40AdobeOrg=179643557%7CMCIDTS%7C19570%7CMCMID%7C86833230213200813150366199748371698242%7CMCAID%7CNONE%7CMCOPTOUT-1690796810s%7CNONE%7CMCAAMLH-1691394410%7C6%7CMCAAMB-1691394410%7Cj8Odv6LonN4r3an7LhD3WZrU1bUpAkFkkiY1ncBR96t2PTI%7CMCSYNCSOP%7C411-19577%7CvVersion%7C5.5.0; s_vnum=1722325611180%26vn%3D1; s_invisit=true; gdslv_s=First%20Visit; s_heroteaser=None; gpv_pmkls=Guest; s_cc=true; BVImplengland=15770_15_0; __adal_id=8657a2cf-95d8-4d4c-8c73-e525f6684d53.1690789610.1.1690789612.1690789610.5d5f5850-ea66-4950-9687-56905d201997; _uetsid=6898df202f7611eeb85ec107fad36a7f; _uetvid=6898f8802f7611eebae2636e28001451; mbox=session#1ca0c56a86e74ea8a244c702058af829#1690791473|PC#1ca0c56a86e74ea8a244c702058af829.37_0#1754034413; _ga_MVHY9P0ZBN=GS1.1.1690789610.1.1.1690789612.58.0.0; _ga=GA1.1.1421999186.1690789610; paypal-offers--view-count-credit=2; gpv_ppid=41709; gpv_ppname=GB%3A10%7C%7C41709%3AUK%20-%20United%20Kingdom%20%28Live%29; gdslv=1690789612720; s_ppvl=GB%253A10%257C%257C84170%253AGlass%2520Cleaning%2520Concentrate%2520500ml%252062957950%2C13%2C13%2C1051%2C1920%2C1051%2C1920%2C1200%2C1%2CP; s_getNewRepeat=1690789612721-New; gpv_pfm=None; s_sq=%5B%5BB%5D%5D; s_ppv=GB%253A10%257C%257C41709%253AUK%2520-%2520United%2520Kingdom%2520%2528Live%2529%2C37%2C34%2C1051%2C1266%2C1051%2C1920%2C1200%2C1%2CP',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://www.kaercher.com/uk/home-garden/detergents/home-garden/battery-powered-window-vacs/kaercher-glass-cleaning/glass-cleaning-concentrate-500ml-62957950.html',
    'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
}


def main_one():
    folder = r'c:\DATA\kaercher\one\*.html'
    files_html = glob.glob(folder)
    heandler = ['sku_product', 'breadcrumbList', 'url_product', 'price_product', 'description_product',
                'description_full_product', 'spec_product', 'properties_product', 'featurebenefits_product',
                'name_product', 'name_img_product', 'image_product']
    with open('output_one.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for item in files_html:
            print(item)
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]

            proxi = {
                'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            }
            with open(item, encoding="utf-8") as f:
                src = f.read()
            soup = BeautifulSoup(src, 'lxml')
            all_application_ld_json = soup.find_all('script', {'type': 'application/ld+json'})

            try:
                json_text = all_application_ld_json[1].text
            except:
                continue
            data_json = json.loads(json_text)
            url_product = data_json['url']
            try:
                sku_product = data_json['sku']
            except:
                sku_product = None
            try:
                price_product = data_json['offers']['price']
            except:
                price_product = None

            description_product = data_json['description']
            try:
                spec_product = str(soup.find('div', attrs={'id': 'specifications'})).replace("\n", "")

            except:
                spec_product = None

            try:
                properties_product = str(soup.find('div', attrs={'id': 'properties'})).replace("\n", "")
            except:
                properties_product = None
            try:
                featurebenefits_product = str(soup.find('div', attrs={'id': 'featurebenefits'})).replace("\n", "")
            except:
                featurebenefits_product = None

            try:
                description_full_product = soup.find('p', attrs={'property': 'description'})
            except:
                description_full_product = None
            name_product = data_json['name']
            if sku_product is not None:
                name_img_product = sku_product.replace('.', '').replace('-', '')
            else:
                continue
            image_product = data_json['image'][0]
            file_path = f'c:\\DATA\\kaercher\\one\\img\\{name_img_product}.jpg'
            if not os.path.exists(file_path):
                img_data = requests.get(image_product, headers=headers, cookies=cookies, proxies=proxi)
                with open(file_path, 'wb') as file_img:
                    file_img.write(img_data.content)

            breadcrumbList = soup.find('ul', attrs={'typeof': 'BreadcrumbList'}).text.replace('\n', '')
            values = [sku_product, breadcrumbList, url_product, price_product, description_product,
                      description_full_product, spec_product, properties_product, featurebenefits_product, name_product,
                      name_img_product, image_product]
            writer.writerow(values)


def main_two():
    cookies = {
        'ekm%5Fmo%5Fff7c25': 'mobile%5Fdevice%5Fchk=eb350cc589d58cb5ada88eadfb38fadf&mobile%5Fdevice=false',
        'ekm%5Fff7c25': 'CookieTest=ENABLED&uid=3B7347CC%2D4D64%2D4C5C%2DA573%2DF73A8DA464A9',
        'ekmpowershop': '',
        'ASPSESSIONIDCGDSQRBB': 'DPCHJOHDOHLOJHPAKJOAKAJE',
        'paypal-offers--view-count-one-touch': '1',
        '_ga_DC3NSVHG3T': 'GS1.1.1690795045.1.0.1690795045.60.0.0',
        '_ga': 'GA1.1.819144449.1690795045',
        '_gcl_au': '1.1.1508993679.1690795045',
        '_ga_M026ZLKZMY': 'GS1.1.1690795045.1.0.1690795045.0.0.0',
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        # 'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Proxy-Authorization': 'Basic cHJveHlfYWxleDpEYnJuamhiWjg4',
        'Connection': 'keep-alive',
        # 'Cookie': 'ekm%5Fmo%5Fff7c25=mobile%5Fdevice%5Fchk=eb350cc589d58cb5ada88eadfb38fadf&mobile%5Fdevice=false; ekm%5Fff7c25=CookieTest=ENABLED&uid=3B7347CC%2D4D64%2D4C5C%2DA573%2DF73A8DA464A9; ekmpowershop=; ASPSESSIONIDCGDSQRBB=DPCHJOHDOHLOJHPAKJOAKAJE; paypal-offers--view-count-one-touch=1; _ga_DC3NSVHG3T=GS1.1.1690795045.1.0.1690795045.60.0.0; _ga=GA1.1.819144449.1690795045; _gcl_au=1.1.1508993679.1690795045; _ga_M026ZLKZMY=GS1.1.1690795045.1.0.1690795045.0.0.0',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }
    folder = r'c:\DATA\kaercher\two\*.html'
    files_html = glob.glob(folder)
    heandler = ['sku_product', 'breadcrumbList', 'url_product', 'price_product', 'description_product','spec_table_product', 'name_product',
                      'name_img_product', 'image_product']
    with open('output_two.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(heandler)  # Записываем заголовки только один ра
        for item in files_html:
            pause_time = random.randint(1, 3)
            with open(item, encoding="utf-8") as f:
                src = f.read()
            soup = BeautifulSoup(src, 'lxml')
            all_application_ld_json = soup.find_all('script', {'type': 'application/ld+json'})

            try:
                json_text = all_application_ld_json[0].text
                data_json = json.loads(json_text)

            except:
                continue
            try:
                name_product = data_json['name']
            except:
                continue
            url_product = data_json['url']
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]

            proxi = {
                'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            }
            sku_product = data_json['sku']
            try:
                name_img_product = sku_product.replace('/', '_')
            except:
                continue
            image_product = data_json['image'].replace('https://www.karcher-center-chemtec.co.uk/ekmps/shops',
                                                       'https://files.ekmcdn.com')
            # print(image_product)
            file_path = f'c:\\DATA\\kaercher\\two\\img\\{name_img_product}.jpg'
            if not os.path.exists(file_path):
                img_data = requests.get(image_product, headers=headers, cookies=cookies, proxies=proxi)
                with open(file_path, 'wb') as file_img:
                    file_img.write(img_data.content)
                # time.sleep(pause_time)
            breadcrumbList = soup.find('div', attrs={'class': 'ekmps-location'}).text.replace(' / ', '-')
            price_product = data_json['offers']['price']
            try:
                description_product = str(soup.find('div', attrs={'class': 'full-product-desc'})).replace('\n', '')
            except:
                description_product = None
            try:
                spec_table_product = str(soup.find('div', attrs={'class': 'spec-table'})).replace('\n', '')
            except:
                spec_table_product = None


            values = [sku_product, breadcrumbList, url_product, price_product, description_product,spec_table_product, name_product,
                      name_img_product, image_product]
            writer.writerow(values)


if __name__ == '__main__':
    # main_one()
    main_two()
