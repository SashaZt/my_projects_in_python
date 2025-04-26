import asyncio
import json
import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from logger import logger
from playwright.async_api import async_playwright

current_directory = Path.cwd()
data_directory = current_directory / "data"
data_directory.mkdir(parents=True, exist_ok=True)
output_csv_file = data_directory / "output.csv"
html_directory = current_directory / "html"
html_directory.mkdir(parents=True, exist_ok=True)
output_html_file = html_directory / "mediamarkt.html"


def get_html():
    # import pandas as pd

    # # Read the CSV file
    # df = pd.read_csv("all_edrs.csv", header=None, names=["edr"])

    # # Add the URL prefix to each EDR value
    # df["edr"] = "https://clarity-project.info/edr/" + df["edr"].astype(str)

    # # Save the updated DataFrame back to CSV
    # df.to_csv("all_edrs_with_urls.csv", index=False, header=False)
    # exit()
    # import requests

    # cookies = {
    #     "__uzma": "97357116-b531-48ea-a787-9a1cdbc0d2a3",
    #     "__uzmb": "1737571173",
    #     "__uzme": "0889",
    #     "__ssds": "2",
    #     "__ssuzjsr2": "a9be0cd8e",
    #     "__uzmaj2": "f52997a6-1322-426e-8b54-c2c2eac61cf7",
    #     "__uzmbj2": "1737571182",
    #     "cid": "Qwjcj8NLrZa4OA91%23169442320",
    #     "shs": "BAQAAAZRXz2gmAAaAAVUAD2mwKzcyMjQyMjM4Mjg5MDAzLDLKGm6oHxSYJNWSOKNvMcNNo6deng**",
    #     "shui-messages-KYC_ALERT-viewsLeft": "999993",
    #     "ebaysid": "BAQAAAZRXz2gmAAaAA/oDQWuVKtBleUpyWlhraU9pSnphWFJsTG1saFppNXphV2R1WVhSMWNtVXVhMlY1Y0dGcGNpSXNJblpsY2lJNk1UTXNJbUZzWnlJNklsSlROVEV5SW4wLmV5SnBjM01pT2lKSlFVWlRUMEZKUkVWT1ZDSXNJbk4xWWlJNklqUm5aWGszYjNwdmRHVnRJaXdpWlhod0lqb3hOelF4T0RZMk9ETTJMQ0p1WW1ZaU9qRTNOREU0TmpVNU16WXNJbWxoZENJNk1UYzBNVGcyTlRrek5pd2lhblJwSWpvaU16azNaams1WXpFdE5HTTRZaTAwWWpKaExUa3daakV0TVRNelpHSTFNak0wWlRKbUlpd2ljMlZ6YzJsdmJsUnZhMlZ1VW1WbVpYSmxibU5sSWpvaWRsNHhMakVqYVY0eEkzQmVNeU55WGpFalpsNHdJMGxlTXlOMFhsVnNOSGhOUmpneFQydEdRMUZVVWtKTmFrSkNVbFJOZUU1RVJrZFNSVmt4VDBSb1ExSnFhekpSYTFKRFRWUnJNVkpVVVhsWWVrWm1UVk5PUmxocVNUSk5RVDA5SWl3aWMyVnpjMmx2Ymtsa0lqb2lPR0ZrTVdZeVlXUXhPVEl3WVdFM01qZzRZelprTnpnMlptWmpaV1UzT1RZaWZRLlB6WWtiNGJZWndOalJMbW81TXprVFBLWUNER1A0UllmSmE3a3BackFyUHhxX0h5TWpjUGtsWmFaZlExVjlEc3RjRUJEVTZPbUFTRzMwcTZoMVpDa3U0SEZOaTVNLU1OSTdhYmxtMkRBdDdnRGZ1VW5BMy1PckVEaUFqLTZmeTRXRjV3N1Q3eHNmbTZQYUJCUWFFTXRZZmRuYk5iZ1VnTk0yYTJ6OHpWNm05VjF0cURXeGY2QkpHX3paOTJaMnRsYl9NWS1ZMkZjVHZhdjI4Wk4zUTRmeGRWUDBRbUloUEdHZS1fMy1GVGNBM1JtUlFUQ3ByV09yNjFJS3c3cFplaFNGQksxODRTTXdjYWFqbWpvanBJZ0VQUjE0dGFCclFUeTlHdkRXblp2YU1RZW45cXN2ZFNTTHUwNUlwREdtdjE4ZFZUbVZtRENJRzBMUG5NdUNHbVdrd8QyyucYciLIbBojCo8LK3++Sy8x",
    #     "__uzmlj2": "G9FAAxnDuMKptEcAzxYkJIGvwaFLJ25rRkt6/3IP/jM=",
    #     "cpt": "%5Ecpt_prvd%3Dhcaptcha%5E",
    #     "__deba": "Wed3akqZJHwtM1z8M732L6ii3bqHZuzpiBZB3tGbaQbTPrlh8SVw389_7KVXBGqwXR8UW1J2_XMwSXzXGqPFGBpfL_bTa09RToxbD82BSPFB4sx0wK9nLHnUrJtlsixT0HRcCVsfcKIPRCZzSv4Rgw==",
    #     "__uzmcj2": "541718282825",
    #     "__uzmdj2": "1745310345",
    #     "__uzmfj2": "7f600038e61fac-f753-483f-8618-80f320552cd617375711825237739162974-e2ffbe8e527097c082",
    #     "ds1": "ats/1745310956857",
    #     "ns1": "BAQAAAZZay1gcAAaAAKUADGnoiG0xMzQ0MDY3NjMvMDvpPZJlkVUgx4l3N2CqNEQAeekN5Q**",
    #     "ak_bmsc": "0D27BDCF56202C71300D2ACDC87B7224~000000000000000000000000000000~YAAQbEx1aAC3RSSWAQAAwiQ4YhtBuDUKZpDl/p96xpBT4Sy87BKiBry7HXH6pGBF7PmkXp7+AaPs0+Xr7mM6PDBXpiCEPbzK/Yb0y3Ts57FRSu6yRfw44FqKOtjQ0VqRLxNc+5ZchDZUZhq8hzW716eB9/2Db8laIzH68Lh50r8lNhaCS3tNsOLNvIUVioHzpr3LjVJeoV3kU/ikm+WOCSqQBHjpcMYI8CGhTFsJ9GWBNmPTcT1iBTPBJNdvyNlNopnzZIPIR5H1WUvffT2B/n+7Rekg+6nHdbzXYKDxMgsKdoIf2aRtpjBW75l8PuFB4fDRgTMX7aDwjZ8F7VzuG6Waja3ZiKY8rtj0zFlTI6XwAK+89g4EhiPX285pwj6b+7UMq1rW2Wc=",
    #     "s": "CgADuAEpoChQ8MTQGaHR0cHM6Ly93d3cuZWJheS5jb20vYi9DYXItVHJ1Y2stRUNVcy1Db21wdXRlci1Nb2R1bGVzLzMzNTk2L2JuXzU4NDMxNAcA+AAgaAoUGDVjYTNjMzVlMTk2MGFkNTk4OGQyMWFlNGZmN2Y3NGIwiLN+rA**",
    #     "ebay": "%5Ejs%3D1%5EsfLMD%3D0%5Esin%3Din%5Esbf%3D%2300000004%5E",
    #     "__uzmc": "1089531333920",
    #     "__uzmd": "1745404604",
    #     "__uzmf": "7f600038e61fac-f753-483f-8618-80f320552cd617375711736317833430498-055a2ce001a2b54c313",
    #     "bm_sv": "E8E1AA3AEECFBDC1EAAEF1BD88A13E36~YAAQF0x1aO972j6WAQAAaP1hYhvY8Oz2QBw30kmLk65otw5Beae40X8mHaCJTdUmgn6TPG0kKlMhIQHxX9S5wwy3vWW20IHg/fNJM6EvZkDadKF6I5hMsCqDAPqXr59mQqWPPPkY74oS8Yp7VCU8GBlKNCx0MKkjsIOxc3d/tcwSTY/A8tLekeyg7V+DO4m3ZvZybmG80Jw2Wg7vSup6LmQNt6dAUfyqg1P8Lry0mMD+d6d2njMOKvFD8v0A6NY=~1",
    #     "dp1": "bu1p/dGVzdHVzZXJfcmVzdGVxMQ**6bcb3f25^kms/in6bcb3f25^pbf/%230000e400e0000000800000000069ea0ba5^u1f/Bohdan6bcb3f25^bl/DEen-US6bcb3f25^",
    #     "nonsession": "CgADKACBryz8lNWNhM2MzNWUxOTYwYWQ1OTg4ZDIxYWU0ZmY3Zjc0YjAAywABaAjfLTIAanfM",
    #     "totp": "1745410087830.H6swJ5A968LLtwauX/XcJIFKXY0xBYpHsPHhmTRA589lDRLvr7M3FEjxVpq9zMU/9e0rpcsMcG6bfNLRB+/rlQ==.rT765YSD8240_-ElUr6mQTVlLWGQPBQxu6oJx1gJKDg",
    # }

    # headers = {
    #     "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    #     "accept-language": "ru,en;q=0.9,uk;q=0.8",
    #     "cache-control": "no-cache",
    #     "dnt": "1",
    #     "pragma": "no-cache",
    #     "priority": "u=0, i",
    #     "referer": "https://www.ebay.com/b/Car-Truck-ECUs-Computer-Modules/33596/bn_584314",
    #     "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    #     "sec-ch-ua-full-version": '"135.0.7049.96"',
    #     "sec-ch-ua-mobile": "?0",
    #     "sec-ch-ua-model": '""',
    #     "sec-ch-ua-platform": '"Windows"',
    #     "sec-ch-ua-platform-version": '"19.0.0"',
    #     "sec-fetch-dest": "document",
    #     "sec-fetch-mode": "navigate",
    #     "sec-fetch-site": "cross-site",
    #     "sec-fetch-user": "?1",
    #     "upgrade-insecure-requests": "1",
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    # }

    # response = requests.get(
    #     "https://www.ebay.com/b/Car-Truck-ECUs-Computer-Modules/33596/bn_584314",
    #     cookies=cookies,
    #     headers=headers,
    #     timeout=10,
    # )

    # # Проверка кода ответа
    # if response.status_code == 200:

    #     # Сохранение HTML-страницы целиком
    #     with open(output_html_file, "w", encoding="utf-8") as file:
    #         file.write(response.text)
    #     logger.info(f"Successfully saved {output_html_file}")
    # else:
    #     logger.error(f"Failed to get HTML. Status code: {response.status_code}")
    # # ПАГИНАЦИЯ ebay
    # import pandas as pd
    # import requests
    # from bs4 import BeautifulSoup
    # import time

    # # Заголовки из curl-запроса
    # headers = {
    #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    #     'accept-language': 'ru,en;q=0.9,uk;q=0.8',
    #     'dnt': '1',
    #     'priority': 'u=0, i',
    #     'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    #     'sec-ch-ua-full-version': '"135.0.7049.96"',
    #     'sec-ch-ua-mobile': '?0',
    #     'sec-ch-ua-model': '""',
    #     'sec-ch-ua-platform': '"Windows"',
    #     'sec-ch-ua-platform-version': '"19.0.0"',
    #     'sec-fetch-dest': 'document',
    #     'sec-fetch-mode': 'navigate',
    #     'sec-fetch-site': 'same-origin',
    #     'sec-fetch-user': '?1',
    #     'upgrade-insecure-requests': '1',
    #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
    # }

    # # Куки из curl-запроса (упрощённые, возможно, потребуется их обновить)
    # cookies = {
    #     '__uzma': '97357116-b531-48ea-a787-9a1cdbc0d2a3',
    #     '__uzmb': '1737571173',
    #     '__uzme': '0889',
    #     '__ssds': '2',
    #     '__ssuzjsr2': 'a9be0cd8e',
    #     '__uzmaj2': 'f52997a6-1322-426e-8b54-c2c2eac61cf7',
    #     '__uzmbj2': '1737571182',
    # }

    # # Базовый URL
    # base_url = 'https://www.ebay.com/b/Car-Truck-Additional-ABS-Parts/33560/bn_583684?Items%2520Included=ABS%2520Accumulator&mag=1&rt=nc'

    # # Список для хранения всех href
    # all_hrefs = []

    # def scrape_page(url):
    #     try:
    #         response = requests.get(url, headers=headers, cookies=cookies)
    #         response.raise_for_status()
    #         soup = BeautifulSoup(response.text, 'html.parser')

    #         # Находим все ссылки на товары
    #         items = soup.select('li.brwrvr__item-card.brwrvr__item-card--list a.bsig__title__wrapper')
    #         hrefs = [item['href'] for item in items if 'href' in item.attrs]

    #         # Добавляем href в общий список
    #         all_hrefs.extend(hrefs)

    #         # Проверяем наличие следующей страницы
    #         next_button = soup.select_one('a.pagination__next')
    #         if next_button and 'href' in next_button.attrs and not soup.select_one('button.pagination__next[aria-disabled="true"]'):
    #             return next_button['href']
    #         return None
    #     except Exception as e:
    #         print(f"Ошибка при обработке {url}: {str(e)}")
    #         return None

    # # Начинаем с первой страницы
    # current_url = base_url
    # page_count = 1

    # while current_url:
    #     print(f"Обработка страницы {page_count}...")
    #     next_url = scrape_page(current_url)
    #     current_url = next_url
    #     page_count += 1
    #     time.sleep(2)  # Пауза, чтобы не перегружать сервер

    # # Сохраняем в CSV с помощью pandas
    # df = pd.DataFrame(all_hrefs, columns=['href'])
    # df.to_csv('all_urls.csv', index=False)

    # print(f"Собрано {len(all_hrefs)} ссылок и сохранено в all_urls.csv")
    # Скачивание каждого HTML файла из CSV
    import re
    import time

    import pandas as pd
    import requests

    # Заголовки из curl-запроса
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en;q=0.9,uk;q=0.8",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
        "sec-ch-ua-full-version": '"135.0.7049.96"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    }

    # Куки из curl-запроса
    cookies = {
        "__uzma": "97357116-b531-48ea-a787-9a1cdbc0d2a3",
        "__uzmb": "1737571173",
        "__uzme": "0889",
        "__ssds": "2",
        "__ssuzjsr2": "a9be0cd8e",
        "__uzmaj2": "f52997a6-1322-426e-8b54-c2c2eac61cf7",
        "__uzmbj2": "1737571182",
        "cid": "Qwjcj8NLrZa4OA91%23169442320",
        "shs": "BAQAAAZRXz2gmAAaAAVUAD2mwKzcyMjQyMjM4Mjg5MDAzLDLKGm6oHxSYJNWSOKNvMcNNo6deng**",
        "shui-messages-KYC_ALERT-viewsLeft": "999993",
        "ebaysid": "BAQAAAZRXz2gmAAaAA/oDQWuVKtBleUpyWlhraU9pSnphWFJsTG1saFppNXphV2R1WVhSMWNtVXVhMlY1Y0dGcGNpSXNJblpsY2lJNk1UTXNJbUZzWnlJNklsSlROVEV5SW4wLmV5SnBjM01pT2lKSlFVWlRUMEZKUkVWT1ZDSXNJbk4xWWlJNklqUm5aWGszYjNwdmRHVnRJaXdpWlhod0lqb3hOelF4T0RZMk9ETTJMQ0p1WW1ZaU9qRTNOREU0TmpVNU16WXNJbWxoZENJNk1UYzBNVGcyTlRrek5pd2lhblJwSWpvaU16azNaams1WXpFdE5HTTRZaTAwWWpKaExUa3daakV0TVRNelpHSTFNak0wWlRKbUlpd2ljMlZ6YzJsdmJsUnZhMlZ1VW1WbVpYSmxibU5sSWpvaWRsNHhMakVqYVY0eEkzQmVNeU55WGpFalpsNHdJMGxlTXlOMFhsVnNOSGhOUmpneFQydEdRMUZVVWtKTmFrSkNVbFJOZUU1RVJrZFNSVmt4VDBSb1ExSnFhekpSYTFKRFRWUnJNVkpVVVhsWWVrWm1UVk5PUmxocVNUSk5RVDA5SWl3aWMyVnpjMmx2Ymtsa0lqb2lPR0ZrTVdZeVlXUXhPVEl3WVdFM01qZzRZelprTnpnMlptWmpaV1UzT1RZaWZRLlB6WWtiNGJZWndOalJMbW81TXprVFBLWUNER1A0UllmSmE3a3BackFyUHhxX0h5TWpjUGtsWmFaZlExVjlEc3RjRUJEVTZPbUFTRzMwcTZoMVpDa3U0SEZOaTVNLU1OSTdhYmxtMkRBdDdnRGZ1VW5BMy1PckVEaUFqLTZmeTRXRjV3N1Q3eHNmbTZQYUJCUWFFTXRZZmRuYk5iZ1VnTk0yYTJ6OHpWNm05VjF0cURXeGY2QkpHX3paOTJaMnRsYl9NWS1ZMkFjVHZhdjI4Wk4zUTRmeGRWUDBRbUloUEdHZS1fMy1GVGNBM1JtUlFUQ3ByV09yNjFJS3c3cFplaFNGQksxODRTTXdjYWFqbWpvanBJZ0VQUjE0dGFCclFUeTlHdkRXblp2YU1RZW45cXN2ZFNTTHUwNUlwREdtdjE4ZFZUbVZtRENJRzBMUG5NdUNHbVdrd8QyyucYciLIbBojCo8LK3++Sy8x",
        "__uzmlj2": "G9FAAxnDuMKptEcAzxYkJIGvwaFLJ25rRkt6/3IP/jM=",
        "cpt": "%5Ecpt_prvd%3Dhcaptcha%5E",
        "__deba": "Wed3akqZJHwtM1z8M732L6ii3bqHZuzpiBZB3tGbaQbTPrlh8SVw389_7KVXBGqwXR8UW1J2_XMwSXzXGqPFGBpfL_bTa09RToxbD82BSPFB4sx0wK9nLHnUrJtlsixT0HRcCVsfcKIPRCZzSv4Rgw==",
        "__uzmcj2": "541718282825",
        "__uzmdj2": "1745310345",
        "__uzmfj2": "7f600038e61fac-f753-483f-8618-80f320552cd617375711825237739162974-e2ffbe8e527097c082",
        "ds1": "ats/1745310956857",
        "ns1": "BAQAAAZZay1gcAAaAAKUADGnoiG0xMzQ0MDY3NjMvMDvpPZJlkVUgx4l3N2CqNEQAeekN5Q**",
        "s": "CgAD4ACBoC2jPNWNhM2MzNWUxOTYwYWQ1OTg4ZDIxYWU0ZmY3Zjc0YjBnFkGC",
        "ak_bmsc": "C2ECD7D77F71821EE513B7B3B2480630~000000000000000000000000000000~YAAQBUx1aAAKEUuWAQAAESyGaRuW9aZ0ekXKkZzsI0kyGf0qouioE7XHR+OXUAPSznIfHKImsFIMTBd1xIIGTho9s7UgT7KXQygQKmt6oHMjS3pL/FXkRYlr/5qxj5EJt/CM+OcIPGzOAeIz1BXiGPHNcFZ6XGQUwqYWxnagmoJh0bBIa4TKOycl13Y/dVv6DBCJlir3eHy7QQ+8Jo69/OA0OxJalZM7spn8e6pULNEe8Gre4sgu4n3e+/+KgLpEnhyfUQCx9iidyooUaFtpa0ERpQ+x4f4UF6wDVNztzEDUr64Foj36k6m6sKnRnfz3h5AYThYMhrpiWz4emz8h+S9cfMEbahTLbtU+A48vbBotjWRN1ecJ/YhsaODxD+06Qw/Ppy2ivJo=",
        "ebay": "%5Ejs%3D1%5EsfLMD%3D0%5Esin%3Din%5Esbf%3D%2300000004%5E",
        "__uzmc": "2378932286496",
        "__uzmd": "1745530440",
        "__uzmf": "7f600038e61fac-f753-483f-8618-80f320552cd617375711736317959267058-150c914f21eedb01322",
        "totp": "1745530442106.iKVpBvoQ4A9rdCj5AxmsfGvdDoUrnJ5aeWFfjbtTpUSYsoJQpHWP+cj1En6KNPh8xOWRTXWVSdbYGvdqABqRqA==.rT765YSD8240_-ElUr6mQTVlLWGQPBQxu6oJx1gJKDg",
        "dp1": "bu1p/dGVzdHVzZXJfcmVzdGVxMQ**6bcd154b^kms/in6bcd154b^pbf/%230000e400e0000000800000000069ebe1cb^u1f/Bohdan6bcd154b^bl/DEen-US6bcd154b^",
        "nonsession": "CgADKACBrzRVLNWNhM2MzNWUxOTYwYWQ1OTg4ZDIxYWU0ZmY3Zjc0YjAAywABaAq1UzQMPWZF",
        "bm_sv": "4412198FB9F945B4A1004A4BC7D99614~YAAQFkx1aIUHxyOWAQAAete4aRuU5vduaJOn4pgjq6EVDHga/DIIqDYbJ7gNTlr+NaByhQco0ZV3ZhO5oZDWMV6jpT7D5uoukWumggLYbu+8RCXeVYVvHjaoNLiBNG/WxbQZAG5sijqhc9Ap9T5/GmoqVNIpSe2bQNnhHWyZBUlkXPYsikwka2eNCt1ux7nG1B8wMY4/gOlEquX3YvTY4bCOg+VDpsLkJa4o0pduncsGr+8X/kWXxSgZRr2wgIs=~1",
    }

    def extract_ids(url):
        # Извлекаем product_id и iid из URL
        product_id = re.search(r"/p/(\d+)", url)
        iid = re.search(r"iid=(\d+)", url)
        if product_id and iid:
            return product_id.group(1), iid.group(1)
        return None, None

    # Читаем CSV-файл
    try:
        df = pd.read_csv("all_urls.csv")
    except FileNotFoundError:
        print("Файл all_urls.csv не найден!")
        exit(1)

    # Проходим по каждой ссылке
    for url in df["href"]:
        product_id, iid = extract_ids(url)
        if not product_id or not iid:
            print(f"Не удалось извлечь product_id или iid из {url}")
            continue

        filename = f"{product_id}_{iid}.html"
        print(f"Загружаем {url} в {filename}...")

        try:
            # Выполняем запрос
            response = requests.get(url, headers=headers, cookies=cookies)
            response.raise_for_status()

            # Сохраняем HTML в файл
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"Сохранено в {filename}")
        except Exception as e:
            print(f"Ошибка при загрузке {url}: {str(e)}")

        time.sleep(2)  # Пауза, чтобы не перегружать сервер

    print("Загрузка завершена!")


def remove_at_type(data):
    """Рекурсивно удаляет ключи '@type' из словаря."""
    if isinstance(data, dict):
        # Создаем новый словарь без '@type'
        new_data = {k: remove_at_type(v) for k, v in data.items() if k != "@type"}
        return new_data
    elif isinstance(data, list):
        return [remove_at_type(item) for item in data]
    return data


# Функция для извлечения названия предприятия
def parse_company_name(soup):
    company_name_tag = soup.find(
        "p", class_="modal-title display-inline-block farmer-modal-name ng-binding"
    )
    if company_name_tag:
        return company_name_tag.text.strip()
    return None


# 1. Парсинг телефонных номеров
def parse_phone_numbers(soup):
    phone_data = []
    phone_rows = soup.find_all("tr", class_="beige-hover ng-scope ng-isolate-scope")

    for row in phone_rows:
        phone_dict = {}

        # Извлекаем номер телефона
        phone_link = row.find("a", class_="same-phone-width")
        if phone_link:
            phone_dict["phone_number"] = re.sub(
                r"\s+", " ", phone_link.get("data-content", "").strip()
            )

        # Извлекаем позицию
        position = row.find("span", class_="position-title")
        phone_dict["position"] = position.text.strip() if position else None

        # Извлекаем ФИО
        full_name = row.find("span", class_="phone-comment")
        phone_dict["full_name"] = (
            re.sub(r"\s+", " ", full_name.text.strip()) if full_name else None
        )

        phone_data.append(phone_dict)

    return phone_data


# 2. Парсинг email-таблицы
def parse_emails(soup):
    email_data = []
    email_rows = soup.find_all(
        "tr",
        class_="beige-hover ng-scope",
        attrs={"ng-repeat": "contact in contacts | filter: { name:'email' }"},
    )

    for row in email_rows:
        email_dict = {}

        # Извлекаем email
        email = row.find("span", class_="ng-binding")
        email_dict["email"] = email.text.strip() if email else None

        email_data.append(email_dict)

    return email_data


# 3. Парсинг дополнительной информации
def parse_additional_info(soup):
    info_dict = {}
    org_info = soup.find("div", class_="org-info-parent")

    if org_info:
        # Извлекаем директора
        director_div = org_info.find("div", {"ng-if": "org.director"})
        if director_div:
            director = director_div.find("div", class_="ng-binding")
            info_dict["director"] = director.text.strip() if director else None

        # Извлекаем ЭДРПОУ
        edrpou_div = org_info.find("div", {"ng-if": "org.erdpou"})
        if edrpou_div:
            edrpou = edrpou_div.find("div", class_="ng-binding")
            info_dict["edrpou"] = edrpou.text.strip() if edrpou else None

        # Извлекаем адрес
        address_div = org_info.find("div", {"ng-if": "org.address_label"})
        if address_div:
            address = address_div.find("div", class_="ng-binding")
            info_dict["address"] = address.text.strip() if address else None

        # Извлекаем КВЭД
        kved_div = org_info.find("div", {"ng-if": "org.description"})
        if kved_div:
            kved = kved_div.find("div", class_="ng-binding")
            info_dict["kved"] = kved.text.strip() if kved else None

    return info_dict


# Функция для разделения ФИО на части
def split_full_name(full_name):
    if not full_name:
        return None, None, None
    parts = full_name.split()
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return parts[0], parts[1], None
    elif len(parts) == 1:
        return parts[0], None, None
    return None, None, None


# Функция для извлечения области, района и города/села из адреса
def parse_address(address):
    if not address:
        return None, None, None

    parts = address.split(",")
    if len(parts) < 3:
        return None, None, None

    # Область обычно после "Україна"
    region = None
    district = None
    locality = None

    for part in parts:
        part = part.strip()
        if "обл." in part:
            region = part
        elif "р-н" in part:
            district = part
        elif "село" in part or "місто" in part or "селище" in part:
            locality = part

    return region, district, locality


def scrap_html():

    # Список для хранения данных
    data = []
    # Множество для хранения всех уникальных ключей характеристик
    spec_keys = set()

    # Проходим по всем HTML-файлам в папке
    for html_file in html_directory.glob("*.html"):
        with html_file.open(encoding="utf-8") as file:
            content = file.read()

            try:
                soup = BeautifulSoup(content, "lxml")

                # Инициализируем словарь для данных
                product_data = {"filename": html_file.name}

                # 1. Извлекаем URL из <meta property="og:url">
                url_meta = soup.find("meta", {"property": "og:url"})
                product_data["url"] = url_meta.get("content", "") if url_meta else ""

                title_tag = soup.find("div", {"data-testid": "x-item-title"})
                product_data["title"] = (
                    title_tag.find("span").get_text(strip=True)
                    if title_tag and title_tag.find("span")
                    else ""
                )
                # 2. Извлекаем цену из <div class="x-price-primary">
                price_div = soup.find("div", {"class": "x-price-primary"})
                if price_div:
                    price_text = price_div.find(
                        "span", {"class": "ux-textspans"}
                    ).get_text(strip=True)
                    # Извлекаем числовое значение (например, "US $1,450.00" -> "1450.00")
                    price = "".join(
                        filter(lambda x: x.isdigit() or x == ".", price_text)
                    )
                    product_data["price"] = price
                else:
                    product_data["price"] = ""

                # 3. Извлекаем изображения (до 3) из <div class="ux-image-carousel-item image-treatment image">
                images = []
                image_divs = soup.find_all(
                    "div", {"class": "ux-image-carousel-item image-treatment image"}
                )
                for div in image_divs[:3]:  # Ограничиваем до 3 изображений
                    img = div.find("img")
                    if img:
                        src = img.get("data-zoom-src")
                        if src:
                            images.append(src)
                product_data["image_1"] = images[0] if len(images) > 0 else ""
                product_data["image_2"] = images[1] if len(images) > 1 else ""
                product_data["image_3"] = images[2] if len(images) > 2 else ""

                # 4. Извлекаем состояние товара
                condition_div = soup.find("div", {"class": "vim x-item-condition"})
                if condition_div:
                    condition_text = condition_div.find(
                        "span", {"data-testid": "ux-textual-display"}
                    )
                    product_data["condition"] = (
                        condition_text.get_text(strip=True) if condition_text else ""
                    )
                else:
                    product_data["condition"] = ""

                # 5. Извлекаем информацию о возврате
                returns_div = soup.find("div", {"class": "vim x-returns-minview"})
                if returns_div:
                    returns_text = returns_div.find(
                        "div", {"class": "ux-labels-values__values-content"}
                    )
                    if returns_text:
                        # Собираем текст, включая текст внутри <a>
                        returns_content = "".join(
                            str(child) for child in returns_text.children
                        )
                        # Удаляем HTML-теги для чистого текста
                        returns_soup = BeautifulSoup(returns_content, "html.parser")
                        product_data["returns"] = returns_soup.get_text(strip=True)
                    else:
                        product_data["returns"] = ""
                else:
                    product_data["returns"] = ""

                # 6. Извлекаем характеристики
                specs_div = soup.find("div", {"class": "x-prp-product-details"})
                specifications = {}
                if specs_div:
                    spec_rows = specs_div.find_all(
                        "div", {"class": "x-prp-product-details_row"}
                    )
                    for row in spec_rows:
                        cols = row.find_all(
                            "div", {"class": "x-prp-product-details_col"}
                        )
                        for col in cols:
                            name = col.find(
                                "span", {"class": "x-prp-product-details_name"}
                            )
                            value = col.find(
                                "span", {"class": "x-prp-product-details_value"}
                            )
                            if name and value:
                                spec_name = name.get_text(strip=True)
                                spec_value = value.get_text(strip=True)
                                specifications[spec_name] = spec_value
                                spec_keys.add(spec_name)  # Добавляем ключ в множество

                # Добавляем характеристики как отдельные поля в product_data
                for key in specifications:
                    product_data[key] = specifications[key]

                # Добавляем данные в список
                data.append(product_data)

            except Exception as e:
                print(f"Ошибка при обработке {html_file.name}: {str(e)}")
                data.append(
                    {
                        "filename": html_file.name,
                        "title": "",
                        "url": "",
                        "price": "",
                        "image_1": "",
                        "image_2": "",
                        "image_3": "",
                        "condition": "",
                        "returns": "",
                    }
                )

    # Создаем DataFrame с учетом всех возможных ключей характеристик
    # Инициализируем все колонки характеристик пустыми строками
    all_columns = [
        "filename",
        "title",
        "url",
        "price",
        "image_1",
        "image_2",
        "image_3",
        "condition",
        "returns",
    ] + sorted(
        spec_keys
    )  # Добавляем все уникальные ключи характеристик

    # Преобразуем данные в DataFrame, заполняя отсутствующие колонки пустыми строками
    df_data = []
    for item in data:
        row = {col: item.get(col, "") for col in all_columns}
        df_data.append(row)

    df = pd.DataFrame(df_data, columns=all_columns)
    df.to_csv("product_details.csv", index=False, encoding="utf-8", sep=";")

    print(f"Обработано {len(data)} файлов, данные сохранены в product_details.csv")


async def main():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False
        )  # Set headless=True in production

        # Create new context with optimizations
        context = await browser.new_context(
            bypass_csp=True,
            java_script_enabled=True,
            permissions=["geolocation"],
            device_scale_factor=1.0,
            has_touch=True,
            ignore_https_errors=True,
        )

        # Disable loading of images, fonts and other media files
        await context.route(
            "**/*",
            lambda route, request: (
                route.abort()
                if request.resource_type in ["image", "media", "font", "stylesheet"]
                else route.continue_()
            ),
        )

        # Create new page
        page = await context.new_page()

        # Navigate to the website (replace with your target URL)
        await page.goto("https://www.tikleap.com/")  # Replace with your actual URL
        await asyncio.sleep(50)

        # Wait for the postal code element to appear and click it
        postal_code_button = await page.wait_for_selector(
            'span:text("Wpisz kod pocztowy")'
        )
        await postal_code_button.click()

        # Wait for the input field to appear
        postal_code_input = await page.wait_for_selector(
            'input[aria-describedby="hnf-postalcode-helper"]'
        )

        # Type the postal code
        await postal_code_input.fill("22-100")

        # Press Enter
        await postal_code_input.press("Enter")

        # Wait a moment to see the result (adjust as needed)
        await asyncio.sleep(5)

        # Close browser
        await browser.close()


if __name__ == "__main__":
    scrap_html()
    # main_realoem()
    # get_html()
    # asyncio.run(main())
