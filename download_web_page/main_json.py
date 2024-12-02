import json

import requests

cookies = {
    "cid": "270153821938440617613145839967091521916",
    "evoauth": "wb5cdecf4c4de459a88a9719d6d85a4d7",
    "timezone_offset": "120",
    "last_search_term": "",
    "user_tracker": "694b374bcae0b670fdef32ed66ce6fb6485f88ae|193.24.221.34|2024-11-30",
    "auth": "5c18ac9a4f6cb3bec14c7df31bbd6ea00f0cacbd",
    "csrf_token": "b0dc3533afe24266b9f754e83dbb165d",
}

headers = {
    "accept": "*/*",
    "accept-language": "ru,en;q=0.9,uk;q=0.8",
    "content-type": "application/json",
    # 'cookie': 'cid=270153821938440617613145839967091521916; evoauth=wb5cdecf4c4de459a88a9719d6d85a4d7; timezone_offset=120; last_search_term=; user_tracker=694b374bcae0b670fdef32ed66ce6fb6485f88ae|193.24.221.34|2024-11-30; auth=5c18ac9a4f6cb3bec14c7df31bbd6ea00f0cacbd; csrf_token=b0dc3533afe24266b9f754e83dbb165d',
    "dnt": "1",
    "origin": "https://satu.kz",
    "priority": "u=1, i",
    "referer": "https://satu.kz/c672063-internet-magazin-itmagkz.html",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "x-forwarded-proto": "https",
    "x-language": "ru",
    "x-requested-with": "XMLHttpRequest",
}

json_data = {
    "operationName": "CompanyContactsQuery",
    "variables": {
        "withGroupManagerPhones": False,
        "withWorkingHoursWarning": False,
        "getProductDetails": False,
        "company_id": 811141,
        "groupId": -1,
        "productId": -1,
    },
    "query": "query CompanyContactsQuery($company_id: Int!, $groupId: Int!, $productId: Long!, $withGroupManagerPhones: Boolean = false, $withWorkingHoursWarning: Boolean = false, $getProductDetails: Boolean = false) {\n  context {\n    context_meta\n    currentRegionId\n    recaptchaToken\n    __typename\n  }\n  company(id: $company_id) {\n    ...CompanyWorkingHoursFragment @include(if: $withWorkingHoursWarning)\n    ...CompanyRatingFragment\n    id\n    name\n    contactPerson\n    contactEmail\n    phones {\n      id\n      description\n      number\n      __typename\n    }\n    addressText\n    isChatVisible\n    mainLogoUrl(width: 100, height: 50)\n    slug\n    isOneClickOrderAllowed\n    isOrderableInCatalog\n    isPackageCPA\n    addressMapDescription\n    region {\n      id\n      __typename\n    }\n    geoCoordinates {\n      id\n      latitude\n      longtitude\n      __typename\n    }\n    branches {\n      id\n      name\n      phones\n      address {\n        region_id\n        country_id\n        city\n        zipCode\n        street\n        regionText\n        __typename\n      }\n      __typename\n    }\n    webSiteUrl\n    site {\n      id\n      isDisabled\n      __typename\n    }\n    operationType\n    __typename\n  }\n  productGroup(id: $groupId) @include(if: $withGroupManagerPhones) {\n    id\n    managerPhones {\n      id\n      number\n      __typename\n    }\n    __typename\n  }\n  product(id: $productId) @include(if: $getProductDetails) {\n    id\n    name\n    image(width: 60, height: 60)\n    price\n    signed_id\n    discountedPrice\n    priceCurrencyLocalized\n    buyButtonDisplayType\n    regions {\n      id\n      name\n      isCity\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment CompanyWorkingHoursFragment on Company {\n  id\n  isWorkingNow\n  isOrderableInCatalog\n  scheduleSettings {\n    id\n    currentDayCaption\n    __typename\n  }\n  scheduleDays {\n    id\n    name\n    dayType\n    hasBreak\n    workTimeRangeStart\n    workTimeRangeEnd\n    breakTimeRangeStart\n    breakTimeRangeEnd\n    __typename\n  }\n  __typename\n}\n\nfragment CompanyRatingFragment on Company {\n  id\n  inTopSegment\n  opinionStats {\n    id\n    opinionPositivePercent\n    opinionTotal\n    __typename\n  }\n  __typename\n}",
}

response = requests.post(
    "https://satu.kz/graphql",
    # cookies=cookies,
    headers=headers,
    json=json_data,
    timeout=30,
)
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
