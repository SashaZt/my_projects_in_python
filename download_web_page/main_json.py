import json

import requests

cookies = {
    "cf_clearance": "1XwsbDkY3U5DU3k3c8fAUkSiyxmsBk8FAl6CpOowXRQ-1732201596-1.2.1.1-wI5.UX2XknNtzhVwlsjr0kHL6Raig6Xgis.s_elBGTHOyiQ3U.iKvIj0LnrMBAHakSoY2VU9pZU4DzbRUuaxeapbDW7HbY7ZgKsgaGEhMkh9tb8FEwXhRCl15ef3_4RvVNHxp9gJLPA04QerS5uoc.YG1IO7Gysm2ipH7ufxkyhw_v_UVnDngQWQNOSEDLA8W3a2Azsy7OtfhkOWsNG0kG6npeNF753ULwcV1Y02Fw5mn.I9nn0tLIzGwfKtldqIJpcsYVqmgAbdpdABAk8mqv2DihXCsL2ETYsLiJ.Nx25TG60601uG_pVKjrXW8zY6pZsKpncSUvgl1oYfnB8cFCIB_sJIWyDWSmKNGT6e1ZWlFecjfHXS0VsQEeO68bCydjckMs1ly5Z8e49e9XkgCw",
}

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "baggage": "sentry-environment=production,sentry-release=IpOdOdcboPTiMhyzE4TiM,sentry-transaction=%2Fcompanies%2F%5Bjurisdiction%5D%2F%5Bslug%5D,sentry-public_key=b125c7ed8d014858abb56d424189d8b3,sentry-trace_id=190b396ccfdb46629d378821c12368b6,sentry-sample_rate=1",
    # 'cookie': 'cf_clearance=1XwsbDkY3U5DU3k3c8fAUkSiyxmsBk8FAl6CpOowXRQ-1732201596-1.2.1.1-wI5.UX2XknNtzhVwlsjr0kHL6Raig6Xgis.s_elBGTHOyiQ3U.iKvIj0LnrMBAHakSoY2VU9pZU4DzbRUuaxeapbDW7HbY7ZgKsgaGEhMkh9tb8FEwXhRCl15ef3_4RvVNHxp9gJLPA04QerS5uoc.YG1IO7Gysm2ipH7ufxkyhw_v_UVnDngQWQNOSEDLA8W3a2Azsy7OtfhkOWsNG0kG6npeNF753ULwcV1Y02Fw5mn.I9nn0tLIzGwfKtldqIJpcsYVqmgAbdpdABAk8mqv2DihXCsL2ETYsLiJ.Nx25TG60601uG_pVKjrXW8zY6pZsKpncSUvgl1oYfnB8cFCIB_sJIWyDWSmKNGT6e1ZWlFecjfHXS0VsQEeO68bCydjckMs1ly5Z8e49e9XkgCw',
    "dnt": "1",
    "priority": "u=1, i",
    "referer": "https://statsnet.co/companies/kg/56782004",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sentry-trace": "190b396ccfdb46629d378821c12368b6-9b8e70a0c8331068-1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-nextjs-data": "1",
}

params = {
    "jurisdiction": "kg",
    "slug": "56782004",
}

response = requests.get(
    "https://statsnet.co/_next/data/IpOdOdcboPTiMhyzE4TiM/ru/companies/kg/56782004.json",
    cookies=cookies,
    headers=headers,
)
print(response)
json_data = response.json()
with open("kyky.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл


# cookies = {
#     "_cmuid": "2dda2bfa-7c83-4d7a-b8c2-c2b019abfc9c",
#     "gdpr_permission_given": "1",
#     "__gfp_64b": "-TURNEDOFF",
#     "OptOutOnRequest": "groups=googleAnalytics:1,googleAdvertisingProducts:1,tikTok:1,allegroAdsNetwork:1,facebook:1",
#     "_fbp": "fb.1.1730705513360.2103671403",
#     "_meta_facebookTag_sync": "1730705513360",
#     "wdctx": "v5.tzPyJlW0iUzjb7gbyMhB78YJ2AQS_PT8_-GhSa7vvAt1k8jKNya9i74l2XK42mebA92eGJSXygxmMmP-j5_Nnn52LeVwdopj41W49t646i7rHSDpFe0vw4ft772Lsl8aKDy0zRt8WYjvVw53AZnZwvKnk955XKnzSxBLmySpuw0H1G9Ag7HyEYxUC6uGH0mRqUAwae7OwXbVwmTCQL_3g34d9lGaqiBo8u6b_c-WH9DJ.RtXzRMINTbaq9hS7Zee1RQ.z5Iwepjqsyw",
#     "_meta_googleGtag_session_id": "1731863084",
#     "_meta_googleGtag_ga_session_count": "1",
#     "_meta_googleGtag_ga": "GA1.2.1486790403.1731863084",
#     "_meta_googleGtag_ga_library_loaded": "1731863330452",
#     "datadome": "nMoErhj7u4zQSTAZgGeff4BDHxWCv6oMavzFbbywRgABkp9uzdIJiS_7EGp~nzPt_bk38LP5c6Bw76h88GGio3lE8lXkF~gpEg0oGBMCvlOP6grEotEfMlTLJ_E73xez",
# }

# headers = {
#     "accept": "application/vnd.opbox-web.subtree+json",
#     "accept-language": "ru,en;q=0.9,uk;q=0.8",
#     "priority": "u=1, i",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
# }

# response = requests.get(
#     "https://allegro.pl/oferta/mlotowiertarka-sieciowa-sds-850w-r-prh-26850-13322918004",
#     cookies=cookies,
#     headers=headers,
# )
# if response.status_code == 200:
#     json_data = response.json()
#     with open("seGetDomainRating.json", "w", encoding="utf-8") as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
# else:
#     print(response.status_code)
