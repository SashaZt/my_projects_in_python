import json
from pathlib import Path

import pandas as pd
import requests

current_directory = Path.cwd()
json_directory = current_directory / "json"
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
json_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
timeout = 30


def get_html():
    cookies = {
        "Suite.Web.SecurityProvider.Customer_PRD": "f7ab3be9-f564-43f9-9030-46732cafae0f",
        "__RequestVerificationToken_L01vZHVsZS9UZW5kZXJz0": "AjdFmb8GTgelmLNCbp3e8BjvQDntsPW_pFsQMpIXuOVDQvNgclSei0P_92M9rPLfSBAQrW_kauV-vlrOfbEHWh27gC81",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        # 'cookie': 'Suite.Web.SecurityProvider.Customer_PRD=f7ab3be9-f564-43f9-9030-46732cafae0f; __RequestVerificationToken_L01vZHVsZS9UZW5kZXJz0=AjdFmb8GTgelmLNCbp3e8BjvQDntsPW_pFsQMpIXuOVDQvNgclSei0P_92M9rPLfSBAQrW_kauV-vlrOfbEHWh27gC81',
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    }

    response = requests.get(
        "https://richmond.bidsandtenders.ca/Module/Tenders/en/Tender/Detail/25f9d175-0e16-4845-a081-e1fedd8bba0d",
        cookies=cookies,
        headers=headers,
        timeout=timeout,
    )
    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba_0.html", "w", encoding="utf-8") as file:
            file.write(response.text)


def get_json():

    headers = {
        "Accept": "*/*",
        "Accept-Language": "ru,en;q=0.9,uk;q=0.8",
        "Connection": "keep-alive",
        "DNT": "1",
        "Referer": "https://bidsandtenders.ic9.esolg.ca/modules/bidsandtenders/index.aspx",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    for page in range(1, 397):
        params = {
            "pageNum": page,
            "pageSize": "200",
            "statusId": "6",
            "organizationId": "0",
            "sortColumn": "UtcClosingDate",
            "sortDir": "DESC",
        }
        output_html_file = json_directory / f"page_0{page}.json"
        if output_html_file.exists():
            continue
        response = requests.get(
            "https://bidsandtenders.ic9.esolg.ca/Modules/BidsAndTenders/services/bidsSearch.ashx",
            params=params,
            headers=headers,
            timeout=timeout,
        )

        # Проверка кода ответа
        if response.status_code == 200:
            json_data = response.json()
            with open(output_html_file, "w", encoding="utf-8") as f:
                json.dump(
                    json_data, f, ensure_ascii=False, indent=4
                )  # Записываем в файл
            print(page)
        else:
            print(response.status_code)


def parisng_json_pages():
    # Обход всех JSON файлов в директории
    all_referenceNumber = []
    for json_file in json_directory.glob("*.json"):
        with json_file.open(encoding="utf-8") as file:
            # Прочитать содержимое JSON файла
            data = json.load(file)
        data_json = data["data"]["tenders"]
        for json_data in data_json:
            referenceNumber = json_data["viewUrl"]
            all_referenceNumber.append(referenceNumber)

    # Создаем DataFrame из списка с заголовком 'url'
    df = pd.DataFrame(all_referenceNumber, columns=["url"])

    # Записываем DataFrame в CSV файл
    df.to_csv(output_csv_file, index=False, encoding="utf-8")


if __name__ == "__main__":
    # get_json()
    parisng_json_pages()
