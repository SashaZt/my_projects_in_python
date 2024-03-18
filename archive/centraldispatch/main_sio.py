import os
import csv
import requests
import random
import time
from proxi import proxies

cookies = {
    'test-session': '1',
    'CSRF_TOKEN': '27049938f262c4d945ff09032720e8035973c63b8406d6ce868598079374c98f',
    'test-persistent': '1',
    'test-session': '1',
    'visitedDashboard': '1',
    'BVBRANDID': '620af17a-81da-42a6-8734-2797d91a1470',
    'PHPSESSID': '58041e67572321503a8912b5199cb8db',
}

headers = {
    'authority': 'www.centraldispatch.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'cache-control': 'no-cache',
    # 'cookie': 'test-session=1; CSRF_TOKEN=27049938f262c4d945ff09032720e8035973c63b8406d6ce868598079374c98f; test-persistent=1; test-session=1; visitedDashboard=1; BVBRANDID=620af17a-81da-42a6-8734-2797d91a1470; PHPSESSID=58041e67572321503a8912b5199cb8db',
    'dnt': '1',
    'pragma': 'no-cache',
    'referer': 'https://id.centraldispatch.com/',
    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-site',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}



def main():
    counter = 0
    with open(f'C:\\scrap_tutorial-master\\centraldispatch\\url\\url_products.csv', newline='',
              encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        for url in urls:
            pause_time = random.randint(10, 20)
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]

            proxi = {
                'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            }
            counter += 1
            filename = f"c:\\DATA\\centraldispatch\\products\\data_{counter}.html"
            if os.path.isfile(filename):
                continue  # Если файл уже существует, переходим к следующей итерации цикла
            try:
                response = requests.get(url[0], cookies=cookies, headers=headers, proxies=proxi)
                src = response.text
                filename = f"c:\\DATA\\centraldispatch\\products\\data_{counter}.html"
                with open(filename, "w", encoding='utf-8') as file:
                    file.write(src)
                    print(f"Сохранил {filename}")
                    print(f'Пауза {pause_time}')
                    time.sleep(pause_time)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    main()
