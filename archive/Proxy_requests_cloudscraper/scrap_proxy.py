import requests
import csv
from bs4 import BeautifulSoup
import random
import concurrent.futures


# get the list of free proxies
def getProxies():
    r = requests.get('https://free-proxy-list.net/')
    soup = BeautifulSoup(r.content, 'html.parser')
    table = soup.find('tbody')
    proxies = []
    for row in table:
        if row.find_all('td')[4].text == 'elite proxy':
            proxy = ':'.join([row.find_all('td')[0].text, row.find_all('td')[1].text])
            proxies.append(proxy)
        else:
            pass
    return proxies


def extract(proxy):
    # this was for when we took a list into the function, without conc futures.
    # proxy = random.choice(proxylist)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0'}
    try:
        # change the url to https://httpbin.org/ip that doesnt block anything
        r = requests.get('https://httpbin.org/ip', headers=headers, proxies={'http': proxy, 'https': proxy}, timeout=1)
        with open('proxylist.csv', "a", errors='ignore') as file:
            writer = csv.writer(file, delimiter=";", lineterminator="\r")
            writer.writerow(
                (
                    {proxy}
                )
            )
        # print(r.json(), r.status_code)
    except requests.ConnectionError as err:
        print(repr(err))
    return proxy


proxylist = getProxies()

# check them all with futures super quick
with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(extract, proxylist)
