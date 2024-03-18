import csv

import requests
from bs4 import BeautifulSoup


def get_onelab():
    cookies = {
        'we.ss.re': 's%3ASkum0FSlLW3gRvC1gzC9okwXYUmV4PMF.5GG85WbgiTRgyE1Fe2BOzoIc142Iq21q2Y97jKKmJdE',
        '_ga_GRSQWWV2KT': 'GS1.1.1690807485.1.0.1690807485.0.0.0',
        '_ga': 'GA1.1.1078542883.1690807486',
    }

    headers = {
        'authority': 'onelab.com.ua',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'we.ss.re=s%3ASkum0FSlLW3gRvC1gzC9okwXYUmV4PMF.5GG85WbgiTRgyE1Fe2BOzoIc142Iq21q2Y97jKKmJdE; _ga_GRSQWWV2KT=GS1.1.1690807485.1.0.1690807485.0.0.0; _ga=GA1.1.1078542883.1690807486',
        'dnt': '1',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    response = requests.get('https://onelab.com.ua/ua/analyses', cookies=cookies, headers=headers)
    with open(f"data_onelab.html", "w", encoding='utf-8') as file:
        file.write(response.text)


def parsing_onelab():
    file = f"data_onelab.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    rows = soup.find_all('tr', class_='a-an')
    data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.replace('\n', '').strip() for ele in cols]
        cols[1] = cols[1].replace("[", "").replace("]", "")  # Удаляем скобки только из первого элемента
        data.append([ele for ele in cols if ele])
    with open('onelab.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=",")
        headers = ["Id", "Description", "Time", "Cost"]  # Замените на свои заголовки
        writer.writerow(headers)
        writer.writerows(data)
    # for item in data[:1]:
    #     print(item)


if __name__ == '__main__':
    get_onelab()
    parsing_onelab()
