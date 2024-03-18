# -*- coding: utf-8 -*-
import re
import csv
import requests
import os
import glob
import random
from proxi import proxies
from bs4 import BeautifulSoup
cookies = {
    '__RequestVerificationToken': 'TxHTdVxPPCKp06aHX5stfQMDHAUQOQBWdFWORtHYgY8jQbtd2pwiBz3b-djVXr1VaXEuSLhR10saBvDoB98Va3cvEH8MlW5qsPB6VIa0lA81',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    # 'Cookie': '__RequestVerificationToken=TxHTdVxPPCKp06aHX5stfQMDHAUQOQBWdFWORtHYgY8jQbtd2pwiBz3b-djVXr1VaXEuSLhR10saBvDoB98Va3cvEH8MlW5qsPB6VIa0lA81',
    'DNT': '1',
    'Referer': 'https://licensedbuilderregistry.bchousing.org/LicenceRegistry/LicenceSearch?LicType=General%20Contractor&Loc=Any%20Location&Area=Any&LicStat=In%20Good%20Standing%2A',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

params = {
    'LicType': 'Any',
    'Loc': 'Any Location',
    'Area': 'Any',
    'LicStat': 'In Good Standing*',
}

response = requests.get(
    'https://licensedbuilderregistry.bchousing.org/LicenceRegistry/LicenceSearch',
    params=params,
    cookies=cookies,
    headers=headers,
)
src = response.text
filename = f"any.html"
with open(filename, "w", encoding='utf-8') as file:
    file.write(src)
current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)

def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

def proxy_random():
    """
    Функция для случайного прокси
    """
    proxy = random.choice(proxies)
    proxy_host = proxy[0]
    proxy_port = proxy[1]
    proxy_user = proxy[2]
    proxy_pass = proxy[3]
    formatted_proxy = f"http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"

    # Возвращаем словарь с прокси
    return {"http": formatted_proxy, "https": formatted_proxy}
def parsing():
    from bs4 import BeautifulSoup
    filename = f"any.html"
    with open(filename, encoding="utf-8") as file:
        src = file.read()
    soup = BeautifulSoup(src, 'lxml')
    all_url = soup.find_all('a', {'class': 'list-group-item list-group-item-action search-result'})
    data_cmd_arg = []
    for a in all_url:
        url = a.get('data-cmd-arg')
        data_cmd_arg.append(url)
    return data_cmd_arg

def get_all_html():
    all_data = parsing()
    for a in all_data:

        cookies = {
            '__RequestVerificationToken': 'TxHTdVxPPCKp06aHX5stfQMDHAUQOQBWdFWORtHYgY8jQbtd2pwiBz3b-djVXr1VaXEuSLhR10saBvDoB98Va3cvEH8MlW5qsPB6VIa0lA81',
        }

        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            # 'Cookie': '__RequestVerificationToken=TxHTdVxPPCKp06aHX5stfQMDHAUQOQBWdFWORtHYgY8jQbtd2pwiBz3b-djVXr1VaXEuSLhR10saBvDoB98Va3cvEH8MlW5qsPB6VIa0lA81',
            'DNT': '1',
            'Origin': 'https://licensedbuilderregistry.bchousing.org',
            'Referer': 'https://licensedbuilderregistry.bchousing.org/LicenceRegistry/LicenceSearch?LicType=Any&Loc=Any%20Location&Area=Any&LicStat=In%20Good%20Standing%2A',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

        data = {
            'iLicenceNumber': a,
            'sPartialPrefix': 'LicenceDetailsViewModel',
        }
        filename = os.path.join(temp_path, f"{a}.html")
        if not os.path.exists(filename):
            proxi = proxy_random()
            response = requests.post(
                'https://licensedbuilderregistry.bchousing.org/Shared/LicenceSelected',
                cookies=cookies,
                headers=headers,
                data=data, proxies=proxi
            )
            if response.status_code == 200:
                src = response.text

                with open(filename, "w", encoding='utf-8') as file:
                    file.write(src)
def parse_contact_info(contact_info):
    if not contact_info:
        return None, None, None, None

    # Удаление указанных фраз
    phrases_to_remove = ["Public Contact Number", "Public Fax Number", "Public Alternate Phone Number"]
    for phrase in phrases_to_remove:
        contact_info = contact_info.replace(phrase, '')

    # Ищем электронную почту
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', contact_info)
    email = email_match.group(0) if email_match else None

    # Извлекаем и удаляем электронную почту из строки
    if email:
        contact_info = contact_info.replace(email, '')
    # Ищем веб-сайт
    website_match = re.search(r'(?:http[s]?://)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', contact_info)
    website = website_match.group(0) if website_match else None

    # Извлекаем и удаляем веб-сайт из строки
    if website:
        contact_info = contact_info.replace(website, '')



    # Ищем телефоны
    # Ищем телефоны в формате (123) 456-7890 или 123-456-7890
    phones = re.findall(r'\(\d{3}\)\s?\d{3}[- ]?\d{4}|\d{3}-\d{3}-\d{4}|\d{3} \d{3}-\d{4}', contact_info)

    # Удаляем телефоны из строки, чтобы оставить только адрес
    for phone in phones:
        contact_info = contact_info.replace(phone, '')

    address = contact_info.strip()

    # Возвращаем адрес, строку с телефонами, веб-сайт и электронную почту
    return address, ', '.join(phones), website, email
def pars():
    folder = os.path.join(temp_path, '*.html')

    files_html = glob.glob(folder)
    # Задаем имя выходного файла
    # Задаем имя выходного файла
    # Задаем имя выходного файла
    output_filename = 'company_info.csv'

    # Проверяем, существует ли файл, и определяем, нужно ли записывать заголовки
    file_exists = os.path.isfile(output_filename)

    with open(output_filename, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Если файл не существует, мы пишем заголовки
        writer.writerow(
                ["Company Name", "Incorporation #", "Licence #", "Licence Type", "Status", "Expiry Date", "Closed Date",
                 "Person responsible for the company", "Contact Information"])

        for item in files_html:
            with open(item, encoding="utf-8") as file:
                src = file.read()

            soup = BeautifulSoup(src, 'lxml')

            # Функция для извлечения текста или возврата None, если элемент не найден
            def get_text_or_none(search_query):
                found = soup.find(string=search_query)
                return found.find_next().get_text(strip=True) if found and found.find_next() else None

            contact_info_raw = get_text_or_none("Contact Information:")
            address, phones, website, email = parse_contact_info(contact_info_raw)

            company_info = {
                "Company Name": soup.strong.text.strip() if soup.strong else None,
                "Incorporation #": get_text_or_none("Incorporation #:"),
                "Licence #": get_text_or_none("Licence #:"),
                "Licence Type": get_text_or_none("Licence Type:"),
                "Status": get_text_or_none("Status:"),
                "Expiry Date": get_text_or_none("Expiry Date:"),
                "Closed Date": get_text_or_none("Closed Date:"),
                "Person responsible for the company": get_text_or_none("Person responsible for the company:"),
                "Address": address,
                "Phone Numbers": phones,
                "Website": website,
                "Email": email
            }

            # Записываем данные компании
            writer.writerow(company_info.values())





if __name__ == '__main__':
    # delete_old_data()
    # parsing()
    # get_all_html()
    pars()

