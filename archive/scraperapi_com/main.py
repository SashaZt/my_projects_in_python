# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import requests
import json
from config import API_KEY

cookies = {
    '_cf_7b': '2600665610.47873.0000',
    '__cf_bm': 'olIzZd.TYKgu36CNe55Sdo2y5aSrS1mIo1k04Kyk8C0-1709674122-1.0.1.1-_7fjVJm2uDm0lNYuC30BxmmkcZJ5ETS3Pbz5Ir2mnMo_xCqgP8jvOoAb6viy20Yy4aYydz15iIoC8UaPW9OQiw.ndeSqOxxcSnXRLnWtMyE',
    'AMCVS_E5F2C8A15481C0E20A4C98BC%40AdobeOrg': '1',
    'AMCV_E5F2C8A15481C0E20A4C98BC%40AdobeOrg': '179643557%7CMCIDTS%7C19788%7CMCMID%7C87554041928093596420804521706073250235%7CMCOPTOUT-1709681322s%7CNONE%7CvVersion%7C5.5.0',
    'RecentSearches': '',
    'X-CSRF-TOKEN-COOKIE': 'CfDJ8GVtXVbq1qBPjGLPgpXml-kJgq_sgTDmbXTUgYM6kGSVnhdhGlVjo4Lnu7H2w3RiZLtVuwd57mgE2fAqCqaYTdAFFFnLmjtRPoW2Ocu7bZfwgtojpeV6BKJzR2JPr5g-P-ByLC3HiYeRoZyLyBpyBVk',
    'Basket': '',
    'OptanonAlertBoxClosed': '2024-03-05T21:45:05.825Z',
    'OptanonConsent': 'isGpcEnabled=0&datestamp=Tue+Mar+05+2024+23%3A45%3A27+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.30.0&isIABGlobal=false&hosts=&consentId=345b7345-9d1a-4ca7-929e-198e46cbd241&interactionCount=3&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=UA%3B18&AwaitingReconsent=false',
}

headers = {
    'authority': 'ee.bca-europe.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
    # 'content-length': '0',
    # 'cookie': '_cf_7b=2600665610.47873.0000; __cf_bm=olIzZd.TYKgu36CNe55Sdo2y5aSrS1mIo1k04Kyk8C0-1709674122-1.0.1.1-_7fjVJm2uDm0lNYuC30BxmmkcZJ5ETS3Pbz5Ir2mnMo_xCqgP8jvOoAb6viy20Yy4aYydz15iIoC8UaPW9OQiw.ndeSqOxxcSnXRLnWtMyE; AMCVS_E5F2C8A15481C0E20A4C98BC%40AdobeOrg=1; AMCV_E5F2C8A15481C0E20A4C98BC%40AdobeOrg=179643557%7CMCIDTS%7C19788%7CMCMID%7C87554041928093596420804521706073250235%7CMCOPTOUT-1709681322s%7CNONE%7CvVersion%7C5.5.0; RecentSearches=; X-CSRF-TOKEN-COOKIE=CfDJ8GVtXVbq1qBPjGLPgpXml-kJgq_sgTDmbXTUgYM6kGSVnhdhGlVjo4Lnu7H2w3RiZLtVuwd57mgE2fAqCqaYTdAFFFnLmjtRPoW2Ocu7bZfwgtojpeV6BKJzR2JPr5g-P-ByLC3HiYeRoZyLyBpyBVk; Basket=; OptanonAlertBoxClosed=2024-03-05T21:45:05.825Z; OptanonConsent=isGpcEnabled=0&datestamp=Tue+Mar+05+2024+23%3A45%3A27+GMT%2B0200+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.30.0&isIABGlobal=false&hosts=&consentId=345b7345-9d1a-4ca7-929e-198e46cbd241&interactionCount=3&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&geolocation=UA%3B18&AwaitingReconsent=false',
    'dnt': '1',
    'origin': 'https://ee.bca-europe.com',
    'referer': 'https://ee.bca-europe.com/buyer/facetedSearch/saleCalendar?page=1',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
}

# params = {
#     'page': '2',
# }
"""Загруска с рендором JavaScript"""
# proxies = {
#     'http': f'http://scraperapi.render=true:{API_KEY}@proxy-server.scraperapi.com:8001',
#     'https': f'http://scraperapi.render=true:{API_KEY}@proxy-server.scraperapi.com:8001',
# }

"""Обычные html"""
proxies = {
    'http': f'http://scraperapi:{API_KEY}@proxy-server.scraperapi.com:8001',
    'https': f'http://scraperapi:{API_KEY}@proxy-server.scraperapi.com:8001',
}

# proxies = {
#     'http': f'http://scraperapi.autoparse=true:{API_KEY}@proxy-server.scraperapi.com:8001',
#     'https': f'http://scraperapi.autoparse=true:{API_KEY}@proxy-server.scraperapi.com:8001',
# }
# response = requests.post(
#     'https://ee.bca-europe.com/buyer/facetedSearch/GetSaleCalendarViewModel',
#     params=params,
#     cookies=cookies,
#     headers=headers,
#     proxies=proxies,
#     verify=False)
# json_data = response.json()
# with open(f'cda_02.json', 'w', encoding='utf-8') as f:
#     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

# response = requests.get('https://www.vaurioajoneuvo.fi/', cookies=cookies, headers=headers,
#                         proxies=proxies)
#
# src = response.text
filename = f"manyvids.html"
# with open(filename, "w", encoding='utf-8') as file:
#     file.write(src)


import requests

r = requests.post(url = 'https://async.scraperapi.com/jobs', json={ 'apiKey': 'a818a4bc04f177c7ae82bb950ccf95ac', 'urls': ["https://www.vaurioajoneuvo.fi/"]  })
src = r.text
with open(filename, "w", encoding='utf-8') as file:
    file.write(src)
