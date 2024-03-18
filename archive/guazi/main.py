import csv
import glob
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

from browsermobproxy import Server
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

# """Используется для Chrome баузера"""
# from concurrent.futures import ProcessPoolExecutor
"""Используется для response"""
import requests
from googletrans import Translator, LANGUAGES

translator = Translator()

def translate_text(text, src_lang, dest_lang):
    translated = translator.translate(text, src=src_lang, dest=dest_lang)
    return translated.text

"""Настройка browsermob-proxy"""
server_options = {
    'log_path': 'NUL'
}

server = Server(r"c:\Program Files (x86)\browsermob-proxy\bin\browsermob-proxy", options=server_options)
server.start()
proxy = server.create_proxy()


def get_chromedriver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(
        f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument("--proxy-server={0}".format(proxy.proxy))
    chrome_options.add_argument("--start-maximized")
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument('--auto-open-devtools-for-tabs=devtools://devtools/bundled/inspector.html')

    s = Service(executable_path="C:\\scrap_tutorial-master\\chromedriver.exe")
    driver = webdriver.Chrome(service=s, options=chrome_options)

    return driver


def main():
    ad = 80
    page_ad = ad // 100
    start = 0
    # for i in range(0, 1):
    for i in range(1, ad + 1):
        filename = f"c:\\DATA\\guazi\\list\\data_{i}.json"
        if not os.path.exists(filename):
            cookies = {
                'uuid': 'ea69252c-f0bd-404c-aab6-9dc341182319',
                'sessionid': '012297e3-851e-4e44-a90a-013ca90d8773',
                'cainfo': '%7B%22ca_s%22%3A%22self%22%2C%22ca_n%22%3A%22self%22%2C%22ca_medium%22%3A%22-%22%2C%22ca_term%22%3A%22-%22%2C%22ca_content%22%3A%22-%22%2C%22ca_campaign%22%3A%22-%22%2C%22ca_kw%22%3A%22-%22%2C%22ca_i%22%3A%22-%22%2C%22scode%22%3A%22-%22%2C%22guid%22%3A%22ea69252c-f0bd-404c-aab6-9dc341182319%22%7D',
            }

            headers = {
                'authority': 'mapi.guazi.com',
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
                'anti-token': '1277105907',
                'client-time': '1695811402',
                'client-timestamp': '1695811000',
                # 'cookie': 'uuid=ea69252c-f0bd-404c-aab6-9dc341182319; sessionid=012297e3-851e-4e44-a90a-013ca90d8773; cainfo=%7B%22ca_s%22%3A%22self%22%2C%22ca_n%22%3A%22self%22%2C%22ca_medium%22%3A%22-%22%2C%22ca_term%22%3A%22-%22%2C%22ca_content%22%3A%22-%22%2C%22ca_campaign%22%3A%22-%22%2C%22ca_kw%22%3A%22-%22%2C%22ca_i%22%3A%22-%22%2C%22scode%22%3A%22-%22%2C%22guid%22%3A%22ea69252c-f0bd-404c-aab6-9dc341182319%22%7D',
                'dnt': '1',
                'origin': 'https://www.guazi.com',
                'platform': '5',
                'referer': 'https://www.guazi.com/',
                'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'szlm-id': 'D2L9BVIH0OCwiGPV5YXGXqjqD2b/dATg3OAsBNY/6GBnUX9d',
                'token': '',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
                'verify-token': 'cfec1ec59af05847b2a5568a51b19f74',
            }

            response = requests.get(
                f'https://mapi.guazi.com/car-source/carList/pcList?versionId=0.0.0.0&sourceFrom=wap&deviceId=ea69252c-f0bd-404c-aab6-9dc341182319&osv=Windows+10&minor=bmw&sourceType=&ec_buy_car_list_ab=&location_city=&district_id=&tag=-1&license_date=&auto_type=&driving_type=&gearbox=&road_haul=&air_displacement=&emission=&car_color=&guobie=&bright_spot_config=&seat=&fuel_type=&order=&priceRange=0,-1&tag_types=&diff_city=&intention_options=&initialPriceRange=&monthlyPriceRange=&transfer_num=&car_year=&carid_qigangshu=&carid_jinqixingshi=&cheliangjibie=&page={i}&pageSize=20&city_filter=16&city=16&guazi_city=16&qpres=720167730262573056&platfromSource=wap',
                cookies=cookies,
                headers=headers,
            )
            data = response.json()

            with open(filename, 'w') as f:
                json.dump(data, f)
            time.sleep(1)
        start += 100
    print(f'Все {ad} страницы скачаны')


def get_id_ad_and_url():
    folders_html = r"c:\DATA\guazi\list\*.json"
    files_html = glob.glob(folders_html)
    file_csv = f"url.csv"
    with open(file_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for i in files_html:
            with open(i, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            content = json_data['data']['postList']
            for c in content:
                url_ad = f'https://www.guazi.com/Detail?clueId={c["clue_id"]}'
                writer.writerow([url_ad])
    print('Получили список всех url')


def split_urls(urls, n):
    """Делит список URL-адресов на n равных частей."""
    avg = len(urls) // n
    urls_split = [urls[i:i + avg] for i in range(0, len(urls), avg)]
    return urls_split


def worker(sub_urls, start_counter):
    driver = get_chromedriver()
    for counter, url in enumerate(sub_urls, start=start_counter):
        try:
            filename = f"c:\\DATA\\guazi\\product\\data_{counter}.html"
            if not os.path.exists(filename):
                driver.get(url[0])
                driver.execute_script("window.scrollBy(0,2000)", "")
                time.sleep(3)

                with open(filename, "w", encoding='utf-8') as fl:
                    fl.write(driver.page_source)

        except Exception as e:
            print(f"Error processing URL {url[0]}: {e}")
    driver.quit()


def get_product_s():
    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        max_workers = 5
        splitted_urls = split_urls(urls, max_workers)
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            for idx, sub_urls in enumerate(splitted_urls):
                executor.submit(worker, sub_urls, idx * len(sub_urls))


"""Следующие 3 функции для работы с Selenium"""


def parsing():
    file = "c:\\DATA\\guazi\\product\\data_988.html"
    with open(file, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    # b_i = soup.find_all('span', attrs={'class': 'type-gray'})
    # for u in b_i:
    #     basic_information = u.text
    #     translated_text_basic_information = translate_text(basic_information, 'zh-CN', 'en')
    #     print(translated_text_basic_information)
    b_e_i = soup.find_all('li', attrs={'class': 'basic-eleven-li'})
    for u in b_e_i[:2]:
        div_text = u.div.get_text(strip=True)
        li_text_without_div = u.get_text(strip=True).replace(div_text, '')
        st = f'{div_text} {li_text_without_div}'
        translated_text_basic_eleven_li = translate_text(st, 'zh-CN', 'en')
        print(st)

if __name__ == '__main__':
    # main()
    # get_id_ad_and_url()
    # get_product_r()
    # get_product_s()
    parsing()
