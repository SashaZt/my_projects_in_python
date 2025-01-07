# import json

# import requests

# cookies = {
#     "EURES_JVSE_SESSIONID": "722A56BA727D00BB535B5D65D6F99F0E",
#     "XSRF-TOKEN": "87e95b57-aeb7-44cd-a836-9272a5b7fb16",
#     "cck1": "%7B%22cm%22%3Afalse%2C%22all1st%22%3Afalse%2C%22closed%22%3Afalse%7D",
# }

# headers = {
#     "Accept": "application/json, text/plain, */*",
#     "Accept-Language": "ru",
#     "Connection": "keep-alive",
#     # 'Cookie': 'EURES_JVSE_SESSIONID=722A56BA727D00BB535B5D65D6F99F0E; XSRF-TOKEN=87e95b57-aeb7-44cd-a836-9272a5b7fb16; cck1=%7B%22cm%22%3Afalse%2C%22all1st%22%3Afalse%2C%22closed%22%3Afalse%7D',
#     "DNT": "1",
#     "Referer": "https://europa.eu/eures/portal/jv-se/jv-details/MTIyMDYtMTI5NDk4ODEtUyAx?lang=en",
#     "Sec-Fetch-Dest": "empty",
#     "Sec-Fetch-Mode": "cors",
#     "Sec-Fetch-Site": "same-origin",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
# }

# params = {
#     "lang": "en",
# }

# response = requests.get(
#     "https://europa.eu/eures/eures-apps/searchengine/page/jv/id/MTIyMDYtMTI5NDk4ODEtUyAx",
#     params=params,
#     cookies=cookies,
#     headers=headers,
#     timeout=30,
# )
# json_data = response.json()
# with open("kyky.json", "w", encoding="utf-8") as f:
#     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
import json

# Load the JSON data
with open("kyky.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Extracting the relevant details
employer_name = data["jvProfiles"]["de"]["employer"]["name"]
contact_name = f"{data['jvProfiles']['de']['personContacts'][0]['givenName']} {data['jvProfiles']['de']['personContacts'][0]['familyName']}"
address = data["jvProfiles"]["de"]["personContacts"][0]["communications"]["addresses"][
    0
]["addressLines"][0]
telephone = f"{data['jvProfiles']['de']['personContacts'][0]['communications']['telephoneNumbers'][0]['countryDialing']} {data['jvProfiles']['de']['personContacts'][0]['communications']['telephoneNumbers'][0]['dialNumber']}"
email = data["jvProfiles"]["de"]["personContacts"][0]["communications"]["emails"][0][
    "uri"
]

# Constructing the dictionary
result = {
    "Name": employer_name,
    "Contact": contact_name,
    "Address": address,
    "Telephone": telephone,
    "Email": email,
}

# Print the resulting dictionary
print(result)

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
