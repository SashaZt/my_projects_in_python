import requests
import json
import random
import time
import os
import csv
import glob


def get_city():
    list_cities = [
        "san francisco,ca,san-francisco--ca",
        "san diego,ca,san-diego--ca",
        "dallas,tx,dallas--tx",
        "los angeles,ca,los-angeles--ca",
        "new york,ny,new-york--ny",
        "Washington,DC,Washington--DC",
        "Atlanta,GA,Atlanta--GA",
        "Austin,TX,Austin--TX",
        "seattle,wa,seattle--wa",
        "Chicago,IL,Chicago--IL",
        "las vegas,nv,las-vegas--nv",
        "Denver,CO,Denver--CO",
        "Philadelphia,PA,Philadelphia--PA",
        "Sacramento,CA,Sacramento--CA",
        "san jose,ca,san-jose--ca",
        "Phoenix,AZ,Phoenix--AZ",
        "Miami,FL,Miami--FL",
        "Houston,TX,Houston--TX",
        "Detroit,MI,Detroit--MI",
        "Orlando,FL,Orlando--FL",
        "Boston,MA,Boston--MA",
        "Portland,OR,Portland--OR",
        "Minneapolis,MN,Minneapolis--MN",
        "Indianapolis,IN,Indianapolis--IN"

    ]
    for i in list_cities:
        pause_time = random.randint(5, 10)
        city = i.split(",")[0]
        state = i.split(",")[1]
        site = i.split(",")[2]
        cookies = {
            'WE': '40ceb2ef-b520-4133-a554-dedcd8ad92f4230622',
            'csrftoken': 'ehA5FSQw2xcZTjtGtBdWph41klvs9a8DmVZYGuYRFHFhxvNSSDTSZTbgZxA5qTXF',
            'ndbr_at': 'zysFnpA1EpyCFGNOhn4NCihfpEhSmp96x9uSEMksWFE',
            'ndbr_idt': 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImJhZmU4NTNkLTlmMTktNGJhMy05NTY4LTA1ZTg1MTk0ODFkOSIsInR5cCI6IkpXVCJ9.eyJhdF9oYXNoIjoiRGVDTk5TSW9PME9VNmVTMU1tYzI3ZyIsImF1ZCI6WyJuZXh0ZG9vci1kamFuZ28iLCJuZXh0ZG9vciJdLCJleHAiOjE2ODc1MjM2MzcsImlhdCI6MTY4NzQzNzIzNywiaXNzIjoiaHR0cHM6Ly9hdXRoLm5leHRkb29yLmNvbSIsIm5kX3ByYyI6W3siY291bnRyeSI6IlVTIiwicGlkIjoiODQzMTk4NTEiLCJ1cmwiOiJodHRwczovL3VzZXIubmV4dGRvb3IuY29tL3YxL3Byb2ZpbGUvODQzMTk4NTEifV0sInN1YiI6IjE2NTE5Nzk1LTZjOGQtNGJhMC1iMDQwLWFhN2MxYTI4YzQwMiJ9.FhyLsVX4bfvxg_32Yyf5QuXl0S0hpcyIvB0AkKzmFsLF5NEhQXetICKJhP35yfMGeCimsepJpfUcZRWbLJB3ipdtx6ZRoGJM76zUTSRyPEljRq7HTppt91UByKikSVwomcOXSMOUFyMQwkW2xtx5x_SZ1GJS4xiKnAN28kKHI-rKRqNVh2nrQcsS0gtXzl25OYr2-ZOSenp-UWMWaHFSbh2sipo7eO_3KYx8Jsu1w-7jTevte0BX7EuRObRnabmy2j50iQQLcJoN9QXO3zC8dn7IO3U7AYBUzNfZzGAMeQ0CJRa-ObowysERv2M2AeY1mPUYRXPwgFC0BSn_vK7trQ',
            'WE3P': '40ceb2ef-b520-4133-a554-dedcd8ad92f4230622',
            's': 'b6j8r0ggnti1plbv2ehw0enik63e0vhr',
            'spark-nav-onboarding-completion': 'Thu%20Jun%2022%202023%2015:34:51%20GMT+0300%20(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F%20%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C%20%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5%20%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)',
            'role-invitation-decline-notification': 'false',
            'role-resignation-notification': 'false',
            'seen-tour-in-past-day': 'true',
            'WERC': '0f78f088-41f3-4084-a2bd-506ec5959e292306221687437708',
            'OptanonConsent': 'isGpcEnabled=0&datestamp=Thu+Jun+22+2023+15%3A41%3A49+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202303.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=a90634c5-1693-420d-bda3-d83a7e98460e&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A0%2CC0004%3A0%2CC0002%3A0%2CC0007%3A0&AwaitingReconsent=false',
            'flaskTrackReferrer': '7B169A77-00B4-42B7-BF82-5F47739C56D8',
        }

        headers = {
            'authority': 'nextdoor.com',
            'accept': '*/*',
            'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
            'content-type': 'application/json',
            # 'cookie': 'WE=40ceb2ef-b520-4133-a554-dedcd8ad92f4230622; csrftoken=ehA5FSQw2xcZTjtGtBdWph41klvs9a8DmVZYGuYRFHFhxvNSSDTSZTbgZxA5qTXF; ndbr_at=zysFnpA1EpyCFGNOhn4NCihfpEhSmp96x9uSEMksWFE; ndbr_idt=eyJhbGciOiJSUzI1NiIsImtpZCI6ImJhZmU4NTNkLTlmMTktNGJhMy05NTY4LTA1ZTg1MTk0ODFkOSIsInR5cCI6IkpXVCJ9.eyJhdF9oYXNoIjoiRGVDTk5TSW9PME9VNmVTMU1tYzI3ZyIsImF1ZCI6WyJuZXh0ZG9vci1kamFuZ28iLCJuZXh0ZG9vciJdLCJleHAiOjE2ODc1MjM2MzcsImlhdCI6MTY4NzQzNzIzNywiaXNzIjoiaHR0cHM6Ly9hdXRoLm5leHRkb29yLmNvbSIsIm5kX3ByYyI6W3siY291bnRyeSI6IlVTIiwicGlkIjoiODQzMTk4NTEiLCJ1cmwiOiJodHRwczovL3VzZXIubmV4dGRvb3IuY29tL3YxL3Byb2ZpbGUvODQzMTk4NTEifV0sInN1YiI6IjE2NTE5Nzk1LTZjOGQtNGJhMC1iMDQwLWFhN2MxYTI4YzQwMiJ9.FhyLsVX4bfvxg_32Yyf5QuXl0S0hpcyIvB0AkKzmFsLF5NEhQXetICKJhP35yfMGeCimsepJpfUcZRWbLJB3ipdtx6ZRoGJM76zUTSRyPEljRq7HTppt91UByKikSVwomcOXSMOUFyMQwkW2xtx5x_SZ1GJS4xiKnAN28kKHI-rKRqNVh2nrQcsS0gtXzl25OYr2-ZOSenp-UWMWaHFSbh2sipo7eO_3KYx8Jsu1w-7jTevte0BX7EuRObRnabmy2j50iQQLcJoN9QXO3zC8dn7IO3U7AYBUzNfZzGAMeQ0CJRa-ObowysERv2M2AeY1mPUYRXPwgFC0BSn_vK7trQ; WE3P=40ceb2ef-b520-4133-a554-dedcd8ad92f4230622; s=b6j8r0ggnti1plbv2ehw0enik63e0vhr; spark-nav-onboarding-completion=Thu%20Jun%2022%202023%2015:34:51%20GMT+0300%20(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F%20%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C%20%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5%20%D0%B2%D1%80%D0%B5%D0%BC%D1%8F); role-invitation-decline-notification=false; role-resignation-notification=false; seen-tour-in-past-day=true; WERC=0f78f088-41f3-4084-a2bd-506ec5959e292306221687437708; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Jun+22+2023+15%3A41%3A49+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202303.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=a90634c5-1693-420d-bda3-d83a7e98460e&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A0%2CC0004%3A0%2CC0002%3A0%2CC0007%3A0&AwaitingReconsent=false; flaskTrackReferrer=7B169A77-00B4-42B7-BF82-5F47739C56D8',
            'dnt': '1',
            'origin': 'https://nextdoor.com',
            'referer': f'https://nextdoor.com/city/{site}/',
            'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'x-csrftoken': 'ehA5FSQw2xcZTjtGtBdWph41klvs9a8DmVZYGuYRFHFhxvNSSDTSZTbgZxA5qTXF',
            'x-nd-activity-id': '24609934-A213-4A4E-A876-C27553A8D921',
            'x-nd-activity-source': 'no-referrer',
            'x-nd-eid': '',
        }

        params = ''

        json_data = {
            'operationName': 'CityQuery',
            'variables': {
                'input': {
                    'city': city,
                    'state': state,
                    'country': 'US',
                },
            },
            'extensions': {
                'persistedQuery': {
                    'version': 1,
                    'sha256Hash': '07634cb9eddf68012bfb3c810e580eba518be9867bfeca0f32a6059d88940af0',
                },
            },
        }

        response = requests.post('https://nextdoor.com/api/gql/CityQuery', params=params, cookies=cookies,
                                 headers=headers,
                                 json=json_data)
        data = response.json()
        filename = f'{site}.json'
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                json.dump(data, f)
            print('')
            time.sleep(pause_time)
        else:
            print(f'Файл уже есть {filename}')


def parsing_url_nextdoor():
    folders_html = r"C:\scrap_tutorial-master\Nextdoor\json\list\*.json"
    files_json = glob.glob(folders_html)
    for item in files_json:
        group = item.split("\\")[-1].split("--")[0]
        with open(item, 'r', encoding="utf-8") as f:
            data_json = json.load(f)
        neighborhoodPages = data_json['data']['city']['neighborhoodPages']
        file_name = f'{group}_url_products.csv'
        with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            for page in neighborhoodPages:
                url = page['styles'][0]['attributes']['action']['url']
                slug = url.split("/")[-2].split("--")[0]
                writer.writerow([group, url, slug])


def get_json_company():
    folders_html = r"C:\scrap_tutorial-master\Nextdoor\csv\*.csv"
    files_json = glob.glob(folders_html)
    for item in files_json:
        with open(item, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                pause_time = random.randint(1, 3)
                element1, element2, element3 = row[:3]
                city = element1
                referer = element2
                slug = element3
                # folder_path = f"C:\\scrap_tutorial-master\\Nextdoor\\json\\product\\{city}"
                # if os.path.exists(folder_path):
                #     print(f'Папка уже есть {city}')
                #     continue  # Пропустить итерацию, если папка уже существует
                # os.mkdir(folder_path)
                cookies = {
                    'WE': '40ceb2ef-b520-4133-a554-dedcd8ad92f4230622',
                    'csrftoken': 'ehA5FSQw2xcZTjtGtBdWph41klvs9a8DmVZYGuYRFHFhxvNSSDTSZTbgZxA5qTXF',
                    'ndbr_at': 'zysFnpA1EpyCFGNOhn4NCihfpEhSmp96x9uSEMksWFE',
                    'ndbr_idt': 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImJhZmU4NTNkLTlmMTktNGJhMy05NTY4LTA1ZTg1MTk0ODFkOSIsInR5cCI6IkpXVCJ9.eyJhdF9oYXNoIjoiRGVDTk5TSW9PME9VNmVTMU1tYzI3ZyIsImF1ZCI6WyJuZXh0ZG9vci1kamFuZ28iLCJuZXh0ZG9vciJdLCJleHAiOjE2ODc1MjM2MzcsImlhdCI6MTY4NzQzNzIzNywiaXNzIjoiaHR0cHM6Ly9hdXRoLm5leHRkb29yLmNvbSIsIm5kX3ByYyI6W3siY291bnRyeSI6IlVTIiwicGlkIjoiODQzMTk4NTEiLCJ1cmwiOiJodHRwczovL3VzZXIubmV4dGRvb3IuY29tL3YxL3Byb2ZpbGUvODQzMTk4NTEifV0sInN1YiI6IjE2NTE5Nzk1LTZjOGQtNGJhMC1iMDQwLWFhN2MxYTI4YzQwMiJ9.FhyLsVX4bfvxg_32Yyf5QuXl0S0hpcyIvB0AkKzmFsLF5NEhQXetICKJhP35yfMGeCimsepJpfUcZRWbLJB3ipdtx6ZRoGJM76zUTSRyPEljRq7HTppt91UByKikSVwomcOXSMOUFyMQwkW2xtx5x_SZ1GJS4xiKnAN28kKHI-rKRqNVh2nrQcsS0gtXzl25OYr2-ZOSenp-UWMWaHFSbh2sipo7eO_3KYx8Jsu1w-7jTevte0BX7EuRObRnabmy2j50iQQLcJoN9QXO3zC8dn7IO3U7AYBUzNfZzGAMeQ0CJRa-ObowysERv2M2AeY1mPUYRXPwgFC0BSn_vK7trQ',
                    'WE3P': '40ceb2ef-b520-4133-a554-dedcd8ad92f4230622',
                    'spark-nav-onboarding-completion': 'Thu%20Jun%2022%202023%2015:34:51%20GMT+0300%20(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F%20%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C%20%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5%20%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)',
                    'role-invitation-decline-notification': 'false',
                    'role-resignation-notification': 'false',
                    'seen-tour-in-past-day': 'true',
                    'nd_utm_medium': 'directory_state_public_page',
                    'nd_utm_source': 'directory_state_public_page',
                    'WERC': '33e94af6-558d-4964-b49c-aaee02691e252306231687496471',
                    'OptanonConsent': 'isGpcEnabled=0&datestamp=Fri+Jun+23+2023+08%3A01%3A14+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202303.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=a90634c5-1693-420d-bda3-d83a7e98460e&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A0%2CC0004%3A0%2CC0002%3A0%2CC0007%3A0&AwaitingReconsent=false',
                    'flaskTrackReferrer': 'ACA89E37-D2BC-49F0-917C-DC7A3F50225E',
                }

                headers = {
                    'authority': 'nextdoor.com',
                    'accept': '*/*',
                    'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
                    'content-type': 'application/json',
                    # 'cookie': 'WE=40ceb2ef-b520-4133-a554-dedcd8ad92f4230622; csrftoken=ehA5FSQw2xcZTjtGtBdWph41klvs9a8DmVZYGuYRFHFhxvNSSDTSZTbgZxA5qTXF; ndbr_at=zysFnpA1EpyCFGNOhn4NCihfpEhSmp96x9uSEMksWFE; ndbr_idt=eyJhbGciOiJSUzI1NiIsImtpZCI6ImJhZmU4NTNkLTlmMTktNGJhMy05NTY4LTA1ZTg1MTk0ODFkOSIsInR5cCI6IkpXVCJ9.eyJhdF9oYXNoIjoiRGVDTk5TSW9PME9VNmVTMU1tYzI3ZyIsImF1ZCI6WyJuZXh0ZG9vci1kamFuZ28iLCJuZXh0ZG9vciJdLCJleHAiOjE2ODc1MjM2MzcsImlhdCI6MTY4NzQzNzIzNywiaXNzIjoiaHR0cHM6Ly9hdXRoLm5leHRkb29yLmNvbSIsIm5kX3ByYyI6W3siY291bnRyeSI6IlVTIiwicGlkIjoiODQzMTk4NTEiLCJ1cmwiOiJodHRwczovL3VzZXIubmV4dGRvb3IuY29tL3YxL3Byb2ZpbGUvODQzMTk4NTEifV0sInN1YiI6IjE2NTE5Nzk1LTZjOGQtNGJhMC1iMDQwLWFhN2MxYTI4YzQwMiJ9.FhyLsVX4bfvxg_32Yyf5QuXl0S0hpcyIvB0AkKzmFsLF5NEhQXetICKJhP35yfMGeCimsepJpfUcZRWbLJB3ipdtx6ZRoGJM76zUTSRyPEljRq7HTppt91UByKikSVwomcOXSMOUFyMQwkW2xtx5x_SZ1GJS4xiKnAN28kKHI-rKRqNVh2nrQcsS0gtXzl25OYr2-ZOSenp-UWMWaHFSbh2sipo7eO_3KYx8Jsu1w-7jTevte0BX7EuRObRnabmy2j50iQQLcJoN9QXO3zC8dn7IO3U7AYBUzNfZzGAMeQ0CJRa-ObowysERv2M2AeY1mPUYRXPwgFC0BSn_vK7trQ; WE3P=40ceb2ef-b520-4133-a554-dedcd8ad92f4230622; spark-nav-onboarding-completion=Thu%20Jun%2022%202023%2015:34:51%20GMT+0300%20(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F%20%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C%20%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5%20%D0%B2%D1%80%D0%B5%D0%BC%D1%8F); role-invitation-decline-notification=false; role-resignation-notification=false; seen-tour-in-past-day=true; nd_utm_medium=directory_state_public_page; nd_utm_source=directory_state_public_page; WERC=33e94af6-558d-4964-b49c-aaee02691e252306231687496471; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Jun+23+2023+08%3A01%3A14+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=202303.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=a90634c5-1693-420d-bda3-d83a7e98460e&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A0%2CC0004%3A0%2CC0002%3A0%2CC0007%3A0&AwaitingReconsent=false; flaskTrackReferrer=ACA89E37-D2BC-49F0-917C-DC7A3F50225E',
                    'dnt': '1',
                    'origin': 'https://nextdoor.com',
                    'referer': referer,
                    'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                    'x-csrftoken': 'ehA5FSQw2xcZTjtGtBdWph41klvs9a8DmVZYGuYRFHFhxvNSSDTSZTbgZxA5qTXF',
                    'x-nd-activity-id': '97562E07-4364-4C46-B8E9-390B5497F7C7',
                    'x-nd-activity-source': 'no-referrer',
                    'x-nd-eid': '',
                }

                params = ''

                json_data = {
                    'operationName': 'NeighborhoodProfile',
                    'variables': {
                        'slug': slug,
                    },
                    'extensions': {
                        'persistedQuery': {
                            'version': 1,
                            'sha256Hash': 'da2def06ea667328dea7ff0d3898634b4e3a9309ff4cb87b012e458940ddb2c2',
                        },
                    },
                }

                response = requests.post(
                    'https://nextdoor.com/api/gql/NeighborhoodProfile',
                    params=params,
                    cookies=cookies,
                    headers=headers,
                    json=json_data,
                )
                data = response.json()
                filename = f'C:\\scrap_tutorial-master\\Nextdoor\\json\\product\\{city}\\{slug}.json'
                if not os.path.exists(filename):
                    with open(filename, 'w') as f:
                        json.dump(data, f)
                    print(f'Пауза {pause_time}, Файл {filename} сохранен')
                    time.sleep(pause_time)
                else:
                    print(f'Файл уже есть {filename}')


if __name__ == '__main__':
    # get_city()
    # parsing_url_nextdoor()
    get_json_company()
