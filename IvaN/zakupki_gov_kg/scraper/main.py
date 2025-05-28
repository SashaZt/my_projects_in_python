import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from config.logger import logger
from scrap import process_all_xml_files
current_directory = Path.cwd()
temp_directory = current_directory / "temp"
output_csv_file = temp_directory / "output.csv"
html_directory = temp_directory / "html"
temp_directory.mkdir(parents=True, exist_ok=True)
html_directory.mkdir(parents=True, exist_ok=True)


def get_html():
    """
    Функция для получения HTML-страниц с сайта zakupki.gov.kg
    и сохранения их в папку temp/html.
    """
    cookies = {
    'JSESSIONID': 'ijuKNdAt3BMJwSM5QFPL30sAy8mhx3YmVIgyCawu.msc01-popp01:main-popp',
}


    headers = {
    'Accept': 'application/xml, text/xml, */*; q=0.01',
    'Accept-Language': 'ru,en;q=0.9,uk;q=0.8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'DNT': '1',
    'Faces-Request': 'partial/ajax',
    'Origin': 'http://zakupki.gov.kg',
    'Referer': 'http://zakupki.gov.kg/popp/view/order/single_source_procurement.xhtml?cid=2',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
        # 'Cookie': 'JSESSIONID=ijuKNdAt3BMJwSM5QFPL30sAy8mhx3YmVIgyCawu.msc01-popp01:main-popp',
    }

    params = {
        'cid': '2',
    }

    

    
    for i in range(0, 5000):
        table_first = str(i * 50)
        output_html_file = html_directory / f"data_{table_first}.html"

        data = {
        'javax.faces.partial.ajax': 'true',
        'javax.faces.source': 'form:table',
        'javax.faces.partial.execute': 'form:table',
        'javax.faces.partial.render': 'form:table',
        'javax.faces.behavior.event': 'page',
        'javax.faces.partial.event': 'page',
        'form:table_pagination': 'true',
        'form:table_first': table_first,
        'form:table_rows': '50',
        'form:table_skipChildren': 'true',
        'form:table_encodeFeature': 'true',
        'form': 'form',
        'form:j_idt75': '',
        'form:supplier_input': '',
        'form:supplier_hinput': '',
        'form:dateFrom_input': '',
        'form:dateTo_input': '',
        'form:table_rppDD': '50',
        'form:table_selection': '',
        'javax.faces.ViewState': '3818524033408927344:-8645504847618338535',
    }



        if output_html_file.exists():
            logger.info(f"File {output_html_file} already exists. Skipping download.")
            continue
        response = requests.post(
        'http://zakupki.gov.kg/popp/view/order/single_source_procurement.xhtml',
        params=params,
        cookies=cookies,
        headers=headers,
        data=data,
        verify=False,)

        

        # Проверка кода ответа
        if response.status_code == 200:

            # Сохранение HTML-страницы целиком
            with open(output_html_file, "w", encoding="utf-8") as file:
                file.write(response.text)
            logger.info(f"Successfully saved {output_html_file}")
        else:
            logger.error(f"Failed to get HTML. Status code: {response.status_code}")

if __name__ == "__main__":
    # get_html()
    process_all_xml_files(html_directory)