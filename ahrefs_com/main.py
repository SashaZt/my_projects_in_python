import csv
import glob
import json
import os
import time
import re
from openpyxl import Workbook

import requests
from config import cookies, headers, date_parsing

current_directory = os.getcwd()
temp_directory = 'temp'
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, temp_directory)
json_path = os.path.join(temp_path, 'json')


def delete_old_data():
    # Убедитесь, что папки существуют или создайте их
    for folder in [temp_path, json_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Удалите файлы из папок list и product
    for folder in [json_path]:
        files = glob.glob(os.path.join(folder, '*'))
        for f in files:
            if os.path.isfile(f):
                os.remove(f)


def get_csv():
    csv_filename = 'site.csv'
    productid_list = []

    with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')

        for row in reader:
            productid_list.append(row)
    return productid_list


def get_requests():
    sites = get_csv()
    heandler = ['url', 'domain_rating', 'organic_traffic', 'country_00', 'traffic_00', 'country_01', 'traffic_01',
                'country_02', 'traffic_02']
    with open('output.csv', 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)
        for row in sites:
            site = row[0]
            params = {
                'input': f'{{"args":{{"competitors":[],"compareDate":["Date","{date_parsing}"],"multiTarget":["Single",'
                         f'{{"protocol":"both","mode":"subdomains","target":"{site}/"}}],"url":"{site}/","protocol":"both","mode":"subdomains"}}}}',
            }

            response_seGetMetricsByCountry = requests.get('https://app.ahrefs.com/v4/seGetMetricsByCountry',
                                                          params=params,
                                                          headers=headers,
                                                          cookies=cookies)
            response_seGetMetrics = requests.get('https://app.ahrefs.com/v4/seGetMetrics', params=params,
                                                 cookies=cookies,
                                                 headers=headers)

            response_seGetDomainRating = requests.get('https://app.ahrefs.com/v4/seGetDomainRating',
                                                      params=params, cookies=cookies,
                                                      headers=headers)

            data_json_seGetMetricsByCountry = response_seGetMetricsByCountry.json()
            data_json_seGetMetrics = response_seGetMetrics.json()
            data_json_seGetDomainRating = response_seGetDomainRating.json()
            try:
                metrics = data_json_seGetMetricsByCountry[1].get('metrics', [])
            except:
                print(f"Ошибка сайта {site}")
                continue
            if len(metrics) > 2:
                country_00 = metrics[0].get('country')
                traffic_00 = metrics[0].get('organic', {}).get('traffic', {}).get('value')
                country_01 = metrics[1].get('country')
                traffic_01 = metrics[1].get('organic', {}).get('traffic', {}).get('value')
                country_02 = metrics[2].get('country')
                traffic_02 = metrics[2].get('organic', {}).get('traffic', {}).get('value')
            else:
                country_00 = country_01 = country_02 = traffic_00 = traffic_01 = traffic_02 = None

            organic_traffic = data_json_seGetMetrics[1].get('organic', {}).get('traffic', {}).get('value')
            domainrating = data_json_seGetDomainRating[1].get('domainRating', {}).get('value')

            value = [site, domainrating, organic_traffic, country_00, traffic_00, country_01, traffic_01, country_02,
                     traffic_02]
            writer.writerow(value)
            time.sleep(1)
            print(site)


def parsing():
    folder = os.path.join(json_path, '*.json')

    files_json = glob.glob(folder)
    for item in files_json[:1]:
        with open(item, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        url = (json_data[1]['countryWithMostKeywords']['seRowsArgsValidatedInput']['url']).replace('/', '')
        country_00 = json_data[1]['metrics'][0]['country']
        traffic_00 = json_data[1]['metrics'][0]['organic']['traffic']['value']
        country_01 = json_data[1]['metrics'][1]['country']
        traffic_01 = json_data[1]['metrics'][1]['organic']['traffic']['value']
        country_02 = json_data[1]['metrics'][2]['country']
        traffic_02 = json_data[1]['metrics'][2]['organic']['traffic']['value']

        print(url)
        print(country_00, traffic_00)
        print(country_01, traffic_01)
        print(country_02, traffic_02)


"""Сохранить csv в xlsx ексель"""


def save_xslx():
    # Определите регулярное выражение для фильтрации недопустимых символов
    pattern = re.compile(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]')

    # Открываем CSV файл для чтения
    with open('output.csv', 'r', newline='', encoding='utf-8') as csvfile:
        # with open('output.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=";")
        # next(reader)  # Пропускаем первую строку с заголовками

        # Создаем новую книгу Excel и выбираем активный лист
        workbook = Workbook()
        sheet = workbook.active

        # Заполняем лист данными из CSV файла, фильтруя недопустимые символы
        for row in reader:
            filtered_row = [re.sub(pattern, '', cell) if cell else cell for cell in row]
            sheet.append(filtered_row)

        # Сохраняем книгу в файле XLSX
        workbook.save('output.xlsx')
        # workbook.save('output.xlsx')


if __name__ == '__main__':
    get_requests()
    save_xslx()
