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
        "JSESSIONID": "KtifH7bKcFDar64HQTaUTMyBkreSUB0CF1SZhChC.zakupki-aogp",
    }

    headers = {
        "Accept": "application/xml, text/xml, */*; q=0.01",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "DNT": "1",
        "Faces-Request": "partial/ajax",
        "Origin": "https://zakupki.okmot.kg",
        "Referer": "https://zakupki.okmot.kg/popp/view/services/registry/procurementEntities.xhtml",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }

    for i in range(0, 15):
        table_first = str(i * 50)
        output_html_file = html_directory / f"data_{table_first}.html"

        data = {
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "table",
            "javax.faces.partial.execute": "table",
            "javax.faces.partial.render": "table",
            "javax.faces.behavior.event": "page",
            "javax.faces.partial.event": "page",
            "table_pagination": "true",
            "table_first": table_first,
            "table_rows": "50",
            "table_skipChildren": "true",
            "table_encodeFeature": "true",
            "form": "form",
            "j_idt31": "",
            "j_idt34": "",
            "ownershipType_focus": "",
            "ownershipType_input": "",
            "status_focus": "",
            "status_input": "",
            "table_rppDD": "50",
            "table_selection": "",
            "javax.faces.ViewState": "-1845043498698486249:-2085788632273726909",
        }

        if output_html_file.exists():
            logger.info(f"File {output_html_file} already exists. Skipping download.")
            continue
        response = requests.post(
            "https://zakupki.okmot.kg/popp/view/services/registry/procurementEntities.xhtml",
            cookies=cookies,
            headers=headers,
            data=data,
            verify=False,
            timeout=30,
        )

        # Проверка кода ответа
        if response.status_code == 200:

            # Сохранение HTML-страницы целиком
            with open(output_html_file, "w", encoding="utf-8") as file:
                file.write(response.text)
            logger.info(f"Successfully saved {output_html_file}")
        else:
            logger.error(f"Failed to get HTML. Status code: {response.status_code}")


if __name__ == "__main__":
    get_html()
    # process_all_xml_files(html_directory)
