import json

import requests

# import requests

# cookies = {
#     "_pk_id.1.a4f6": "a9bdd88fceaff220.1730455246.",
#     "intercom-device-id-dic5omcp": "ceefafba-c961-4d62-a06c-5fdf62d5a407",
#     "kd-e69b6f5b4cc54159": "MctJ%2B9AzpQIC8UgBt3Ub97yQ%2FTLyK7xrUqas4vHl6DyvirTjJyxMFS4q9jU02abzLkTcQ7cnLFfLyu2R9A",
#     "__cflb": "02DiuFMJyRDQ1SqAwiXo5YsPbMTGqHELt7Y7C7rdcpjfz",
#     "__cf_bm": "ZVYBNMO4W0rMOol9HhlEsLie9wv0u3YCgh1HzWTElSE-1731693666-1.0.1.1-1CUJhE_0F2wuuTmz_HTmxEd0SflzeGf6GYBrLfT8ri7zmaJ2VHb8ZCLF1jRqmcfR3osO3jwKza201CTgumljQA",
#     "_pk_ref.1.a4f6": "%5B%22%22%2C%22%22%2C1731693667%2C%22https%3A%2F%2Fahrefs.com%2F%22%5D",
#     "_pk_ses.1.a4f6": "1",
#     "cf_clearance": "AsndzK.Rb0Gi6M0K3FPNiSuX.H93au4ONFTUH5J7iYI-1731693668-1.2.1.1-z5_0nk4fTmeIudf9bk8O_x9KSXmqK4vnghQp_VcyP6nI7Vm8.Y283FmjYKEqOS8HWmKyn49USPMkbKvQTD0QFyK1c_bZHQORCTXZy7VTgRQedlPGpp6AWimMlGYa2GoOtFTI.EDO2zZ8gkg2d850bsyMXi7j4PRHmQX0_sbKtJYTp0.QHpHoQYtX_lMwGpeRG7mUt1519gGJjzHuoyDh7jHdTAEoexHruMwMvd_l9JUADtg88EtIFwpWVKisoI8E_DoSNh0s8a1xVQwyepodK2ks.rolVguqgISZXsZh2g0MDZng3QSJ8EYtqXVyZ0KFJrarBfMZAC2ybxjppwrW4sbxxDmXMAmlNWa9FGnAnXBPBCruqoklbER9hq6Uqr2EmJNFvPOy0pSrojubOc_qqQ",
#     "BSSESSID": "nrHcFUJR13xX4tTRTrpdDI7CKvbOx00KPmxbNmlp",
#     "intercom-session-dic5omcp": "cmlVRGtrNm1WWk1JTnJKWlRzUWIzajhrNE01Zkg0VSs3eEhLMnVSUlNYam5NVzh2Tkd6UGVPMWRpSDdtL2FseC0tV2FmUnFvTUhGWmxRb1l0MGtEOEVUZz09--050f7779752b79baa66b8a81f60172ce255bf198",
# }

# headers = {
#     "accept": "*/*",
#     "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#     "priority": "u=1, i",
#     "referer": "https://app.ahrefs.com/v2-site-explorer/overview?backlinksChartMode=metrics&backlinksChartPerformanceSources=domainRating%7C%7CurlRating&backlinksCompetitorsSource=%22UrlRating%22&backlinksRefdomainsSource=%22RefDomainsNew%22&bestFilter=all&brandedTrafficSource=Branded&chartGranularity=daily&chartInterval=halfYear&competitors=&countries=&country=all&dataMode=text&generalChartBrandedTraffic=Branded%7C%7CNon-Branded&generalChartMode=metrics&generalChartPerformanceSources=organicTraffic%7C%7CrefDomains&generalChartTopPosition=top11_20%7C%7Ctop21_50%7C%7Ctop3%7C%7Ctop4_10%7C%7Ctop51&generalCompetitorsSource=%22OrganicTraffic%22&generalCountriesSource=organic-traffic&highlightChanges=3m&keywordsSource=all&mode=subdomains&organicChartBrandedTraffic=Branded%7C%7CNon-Branded&organicChartMode=metrics&organicChartPerformanceSources=organicTraffic&organicChartTopPosition=top11_20%7C%7Ctop21_50%7C%7Ctop3%7C%7Ctop4_10%7C%7Ctop51&organicCompetitorsSource=%22OrganicTraffic%22&organicCountriesSource=organic-traffic&overview_tab=general&paidTrafficSources=cost%7C%7Ctraffic&target=audioboo.fm&topLevelDomainFilter=all&topOrganicKeywordsMode=normal&topOrganicPagesMode=normal&trafficType=organic&volume_type=monthly",
#     "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-origin",
#     "traceparent": "00-7ac51ac0c8e2d930029f9b50c693c820-bb2aa41a71c5106b-00",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
#     "x-client-version": "release-20241115-bk209254-bcc036846e1",
# }

# params = {
#     "input": '{"args":{"competitors":[],"best_links_filter":"showAll","backlinksFilter":null,"compareDate":["Ago","Month3"],"multiTarget":["Single",{"protocol":"both","mode":"subdomains","target":"audioboo.fm/"}],"url":"audioboo.fm/","protocol":"both","mode":"subdomains"}}',
# }


# response = requests.get(
#     "https://app.ahrefs.com/v4/seGetDomainRating",
#     params=params,
#     cookies=cookies,
#     headers=headers,
# )
# # Проверка кода ответа
# if response.status_code == 200:
#     json_data = response.json()
#     with open("seGetDomainRating.json", "w", encoding="utf-8") as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
# else:
#     print(response.status_code)

# response = requests.get(
#     "https://app.ahrefs.com/v4/seBacklinksStats",
#     params=params,
#     cookies=cookies,
#     headers=headers,
# )

# # Проверка кода ответа
# if response.status_code == 200:
#     json_data = response.json()
#     with open("seBacklinksStats.json", "w", encoding="utf-8") as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
# else:
#     print(response.status_code)


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
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
# }

# # response = requests.get(
# #     "https://allegro.pl/oferta/mlotowiertarka-sieciowa-sds-850w-r-prh-26850-13322918004",
# #     cookies=cookies,
# #     headers=headers,
# # )

headers = {
    "accept": "application/vnd.opbox-web.subtree+json",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "cache-control": "no-cache",
    "dnt": "1",
    "dpr": "1",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://allegro.pl/oferta/mlotowiertarka-sieciowa-sds-850w-r-prh-26850-13322918004",
    "sec-ch-device-memory": "8",
    "sec-ch-prefers-color-scheme": "light",
    "sec-ch-prefers-reduced-motion": "reduce",
    "sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-full-version-list": '"Chromium";v="130.0.6723.117", "Google Chrome";v="130.0.6723.117", "Not?A_Brand";v="99.0.0.0"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-viewport-height": "1031",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "viewport-width": "1136",
    "x-box-id": "LUo64bt1RQOuwIphdVaomw==sx2lrxHNQUG4Wa7QQbUK8g==4iJ4NQTRQsGK0YC-eOOwlg==",
    "x-page-rendering-status": "OK",
    "x-view-id": "f40fb504-8d73-4e50-9916-5f6c428fe700",
}
payload = {
    "api_key": "5edddbdddb89aed6e9d529c4ff127e8f",
    "url": "https://allegro.pl/oferta/mlotowiertarka-sieciowa-sds-850w-r-prh-26850-13322918004",
    "premium": True,
}
r = requests.get("https://api.scraperapi.com/", params=payload)
# Проверка кода ответа
if r.status_code == 200:
    with open("proba_0.html", "w", encoding="utf-8") as file:
        file.write(r.text)
#     json_data = r.json()
#     with open("seBacklinksStats.json", "w", encoding="utf-8") as f:
#         json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
# else:
#     print(r.status_code)


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
