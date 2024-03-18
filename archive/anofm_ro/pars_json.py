import glob
import csv
import json
import os

folder = os.path.join('C:\\json', '*.json')

files_html = glob.glob(folder)
heandler = ['agent_company', 'ocupatie_company', 'email_company']
with open('output.csv', 'w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter=";")
    writer.writerow(heandler)  # Записываем заголовки только один раз
    for item in files_html:
        with open(item, "r", encoding="utf-8") as file:
            data = json.load(file)
        email_company = data['detalii_lmv'][0]['EMAIL']
        ocupatie_company= data['detalii_lmv'][0]['ocupatie']
        agent_company= data['detalii_lmv'][0]['AGENT']
        values = [agent_company, ocupatie_company, email_company]
        writer.writerow(values)