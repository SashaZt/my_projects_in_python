# import concurrent.futures
# import csv
#
# import requests
# from bs4 import BeautifulSoup
# from fake_useragent import UserAgent
#
# useragent = UserAgent()
#
#
# # Получаем список рабочих прокси-серверов
# def get_list_proxy():
#     r = requests.get('https://free-proxy-list.net/')
#     soup = BeautifulSoup(r.content, 'html.parser')
#     table = soup.find('tbody')
#     proxies = []
#     for row in table:
#         if row.find_all('td')[4].text == 'elite proxy':
#             proxy = ':'.join([row.find_all('td')[0].text, row.find_all('td')[1].text])
#             proxies.append(proxy)
#         else:
#             pass
#     return proxies
#
#
# # Записываем в файл рабочие сервера
# def save_proxy_to_csv(proxy):
#
#     # this was for when we took a list into the function, without conc futures.
#     # proxy = random.choice(proxylist)
#     headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
#     try:
#         # change the url to https://httpbin.org/ip that doesnt block anything
#         r = requests.get('https://httpbin.org/ip', headers=headers, proxies={'http': proxy, 'https': proxy}, timeout=1)
#         with open('proxylist.csv', "a", errors='ignore') as file:
#             writer = csv.writer(file, delimiter=";", lineterminator="\r")
#             writer.writerow(
#                 (
#                     {proxy}
#                 )
#             )
#         # print(r.json(), r.status_code)
#     except requests.ConnectionError as err:
#         print(repr(err))
#     return proxy
#
#
# proxylist = get_list_proxy()
#
# # check them all with futures super quick
# with concurrent.futures.ThreadPoolExecutor() as executor:
#     executor.map(save_proxy_to_csv, proxylist)
#
#

import requests
from bs4 import BeautifulSoup
from proxy import proxy_list

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
}

proxy = proxy_list
for i in proxy:
    proxy_host = i[0]
    proxy_port = i[1]
    proxy_user = i[2]
    proxy_pass = i[3]
    proxi = {
        'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
        'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
    }
    r = requests.get('https://httpbin.org/ip', headers=headers, proxies=proxi, timeout=1)
    json_data = r.json()
    ip_proxy = json_data['origin']
    if proxy_host == ip_proxy:
        print(f'{proxy_host} рабочий')
    else:
        print(f'{proxy_host} не рабочий')
