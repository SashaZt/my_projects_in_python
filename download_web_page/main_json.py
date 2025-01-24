import json

import requests

# cookies = {
#     "LNG": "UA",
#     "_csrf": "c1e6328d4d1a00430f580954cd699bfcb582e349d7cdb35b0fc25fc69f79504fa%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22sPIghgsE62pvjuIdspysobQGcw1EBt3j%22%3B%7D",
#     "device-referrer": "https://edrpou.ubki.ua/ua/FO12726884",
#     "device-source": "https://edrpou.ubki.ua/ua/FO14352035",
# }

# headers = {
#     "accept": "*/*",
#     "accept-language": "ru,en;q=0.9,uk;q=0.8",
#     "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
#     # 'cookie': 'LNG=UA; _csrf=c1e6328d4d1a00430f580954cd699bfcb582e349d7cdb35b0fc25fc69f79504fa%3A2%3A%7Bi%3A0%3Bs%3A5%3A%22_csrf%22%3Bi%3A1%3Bs%3A32%3A%22sPIghgsE62pvjuIdspysobQGcw1EBt3j%22%3B%7D; device-referrer=https://edrpou.ubki.ua/ua/FO12726884; device-source=https://edrpou.ubki.ua/ua/FO14352035',
#     "dnt": "1",
#     "origin": "https://edrpou.ubki.ua",
#     "priority": "u=1, i",
#     "referer": "https://edrpou.ubki.ua/ua",
#     "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
#     "sec-ch-ua-mobile": "?0",
#     "sec-ch-ua-platform": '"Windows"',
#     "sec-fetch-dest": "empty",
#     "sec-fetch-mode": "cors",
#     "sec-fetch-site": "same-origin",
#     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
#     "x-csrf-token": "V3braoDaxccc2EIecpi2D4UXNjQf0ylfFHOjHuEk80AkJqIN6L22girqMmgY7f9r9mdPR3CxeBh3BJJbo1DAKg==",
#     "x-requested-with": "XMLHttpRequest",
# }

# params = {
#     "signature": "71cdde7e23dc850751823112839bf8136a186164",
#     "scheme": "cki",
#     "reqid": "",
# }

# data = {
#     "tp": "1",
#     "page": "1",
#     "dr_common_data": "3876303462",
#     "dr_regions": "",
#     "dr_edrstate": "",
#     "dr_kvedcode": "",
#     "dr_search_just": "true",
#     "dr_search_type": "1",
# }

# response = requests.post(
#     "https://edrpou.ubki.ua/srchopenitems",
#     params=params,
#     cookies=cookies,
#     headers=headers,
#     data=data,
#     timeout=30,
# )
# json_data = response.json()
# with open("kyky.json", "w", encoding="utf-8") as f:
#     json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл

# Load the JSON data
with open("kyky.json", "r", encoding="utf-8") as file:
    data = json.load(file)
taxNumber = data["clients"][0]["taxNumber"]
print(taxNumber)
# # Extracting the relevant details
# employer_name = data["jvProfiles"]["de"]["employer"]["name"]
# contact_name = f"{data['jvProfiles']['de']['personContacts'][0]['givenName']} {data['jvProfiles']['de']['personContacts'][0]['familyName']}"
# address = data["jvProfiles"]["de"]["personContacts"][0]["communications"]["addresses"][
#     0
# ]["addressLines"][0]
# telephone = f"{data['jvProfiles']['de']['personContacts'][0]['communications']['telephoneNumbers'][0]['countryDialing']} {data['jvProfiles']['de']['personContacts'][0]['communications']['telephoneNumbers'][0]['dialNumber']}"
# email = data["jvProfiles"]["de"]["personContacts"][0]["communications"]["emails"][0][
#     "uri"
# ]

# # Constructing the dictionary
# result = {
#     "Name": employer_name,
#     "Contact": contact_name,
#     "Address": address,
#     "Telephone": telephone,
#     "Email": email,
# }

# # Print the resulting dictionary
# print(result)
