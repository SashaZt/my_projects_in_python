from bs4 import BeautifulSoup
import csv
from rich import print
import random
import pandas as pd
import os
import glob
import requests
import time
import json
from proxi import proxies

"""Рабочи скрипт"""
cookies = {
    'v': '1687507051_be3c3709-b6c0-4ae1-a506-2a2beba5b098_4a30af50d9ae1ab5ff4d9ecb20c62cfa',
    'vct': 'en-US-CR9rUJVk8B9rUJVkSBxrUJVk4R1rUJVk4h1rUJVk',
    '_csrf': 'foSkkM6_E6wKQNZtIt3yNl3F',
    'prf': 'prodirDistFil%7C%7D',
    'hzd': '02c2e91f-3cb0-436f-ad33-068d827b641c%3A6540628%3Adisplay_name_pro_dir%3Ao%3A3%3A3%3Ad%3Abrowse_pro%3A2%3AVerifiedLicense',
    '_gid': 'GA1.2.1561165104.1687507055',
    '_gat': '1',
    '_gcl_au': '1.1.938942522.1687507055',
    '_ga_PB0RC2CT7B': 'GS1.1.1687507054.1.0.1687507054.60.0.0',
    '_ga': 'GA1.1.340411067.1687507055',
    '_uetsid': '9d1a5b80119b11eeb3959513fec91032',
    '_uetvid': '9d1a7d40119b11ee8cdfe3191853765a',
    '_sp_ses.c905': '*',
    '_sp_id.c905': '9379c154-a074-45ad-ae3e-732e1d4473ee.1687507055.1.1687507055.1687507055.7e74ed6b-239f-4ae5-9f65-be99aa2edfa4',
    'IR_gbd': 'houzz.com',
    'IR_5455': '1687507055140%7C0%7C1687507055140%7C%7C',
    'ln_or': 'eyIzODE1NzE2IjoiZCJ9',
    '_pin_unauth': 'dWlkPU1ESm1NalV6WkRFdE1qZzBNQzAwTXpReUxUazFOREl0T0daaU16QXhOR05rTVRVMA',
    'crossdevicetracking': '6b53ecca-c36c-4f80-8b9d-3d765803bc51',
    'documentWidth': '940',
    'jdv': 't7WOzUb2vHLZtWVVHSk9XJMdN7ua9zR%2FUkXoZtQMDxPlgkBDnOmreue175uoTwe7WLcuJcvxFwz9ShkgfTvhjY%2F6sIoS',
}

headers = {
    'authority': 'www.houzz.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru',
    'cache-control': 'no-cache',
    # 'cookie': 'v=1687507051_be3c3709-b6c0-4ae1-a506-2a2beba5b098_4a30af50d9ae1ab5ff4d9ecb20c62cfa; vct=en-US-CR9rUJVk8B9rUJVkSBxrUJVk4R1rUJVk4h1rUJVk; _csrf=foSkkM6_E6wKQNZtIt3yNl3F; prf=prodirDistFil%7C%7D; hzd=02c2e91f-3cb0-436f-ad33-068d827b641c%3A6540628%3Adisplay_name_pro_dir%3Ao%3A3%3A3%3Ad%3Abrowse_pro%3A2%3AVerifiedLicense; _gid=GA1.2.1561165104.1687507055; _gat=1; _gcl_au=1.1.938942522.1687507055; _ga_PB0RC2CT7B=GS1.1.1687507054.1.0.1687507054.60.0.0; _ga=GA1.1.340411067.1687507055; _uetsid=9d1a5b80119b11eeb3959513fec91032; _uetvid=9d1a7d40119b11ee8cdfe3191853765a; _sp_ses.c905=*; _sp_id.c905=9379c154-a074-45ad-ae3e-732e1d4473ee.1687507055.1.1687507055.1687507055.7e74ed6b-239f-4ae5-9f65-be99aa2edfa4; IR_gbd=houzz.com; IR_5455=1687507055140%7C0%7C1687507055140%7C%7C; ln_or=eyIzODE1NzE2IjoiZCJ9; _pin_unauth=dWlkPU1ESm1NalV6WkRFdE1qZzBNQzAwTXpReUxUazFOREl0T0daaU16QXhOR05rTVRVMA; crossdevicetracking=6b53ecca-c36c-4f80-8b9d-3d765803bc51; documentWidth=940; jdv=t7WOzUb2vHLZtWVVHSk9XJMdN7ua9zR%2FUkXoZtQMDxPlgkBDnOmreue175uoTwe7WLcuJcvxFwz9ShkgfTvhjY%2F6sIoS',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}


def get_category():
    response = requests.get('https://www.houzz.com/professionals/architect/probr0-bo~t_11784', cookies=cookies,
                            headers=headers)  # Используйте индекс 0, чтобы получить URL из списка
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    script_json = soup.find('script', type="application/json")
    data_json = json.loads(script_json.string)
    urls_all = data_json['data']['stores']['data']['NavigationStore']['data']['filters'][2]['options']
    urls = []
    for item in urls_all:
        options = item['options']
        for option in options:
            url = option['url']
            urls.append(url)

    print(urls)


def get_requests(url):
    data_url = []

    group = url.split('/')[-2]
    print(f'Собираем категорию {group}')
    response = requests.get(url, cookies=cookies, headers=headers)
    src = response.text
    soup = BeautifulSoup(src, 'lxml')
    script_json = soup.find('script', type="application/json")
    data_json = json.loads(script_json.string)
    try:
        pagination_total = int(
            data_json['data']['stores']['data']['ViewProfessionalsStore']['data']['paginationSummary']['total'].replace(
                ',',
                ''))
    except:
        print(f'Нет данных вкатегории {group}')
        return

    amount_page = pagination_total // 15
    print(f"Всего {pagination_total} а файлов будет {amount_page + 2}")
    coun = 0
    for i in range(1, amount_page + 2):
        proxy = random.choice(proxies)
        proxy_host = proxy[0]
        proxy_port = proxy[1]
        proxy_user = proxy[2]
        proxy_pass = proxy[3]

        proxi = {
            'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
            'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
        }
        # pause_time = random.randint(1, 10) #Случайное число

        # Пауза в секундах
        if i == 1:
            filename = f"c:\\DATA\\houzz_com\\list\\{group}\\data_{coun}.html"
            if not os.path.exists(filename):
                url_first = url
                try:
                    response = requests.get(url_first, cookies=cookies, headers=headers, proxies=proxi)
                except:
                    continue
                with open(filename, "w", encoding='utf-8') as file:
                    file.write(response.text)
                # time.sleep(pause_time)
                with open('log.txt', 'a') as f:
                    print(url_first, file=f)
            else:
                continue
        elif i > 1:
            coun += 15
            filename = f"c:\\DATA\\houzz_com\\list\\{group}\\data_{coun}.html"
            if not os.path.exists(filename):
                urls = f'{url}?fi={coun}'
                # urls = f'{url}?fi={coun}' #Если Испания
                try:
                    response = requests.get(urls, cookies=cookies, headers=headers, proxies=proxi)
                except:
                    continue
                with open(filename, "w", encoding='utf-8') as file:
                    file.write(response.text)
                with open('log.txt', 'a') as f:
                    print(urls, file=f)
                # time.sleep(pause_time)
            else:
                continue
        print(f'Сейчас {coun} из {pagination_total} ')

    print('Собрали все html')


def parsing():
    group = 'electrical-contractors'
    # print(group)
    data_url = []
    try:
        folders_html = [fr"c:\DATA\houzz_com\list\{group}\*.html"]
    except:
        return
    filename = f'C:\\scrap_tutorial-master\\houzz_es\\url\\{group}.csv'
    print(filename)
    for file in folders_html:
        files_json = glob.glob(file)
        for item in files_json:
            with open(item, encoding="utf-8") as file:
                src = file.read()
            soup = BeautifulSoup(src, 'lxml')
            try:
                products_urls = soup.find('ul', attrs={'class': 'hz-pro-search-results mb0'}).find_all('a')
            except:
                print(item)
                continue
            for u in products_urls:
                url = u.get("href")
                data_url.append([url])  # Оборачиваем URL-адрес в список

    with open(f'url/{group}.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data_url)  # Записываем данные построчно

    print(f"Данные успешно записаны в файл {group}.csv.")


def drop_duplicates(group):
    all_csv = [
        f'C:\\scrap_tutorial-master\\houzz_es\\url\\houzz_com\\{group}.csv'
    ]
    for f in all_csv:
        try:
            df = pd.read_csv(f)
        except:
            continue

        # удалить дубликаты строк и сохранить уникальные строки в новом DataFrame
        df_unique = df.drop_duplicates()

        # сохранить уникальные строки в CSV-файл
        df_unique.to_csv(f'url/{group}.csv', index=False)
    print("Дубликты удалили")


if __name__ == '__main__':
    # get_category()
    urls = [
        'https://www.houzz.com/professionals/architect/probr0-bo~t_11784',
        'https://www.houzz.com/professionals/design-build/probr0-bo~t_11793',
        'https://www.houzz.com/professionals/general-contractor/probr0-bo~t_11786',
        'https://www.houzz.com/professionals/home-builders/probr0-bo~t_11823',
        'https://www.houzz.com/professionals/interior-designer/probr0-bo~t_11785',
        'https://www.houzz.com/professionals/kitchen-and-bath/probr0-bo~t_11790',
        'https://www.houzz.com/professionals/kitchen-and-bath-remodelers/probr0-bo~t_11825',
        'https://www.houzz.com/professionals/landscape-architect/probr0-bo~t_11788',
        'https://www.houzz.com/professionals/landscape-contractors/probr0-bo~t_11812',
        'https://www.houzz.com/professionals/adu-contractors/probr0-bo~t_34256',
        'https://www.houzz.com/professionals/home-remodeling/probr0-bo~t_34257',
        'https://www.houzz.com/professionals/home-additions-and-extensions/probr0-bo~t_34259',
        'https://www.houzz.com/professionals/siding-and-exterior/probr0-bo~t_11826',
        'https://www.houzz.com/professionals/fireplace/probr0-bo~t_11800',
        'https://www.houzz.com/professionals/garage-doors/probr0-bo~t_11828',
        'https://www.houzz.com/professionals/building-supplies/probr0-bo~t_11805',
        'https://www.houzz.com/professionals/stone-pavers-and-concrete/probr0-bo~t_11824',
        'https://www.houzz.com/professionals/specialty-contractors/probr0-bo~t_11811',
        'https://www.houzz.com/professionals/staircases/probr0-bo~t_11839',
        'https://www.houzz.com/professionals/wine-cellars/probr0-bo~t_11841',
        'https://www.houzz.com/professionals/custom-countertops/probr0-bo~t_33909',
        'https://www.houzz.com/professionals/tile-and-stone-contractors/probr0-bo~t_33910',
        'https://www.houzz.com/professionals/basement-remodelers/probr0-bo~t_34261',
        'https://www.houzz.com/professionals/bedding-and-bath/probr0-bo~t_11806',
        'https://www.houzz.com/professionals/cabinets/probr0-bo~t_11829',
        'https://www.houzz.com/professionals/carpenter/probr0-bo~t_11831',
        'https://www.houzz.com/professionals/carpet-and-flooring/probr0-bo~t_11799',
        'https://www.houzz.com/professionals/doors/probr0-bo~t_11827',
        'https://www.houzz.com/professionals/environmental-services-and-restoration/probr0-bo~t_11813',
        'https://www.houzz.com/professionals/hardwood-flooring-dealers/probr0-bo~t_28349',
        'https://www.houzz.com/professionals/furniture-and-accessories/probr0-bo~t_11802',
        'https://www.houzz.com/professionals/furniture-refinishing-and-upholstery/probr0-bo~t_11840',
        'https://www.houzz.com/professionals/glass-and-shower-door-dealers/probr0-bo~t_27203',
        'https://www.houzz.com/professionals/ironwork/probr0-bo~t_11834',
        'https://www.houzz.com/professionals/kitchen-and-bath-fixtures/probr0-bo~t_11804',
        'https://www.houzz.com/professionals/lighting/probr0-bo~t_11794',
        'https://www.houzz.com/professionals/windows/probr0-bo~t_11797',
        'https://www.houzz.com/professionals/universal-design/probr0-bo~t_34260',
        'https://www.houzz.com/professionals/backyard-courts/probr0-bo~t_11838',
        'https://www.houzz.com/professionals/decks-and-patios/probr0-bo~t_11830',
        'https://www.houzz.com/professionals/driveways-and-paving/probr0-bo~t_11832',
        'https://www.houzz.com/professionals/fencing-and-gates/probr0-bo~t_11833',
        'https://www.houzz.com/professionals/garden-and-landscape-supplies/probr0-bo~t_11809',
        'https://www.houzz.com/professionals/lawn-and-sprinklers/probr0-bo~t_11835',
        'https://www.houzz.com/professionals/hot-tub-and-spa-dealers/probr0-bo~t_28350',
        'https://www.houzz.com/professionals/outdoor-lighting-and-audio-visual-systems/probr0-bo~t_11836',
        'https://www.houzz.com/professionals/outdoor-play/probr0-bo~t_11837',
        'https://www.houzz.com/professionals/spa-and-pool-maintenance/probr0-bo~t_28351',
        'https://www.houzz.com/professionals/pools-and-spas/probr0-bo~t_11795',
        'https://www.houzz.com/professionals/tree-service/probr0-bo~t_11821',
        'https://www.houzz.com/professionals/custom-closet-designers/probr0-bo~t_33907',
        'https://www.houzz.com/professionals/professional-organizers/probr0-bo~t_33908',
        'https://www.houzz.com/professionals/artist-and-artisan/probr0-bo~t_11801',
        'https://www.houzz.com/professionals/handyman/probr0-bo~t_27204',
        'https://www.houzz.com/professionals/home-staging/probr0-bo~t_11789',
        'https://www.houzz.com/professionals/movers/probr0-bo~t_27206',
        'https://www.houzz.com/professionals/paint-and-wall-coverings/probr0-bo~t_11807',
        'https://www.houzz.com/professionals/painters/probr0-bo~t_27105',
        'https://www.houzz.com/professionals/photographer/probr0-bo~t_11792',
        'https://www.houzz.com/professionals/agents-and-brokers/probr0-bo~t_11822',
        'https://www.houzz.com/professionals/roofing-and-gutter/probr0-bo~t_11819',
        'https://www.houzz.com/professionals/window-coverings/probr0-bo~t_11798',
        'https://www.houzz.com/professionals/appliances/probr0-bo~t_11810',
        'https://www.houzz.com/professionals/electrical-contractors/probr0-bo~t_11818',
        'https://www.houzz.com/professionals/home-media/probr0-bo~t_11787',
        'https://www.houzz.com/professionals/hvac-contractors/probr0-bo~t_11814',
        'https://www.houzz.com/professionals/plumbing-contractors/probr0-bo~t_11817',
        'https://www.houzz.com/professionals/septic-tanks-and-systems/probr0-bo~t_11815',
        'https://www.houzz.com/professionals/solar-energy-contractors/probr0-bo~t_11816',
        'https://www.houzz.com/professionals/carpet-cleaners/probr0-bo~t_27201',
        'https://www.houzz.com/professionals/chimney-cleaners/probr0-bo~t_27200',
        'https://www.houzz.com/professionals/exterior-cleaners/probr0-bo~t_27202',
        'https://www.houzz.com/professionals/house-cleaners/probr0-bo~t_27205',
        'https://www.houzz.com/professionals/rubbish-removal/probr0-bo~t_11820',
        'https://www.houzz.com/professionals/pest-control/probr0-bo~t_27207',
        'https://www.houzz.com/professionals/window-cleaners/probr0-bo~t_27209']

    for url in urls:
        group = url.split('/')[-2]
        folder_path = f"c:\\DATA\\houzz_com\\product\\{group}"
        if os.path.exists(folder_path):
            continue  # Пропустить итерацию, если папка уже существует
        os.mkdir(folder_path)
        # get_requests(url)
        # parsing()
        # drop_duplicates(group)
        # print(f'Категория {group} готова')
    # # time.sleep(10)
