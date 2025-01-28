import requests
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
import time
import requests
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Установка директорий для логов и данных
current_directory = Path.cwd()
html_directory = current_directory / "html"
json_directory = current_directory / "json"
configuration_directory = current_directory / "configuration"
# Пути к файлам
output_csv_file = current_directory / "urls.csv"
txt_file_proxies = configuration_directory / "proxies.txt"
# Создание директорий, если их нет
html_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
configuration_directory.mkdir(parents=True, exist_ok=True)

cookies = {
    'lurl': '8b2f917b175e2095510e4a345d44d5677638189a846a7792241ddad7a435d94da%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22lurl%22%3Bi%3A1%3Bs%3A61%3A%22http%3A%2F%2Fyoucontrol.com.ua%2Fru%2Fcatalog%2Fcompany_details%2F00032945%2F%22%3B%7D',
    'catalog-register-banner': '1',
    'spm1': 'c4fa386f23d7a166a29d233e48304b4f',
    'utrt': '2df7b9d058477bfb4a34eaa816bd87beddb0d1f68cc7a3c843038a665b9202e8a%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22utrt%22%3Bi%3A1%3Bi%3A11780115%3B%7D',
    '_csrf-frontend': '963c6d68d9bec8f5164308401be997f85c97786661c3c6f76e11e3ed0a1ff0f7a%3A2%3A%7Bi%3A0%3Bs%3A14%3A%22_csrf-frontend%22%3Bi%3A1%3Bs%3A32%3A%22HFKQ8c-sSiC2G6eC3OzIxCyfZZahW8is%22%3B%7D',
    'hide-ios-homescreen': '2',
}

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru,en;q=0.9,uk;q=0.8',
    'cache-control': 'no-cache',
    # 'cookie': 'lurl=8b2f917b175e2095510e4a345d44d5677638189a846a7792241ddad7a435d94da%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22lurl%22%3Bi%3A1%3Bs%3A61%3A%22http%3A%2F%2Fyoucontrol.com.ua%2Fru%2Fcatalog%2Fcompany_details%2F00032945%2F%22%3B%7D; catalog-register-banner=1; spm1=c4fa386f23d7a166a29d233e48304b4f; utrt=2df7b9d058477bfb4a34eaa816bd87beddb0d1f68cc7a3c843038a665b9202e8a%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22utrt%22%3Bi%3A1%3Bi%3A11780115%3B%7D; _csrf-frontend=963c6d68d9bec8f5164308401be997f85c97786661c3c6f76e11e3ed0a1ff0f7a%3A2%3A%7Bi%3A0%3Bs%3A14%3A%22_csrf-frontend%22%3Bi%3A1%3Bs%3A32%3A%22HFKQ8c-sSiC2G6eC3OzIxCyfZZahW8is%22%3B%7D; hide-ios-homescreen=2',
    'dnt': '1',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    'sec-ch-ua-arch': '"x86"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version': '"131.0.6778.265"',
    'sec-ch-ua-full-version-list': '"Google Chrome";v="131.0.6778.265", "Chromium";v="131.0.6778.265", "Not_A Brand";v="24.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"Windows"',
    'sec-ch-ua-platform-version': '"19.0.0"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

def download_xml(url, filename):
    response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        return response.content
    else:
        print(f"Ошибка при скачивании {url}: {response.status_code}")
        return None

def extract_urls(xml_content):
    urls = []
    root = ET.fromstring(xml_content)
    for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
        urls.append(loc.text)
    return urls

def save_to_csv(urls, filename):
    df = pd.DataFrame({'url': urls})
    df.to_csv(filename, index=False)

def main_xml():
    sitemap_url = 'https://youcontrol.com.ua/sitemap.xml'
    sitemap_content = download_xml(sitemap_url, 'sitemap.xml')
    print("Скачал основной sitemap.xml")
    
    company_sitemaps = []
    root = ET.fromstring(sitemap_content)
    for loc in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
        if 'company' in loc.text:
            company_sitemaps.append(loc.text)
    
    all_urls = []
    for i, sitemap in enumerate(company_sitemaps, start=1):
        sitemap_filename = f'company_sitemap_{i}.xml'
        sitemap_content = download_xml(sitemap, sitemap_filename)
        if sitemap_content:
            print(f"Скачал {sitemap} и сохранил как {sitemap_filename}")
            urls = extract_urls(sitemap_content)
            all_urls.extend(urls)
    
    save_to_csv(all_urls, 'urls.csv')
    print(f'Всего URL-адресов: {len(all_urls)}')
def work_csv():
    # Загрузка файлов CSV
    urls_df = pd.read_csv('urls.csv', names=['url'])
    edrpo_df = pd.read_csv('edrpo.csv', names=['edrpo'])

    # Создание нового столбца 'edrpo' в urls_df
    urls_df['edrpo'] = urls_df['url'].str.extract(r'/(\d+)/$', expand=False)

    # Объединение DataFrame по столбцу 'edrpo'
    matched_df = pd.merge(urls_df, edrpo_df, on='edrpo', how='inner')

    # Выбор только столбца 'url' и запись в новый файл
    matched_df[['url']].to_csv('matched_urls.csv', index=False, header=['url'])
def download_html(url):
    cookies = {
    'lurl': '05b5670e5ccc4a601610ac92419f7c5ca460797a6fdb78922f7d5d16475c50a8a%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22lurl%22%3Bi%3A1%3Bs%3A36%3A%22http%3A%2F%2Fyoucontrol.com.ua%2Fsitemap.xml%22%3B%7D',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru,en;q=0.9,uk;q=0.8',
        'cache-control': 'no-cache',
        # 'cookie': 'lurl=05b5670e5ccc4a601610ac92419f7c5ca460797a6fdb78922f7d5d16475c50a8a%3A2%3A%7Bi%3A0%3Bs%3A4%3A%22lurl%22%3Bi%3A1%3Bs%3A36%3A%22http%3A%2F%2Fyoucontrol.com.ua%2Fsitemap.xml%22%3B%7D',
        'dnt': '1',
        'pragma': 'no-cache',
        'priority': 'u=0, i',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-bitness': '"64"',
        'sec-ch-ua-full-version': '"131.0.6778.265"',
        'sec-ch-ua-full-version-list': '"Google Chrome";v="131.0.6778.265", "Chromium";v="131.0.6778.265", "Not_A Brand";v="24.0.0.0"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-ch-ua-platform-version': '"19.0.0"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30
                                )
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при скачивании {url}: {e}")
        return None

    

def download_and_save(url):
    file_name = url.split("/")[-2] + ".html"
    file_path = html_directory / file_name
    if file_path.exists():
        return None
    html_content = download_html(url)
    if html_content:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(html_content)
        time.sleep(5)

def main_html():
    # Чтение файла matched_urls.csv
    urls_df = pd.read_csv("matched_urls.csv")
    urls = urls_df["url"].tolist()

    # Создание директории для сохранения HTML-файлов
    html_directory.mkdir(exist_ok=True)

    # Многопоточное скачивание HTML-файлов
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(download_and_save, url) for url in urls]
        for future in as_completed(futures):
            future.result()
if __name__ == '__main__':
    # main_xml()
    # work_csv()
    main_html()
    