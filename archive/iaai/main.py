from bs4 import BeautifulSoup
import glob
import os
import requests
import json
import random
import time
import csv
from proxi import proxies


def get_request():
    cookies = {
        'IAAITrackingCookie': '78615b68-251a-4007-a12b-386cfbfb91df',
        'visid_incap_2807936': 'tLnSenfQQ123Il24AjHzFunDjGQAAAAAQUIPAAAAAABXxfyQWTtaU8tqF3BmSet+',
        'nlbi_2807936': 'Hoa7WCcxa276QKi5xRLPjgAAAAA5TTbJsmC/VkRPCQZAf38u',
        'TimeZoneMapID': '120',
        'last_viewed_page': '%2Fsearch',
        '.AspNetCore.Antiforgery.Q7Ul_3t76s0': 'CfDJ8Kywx80n0ntMiIjqmuNevRlZMSOCednwLeAr9uwtCaV8bnIwlMJMMliAjQ8Hb9ycuzq0wIciKf4I5JybJI2FfaUXTdyd60H9PMxfRSL3dJNY3oTcFwN5pxfnHavCmpjsK64uO8CeNJpDdr0TEPMrKsw',
        'OptanonAlertBoxClosed': '2023-07-05T05:56:31.954Z',
        'LanguageCode': '',
        'ZipCode': '',
        'X-Forwarded-For_IpAddress': '146.120.185.4%2C%20198.143.55.5%3A5516',
        'BrokerPopupIPAddress': '2457385220-146.120.185.4-2457385220',
        'BrokerPopupCountryCode': 'UA',
        'incap_ses_520_2807936': '1jWRFzOcEmL7phwppWk3B1aLpWQAAAAANsrNczWgQ3Nr7ghm1f5DMg==',
        'reese84': '3:2xF5+xGvYMEb0e0OkItKDA==:NCUFx7q3fKHQ9O/gBOnsnUZvw3TF+HGYS3HUqIMiASH0OxclpVRW/i3Qim7k0p4NOkVPKlB+PwQf+McWlO00Rt/jQ6gSkOTnTD5POf492np7vawYywtT60Sw8ULFeWipmfPK5xUDG161X0qr7Nmvfhvlsa1MAQLTEtlUnHVupoAHCJM42cuzWYBzAbClBZMtJuQIW4WpsQVYT1THlF3p5VVn43NjH9Wq/hiane5Bf3e24aOv2i9feZ/j/fEBHeoc/3V7gE/WHSdZMVzkjrZCocUFM/lHtDBcZJug0aTTo0p2w46lXhra0NXYKyzGwKc04mlESH4f3DeUYfgQHXGlQfRm314i0xZr9gfRpdF0ghlY/M7GyPczCy0Gj2V8NnzHXKVtVJVfBeFrVeGlChVKeRNskcYQA3jcKNVv22TMHHR2mBRy9e1ralXiWSEqNO2jMQNX/zXlINsca3stjqJMlQ==:8CpZ5+nxtd8b3Qkf/joWAyzLrU0jgMwnwrPAEYvfLAk=',
        'nlbi_2807936_2147483392': 'A59Qaia2R2OuAvWExRLPjgAAAAA+WeNjRpCgdRvGA529ls0T',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Jul+05+2023+18%3A51%3A48+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.28.0&isIABGlobal=false&hosts=&consentId=47602eac-6f07-4c80-957d-08c366eb797d&interactionCount=2&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&AwaitingReconsent=false&geolocation=%3B',
        'URI': 'X7xtvPHYxvDplIZsSgFU5rRCKKA%252fmcSNSVxMYm0lLlM%253d',
    }

    headers = {
        'authority': 'www.iaai.com',
        'accept': '*/*',
        'accept-language': 'ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6',
        'content-type': 'application/json',
        # 'cookie': 'IAAITrackingCookie=78615b68-251a-4007-a12b-386cfbfb91df; visid_incap_2807936=tLnSenfQQ123Il24AjHzFunDjGQAAAAAQUIPAAAAAABXxfyQWTtaU8tqF3BmSet+; nlbi_2807936=Hoa7WCcxa276QKi5xRLPjgAAAAA5TTbJsmC/VkRPCQZAf38u; TimeZoneMapID=120; last_viewed_page=%2Fsearch; .AspNetCore.Antiforgery.Q7Ul_3t76s0=CfDJ8Kywx80n0ntMiIjqmuNevRlZMSOCednwLeAr9uwtCaV8bnIwlMJMMliAjQ8Hb9ycuzq0wIciKf4I5JybJI2FfaUXTdyd60H9PMxfRSL3dJNY3oTcFwN5pxfnHavCmpjsK64uO8CeNJpDdr0TEPMrKsw; OptanonAlertBoxClosed=2023-07-05T05:56:31.954Z; LanguageCode=; ZipCode=; X-Forwarded-For_IpAddress=146.120.185.4%2C%20198.143.55.5%3A5516; BrokerPopupIPAddress=2457385220-146.120.185.4-2457385220; BrokerPopupCountryCode=UA; incap_ses_520_2807936=1jWRFzOcEmL7phwppWk3B1aLpWQAAAAANsrNczWgQ3Nr7ghm1f5DMg==; reese84=3:2xF5+xGvYMEb0e0OkItKDA==:NCUFx7q3fKHQ9O/gBOnsnUZvw3TF+HGYS3HUqIMiASH0OxclpVRW/i3Qim7k0p4NOkVPKlB+PwQf+McWlO00Rt/jQ6gSkOTnTD5POf492np7vawYywtT60Sw8ULFeWipmfPK5xUDG161X0qr7Nmvfhvlsa1MAQLTEtlUnHVupoAHCJM42cuzWYBzAbClBZMtJuQIW4WpsQVYT1THlF3p5VVn43NjH9Wq/hiane5Bf3e24aOv2i9feZ/j/fEBHeoc/3V7gE/WHSdZMVzkjrZCocUFM/lHtDBcZJug0aTTo0p2w46lXhra0NXYKyzGwKc04mlESH4f3DeUYfgQHXGlQfRm314i0xZr9gfRpdF0ghlY/M7GyPczCy0Gj2V8NnzHXKVtVJVfBeFrVeGlChVKeRNskcYQA3jcKNVv22TMHHR2mBRy9e1ralXiWSEqNO2jMQNX/zXlINsca3stjqJMlQ==:8CpZ5+nxtd8b3Qkf/joWAyzLrU0jgMwnwrPAEYvfLAk=; nlbi_2807936_2147483392=A59Qaia2R2OuAvWExRLPjgAAAAA+WeNjRpCgdRvGA529ls0T; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Jul+05+2023+18%3A51%3A48+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.28.0&isIABGlobal=false&hosts=&consentId=47602eac-6f07-4c80-957d-08c366eb797d&interactionCount=2&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A1%2CC0004%3A1&AwaitingReconsent=false&geolocation=%3B; URI=X7xtvPHYxvDplIZsSgFU5rRCKKA%252fmcSNSVxMYm0lLlM%253d',
        'dnt': '1',
        'origin': 'https://www.iaai.com',
        'referer': 'https://www.iaai.com/Search?url=X7xtvPHYxvDplIZsSgFU5rRCKKA%2fmcSNSVxMYm0lLlM%3d',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    params = {
        'c': '1688572323571',
    }

    ad = 10821
    page_ad = ad // 10

    page = 0
    for i in range(1, 11):
        # for i in range(page_ad + 1):
        proxy = random.choice(proxies)
        proxy_host = proxy[0]
        proxy_port = proxy[1]
        proxy_user = proxy[2]
        proxy_pass = proxy[3]

        proxi = {
            'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
            'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
        }

        json_data = {
            'Searches': [
                {
                    'Facets': [
                        {
                            'Group': 'IsDemo',
                            'Value': 'False',
                        },
                    ],
                    'FullSearch': None,
                    'LongRanges': None,
                },
                {
                    'Facets': None,
                    'FullSearch': 'buy now',
                    'LongRanges': None,
                },
            ],
            'ZipCode': '',
            'miles': 0,
            'PageSize': 100,
            'CurrentPage': page,
            'Sort': [
                {
                    'IsGeoSort': False,
                    'SortField': 'AuctionDateTime',
                    'IsDescending': False,
                },
            ],
            'SaleStatusFilters': [
                {
                    'SaleStatus': 1,
                    'IsSelected': True,
                },
            ],
            'BidStatusFilters': [
                {
                    'BidStatus': 6,
                    'IsSelected': True,
                },
            ],
        }

        response = requests.post('https://www.iaai.com/Search', cookies=cookies, headers=headers, json=json_data,
                                 proxies=proxi, params=params)
        filename = f"c:\\DATA\\iaai\\list\\data_{page}.html"
        src = response.text
        with open(filename, "w", encoding='utf-8') as file:
            file.write(src)
        page += 1


def get_id_ad_and_url():
    folders_html = r"c:\DATA\iaai\list\*.html"
    files_html = glob.glob(folders_html)
    with open(f"url.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for i in files_html:
            with open(i, encoding="utf-8") as html_file:
                src = html_file.read()
            soup = BeautifulSoup(src, 'lxml')
            all_url = soup.find_all('h4', attrs={'class': 'heading-7 rtl-disabled'})
            for u in all_url:
                url = f'https://www.iaai.com{u.find("a").get("href")}'
                writer.writerow([url])


def get_product():

    cookies = {

        'BrokerPopupIPAddress': '2457385220-146.120.185.4-2457385220',
        'BrokerPopupCountryCode': 'UA',
        'IAAITrackingCookie': '3ca68b7f-5664-4c24-a37f-8ce1bdad0eef',
        'visid_incap_2807936': '3Xr4afWaTFqc6ix+6ceJR3q8pWQAAAAAQUIPAAAAAABCX2U0d9912umOWc2E3ky2',
        'nlbi_2807936': 'sobBPkyeth/Xgo3GxRLPjgAAAAAUr9dDmKiNlCvq1zuVAN4Q',
        'incap_ses_520_2807936': 'c6YFRI34fwIhpTcppWk3B3q8pWQAAAAAH+YqwHycVv94gp+eMWDKlQ==',
        'TimeZoneMapID': '120',
        '_gcl_au': '1.1.745602433.1688583292',
        '_ga_8J4GTR5B9Q': 'GS1.1.1688583291.1.0.1688583291.60.0.0',
        '_evga_4ff5': '{%22uuid%22:%22bf58fa0b20aed1b6%22}',
        '_sfid_4446': '{%22anonymousId%22:%22bf58fa0b20aed1b6%22%2C%22consents%22:[]}',
        '_uetsid': '6c76d9201b6511eea2dffd5acdf6d6db',
        '_uetvid': '6c76c7d01b6511ee8ec2a11cf202bd7b',
        'nlbi_2807936_2147483392': 'SakDRHmwkXEYJKeWxRLPjgAAAABQg+Q3Y5H9kcBAqkZVxfN1',
        'reese84': '3:exfDceMepIp4UaWp/ExwvA==:r4WpmRn7ZiLNJxq+dwjqiM9z40RdCWZEyLJfQ1iyyV8t2pN9sL80gJcfuyg+2E5rQCm1JEWaBhl52xF/zLRkTLE44+bmoL1BPnbCeRKzUVtUwc/JZ02eB/OOIAmVsajVGpiG+aFPyDC3CRbEawAHH6OBlAduFHVEfDqxZ7ry/6bXzs1A97cf+zyrTl9qhrJ/ze37chQeFqrR//grsOmcX4yaHDcexSKB9tCxijw+gV9K0omsIXY/sSqCZ5YUHnNp/FPFLQhmrZmbPcidoJNyRn43sw2kuash/07XW4+gMizOhdKv9gq8fgLcq/f7liFU0hlczjHA38qrgYZy1teDzyJsEjyW7rVuwSHdSDP0d9L1owtY8GN8gw4ucF/bnaIzhOcBXN8Q+HtsdBsluloTJ/0Z58lCyiJ18kO2IRudK8Tdfd/CNUdE2joKUb+IjUZU6AYfjzGz7FlRDWJ3UNcW9Q==:27MOtinN9SNptBGyU7j8Jt/1twtN/SPCiZ+AOvDcbHY=',
        'ln_or': 'eyIyMzg4ODk3IjoiZCJ9',
        '_fbp': 'fb.1.1688583292361.87537795',
        '_clck': '1xptlkx|2|fd1|0|1281',
        '_clsk': 'dkp5pg|1688583293156|1|1|v.clarity.ms/collect',
        'mdLogger': 'false',
        'kampyle_userid': '7a50-797e-3339-464d-e264-7692-45be-0552',
        'kampyleUserSession': '1688583293405',
        'kampyleUserSessionsCount': '1',
        'kampyleSessionPageCounter': '1',
        'ASP.NET_SessionId': 'xo50ztpwwwlbidqfilorzvpy',
        'BrokerPopupCountryCodeIP': '3331274501',
        'Locations_Cookie': 'Locations_Cookie=MapView',
        'OptanonAlertBoxClosed': '2023-07-05T18:55:00.745Z',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Jul+05+2023+21%3A55%3A00+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.28.0&isIABGlobal=false&hosts=&consentId=257342f0-26fd-44be-a06d-d52063ffe8db&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A0%2CC0004%3A0',
        'actualOptanonConsent': '%2CC0001%2CC0003%2C',
        '_ga': 'GA1.2.1025765507.1688583292',
        '_gid': 'GA1.2.854761563.1688583302',
        '_gat_%5Bobject%20Object%5D': '1',
    }

    headers = {
        'authority': 'www.iaai.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'X-Forwarded-For_IpAddress=146.120.185.4%2C%20198.143.55.5%3A23106; BrokerPopupIPAddress=2457385220-146.120.185.4-2457385220; BrokerPopupCountryCode=UA; IAAITrackingCookie=3ca68b7f-5664-4c24-a37f-8ce1bdad0eef; visid_incap_2807936=3Xr4afWaTFqc6ix+6ceJR3q8pWQAAAAAQUIPAAAAAABCX2U0d9912umOWc2E3ky2; nlbi_2807936=sobBPkyeth/Xgo3GxRLPjgAAAAAUr9dDmKiNlCvq1zuVAN4Q; incap_ses_520_2807936=c6YFRI34fwIhpTcppWk3B3q8pWQAAAAAH+YqwHycVv94gp+eMWDKlQ==; TimeZoneMapID=120; _gcl_au=1.1.745602433.1688583292; _ga_8J4GTR5B9Q=GS1.1.1688583291.1.0.1688583291.60.0.0; _evga_4ff5={%22uuid%22:%22bf58fa0b20aed1b6%22}; _sfid_4446={%22anonymousId%22:%22bf58fa0b20aed1b6%22%2C%22consents%22:[]}; _uetsid=6c76d9201b6511eea2dffd5acdf6d6db; _uetvid=6c76c7d01b6511ee8ec2a11cf202bd7b; nlbi_2807936_2147483392=SakDRHmwkXEYJKeWxRLPjgAAAABQg+Q3Y5H9kcBAqkZVxfN1; reese84=3:exfDceMepIp4UaWp/ExwvA==:r4WpmRn7ZiLNJxq+dwjqiM9z40RdCWZEyLJfQ1iyyV8t2pN9sL80gJcfuyg+2E5rQCm1JEWaBhl52xF/zLRkTLE44+bmoL1BPnbCeRKzUVtUwc/JZ02eB/OOIAmVsajVGpiG+aFPyDC3CRbEawAHH6OBlAduFHVEfDqxZ7ry/6bXzs1A97cf+zyrTl9qhrJ/ze37chQeFqrR//grsOmcX4yaHDcexSKB9tCxijw+gV9K0omsIXY/sSqCZ5YUHnNp/FPFLQhmrZmbPcidoJNyRn43sw2kuash/07XW4+gMizOhdKv9gq8fgLcq/f7liFU0hlczjHA38qrgYZy1teDzyJsEjyW7rVuwSHdSDP0d9L1owtY8GN8gw4ucF/bnaIzhOcBXN8Q+HtsdBsluloTJ/0Z58lCyiJ18kO2IRudK8Tdfd/CNUdE2joKUb+IjUZU6AYfjzGz7FlRDWJ3UNcW9Q==:27MOtinN9SNptBGyU7j8Jt/1twtN/SPCiZ+AOvDcbHY=; ln_or=eyIyMzg4ODk3IjoiZCJ9; _fbp=fb.1.1688583292361.87537795; _clck=1xptlkx|2|fd1|0|1281; _clsk=dkp5pg|1688583293156|1|1|v.clarity.ms/collect; mdLogger=false; kampyle_userid=7a50-797e-3339-464d-e264-7692-45be-0552; kampyleUserSession=1688583293405; kampyleUserSessionsCount=1; kampyleSessionPageCounter=1; ASP.NET_SessionId=xo50ztpwwwlbidqfilorzvpy; BrokerPopupCountryCodeIP=3331274501; Locations_Cookie=Locations_Cookie=MapView; OptanonAlertBoxClosed=2023-07-05T18:55:00.745Z; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Jul+05+2023+21%3A55%3A00+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.28.0&isIABGlobal=false&hosts=&consentId=257342f0-26fd-44be-a06d-d52063ffe8db&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A0%2CC0004%3A0; actualOptanonConsent=%2CC0001%2CC0003%2C; _ga=GA1.2.1025765507.1688583292; _gid=GA1.2.854761563.1688583302; _gat_%5Bobject%20Object%5D=1',
        'dnt': '1',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    with open("url.csv", newline='', encoding='utf-8') as files:
        urls = list(csv.reader(files, delimiter=' ', quotechar='|'))
        counter = 0
        for url in urls:
            filename = f"c:\\DATA\\iaai\\product\\data_{counter}.json"
            counter += 1
            if not os.path.exists(filename):
                pause_time = random.randint(5, 10)
                proxy = random.choice(proxies)
                proxy_host = proxy[0]
                proxy_port = proxy[1]
                proxy_user = proxy[2]
                proxy_pass = proxy[3]

                proxi = {
                    'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                    'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
                }
                try:
                    response = requests.get(url[0], cookies=cookies, headers=headers, proxies=proxi)  # , proxies=proxi
                except:
                    continue
                src = response.text
                soup = BeautifulSoup(src, 'lxml')
                script_tag = soup.find('script', {'id': 'ProductDetailsVM'})
                json_data = json.loads(script_tag.string)
                with open(filename, 'w') as f:
                    json.dump(json_data, f)

                time.sleep(pause_time)
            else:
                continue



def parsin():

    cookies = {

        'BrokerPopupIPAddress': '2457385220-146.120.185.4-2457385220',
        'BrokerPopupCountryCode': 'UA',
        'IAAITrackingCookie': '3ca68b7f-5664-4c24-a37f-8ce1bdad0eef',
        'visid_incap_2807936': '3Xr4afWaTFqc6ix+6ceJR3q8pWQAAAAAQUIPAAAAAABCX2U0d9912umOWc2E3ky2',
        'nlbi_2807936': 'sobBPkyeth/Xgo3GxRLPjgAAAAAUr9dDmKiNlCvq1zuVAN4Q',
        'incap_ses_520_2807936': 'c6YFRI34fwIhpTcppWk3B3q8pWQAAAAAH+YqwHycVv94gp+eMWDKlQ==',
        'TimeZoneMapID': '120',
        '_gcl_au': '1.1.745602433.1688583292',
        '_ga_8J4GTR5B9Q': 'GS1.1.1688583291.1.0.1688583291.60.0.0',
        '_evga_4ff5': '{%22uuid%22:%22bf58fa0b20aed1b6%22}',
        '_sfid_4446': '{%22anonymousId%22:%22bf58fa0b20aed1b6%22%2C%22consents%22:[]}',
        '_uetsid': '6c76d9201b6511eea2dffd5acdf6d6db',
        '_uetvid': '6c76c7d01b6511ee8ec2a11cf202bd7b',
        'nlbi_2807936_2147483392': 'SakDRHmwkXEYJKeWxRLPjgAAAABQg+Q3Y5H9kcBAqkZVxfN1',
        'reese84': '3:exfDceMepIp4UaWp/ExwvA==:r4WpmRn7ZiLNJxq+dwjqiM9z40RdCWZEyLJfQ1iyyV8t2pN9sL80gJcfuyg+2E5rQCm1JEWaBhl52xF/zLRkTLE44+bmoL1BPnbCeRKzUVtUwc/JZ02eB/OOIAmVsajVGpiG+aFPyDC3CRbEawAHH6OBlAduFHVEfDqxZ7ry/6bXzs1A97cf+zyrTl9qhrJ/ze37chQeFqrR//grsOmcX4yaHDcexSKB9tCxijw+gV9K0omsIXY/sSqCZ5YUHnNp/FPFLQhmrZmbPcidoJNyRn43sw2kuash/07XW4+gMizOhdKv9gq8fgLcq/f7liFU0hlczjHA38qrgYZy1teDzyJsEjyW7rVuwSHdSDP0d9L1owtY8GN8gw4ucF/bnaIzhOcBXN8Q+HtsdBsluloTJ/0Z58lCyiJ18kO2IRudK8Tdfd/CNUdE2joKUb+IjUZU6AYfjzGz7FlRDWJ3UNcW9Q==:27MOtinN9SNptBGyU7j8Jt/1twtN/SPCiZ+AOvDcbHY=',
        'ln_or': 'eyIyMzg4ODk3IjoiZCJ9',
        '_fbp': 'fb.1.1688583292361.87537795',
        '_clck': '1xptlkx|2|fd1|0|1281',
        '_clsk': 'dkp5pg|1688583293156|1|1|v.clarity.ms/collect',
        'mdLogger': 'false',
        'kampyle_userid': '7a50-797e-3339-464d-e264-7692-45be-0552',
        'kampyleUserSession': '1688583293405',
        'kampyleUserSessionsCount': '1',
        'kampyleSessionPageCounter': '1',
        'ASP.NET_SessionId': 'xo50ztpwwwlbidqfilorzvpy',
        'BrokerPopupCountryCodeIP': '3331274501',
        'Locations_Cookie': 'Locations_Cookie=MapView',
        'OptanonAlertBoxClosed': '2023-07-05T18:55:00.745Z',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Wed+Jul+05+2023+21%3A55%3A00+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.28.0&isIABGlobal=false&hosts=&consentId=257342f0-26fd-44be-a06d-d52063ffe8db&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A0%2CC0004%3A0',
        'actualOptanonConsent': '%2CC0001%2CC0003%2C',
        '_ga': 'GA1.2.1025765507.1688583292',
        '_gid': 'GA1.2.854761563.1688583302',
        '_gat_%5Bobject%20Object%5D': '1',
    }

    headers = {
        'authority': 'www.iaai.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru',
        'cache-control': 'no-cache',
        # 'cookie': 'X-Forwarded-For_IpAddress=146.120.185.4%2C%20198.143.55.5%3A23106; BrokerPopupIPAddress=2457385220-146.120.185.4-2457385220; BrokerPopupCountryCode=UA; IAAITrackingCookie=3ca68b7f-5664-4c24-a37f-8ce1bdad0eef; visid_incap_2807936=3Xr4afWaTFqc6ix+6ceJR3q8pWQAAAAAQUIPAAAAAABCX2U0d9912umOWc2E3ky2; nlbi_2807936=sobBPkyeth/Xgo3GxRLPjgAAAAAUr9dDmKiNlCvq1zuVAN4Q; incap_ses_520_2807936=c6YFRI34fwIhpTcppWk3B3q8pWQAAAAAH+YqwHycVv94gp+eMWDKlQ==; TimeZoneMapID=120; _gcl_au=1.1.745602433.1688583292; _ga_8J4GTR5B9Q=GS1.1.1688583291.1.0.1688583291.60.0.0; _evga_4ff5={%22uuid%22:%22bf58fa0b20aed1b6%22}; _sfid_4446={%22anonymousId%22:%22bf58fa0b20aed1b6%22%2C%22consents%22:[]}; _uetsid=6c76d9201b6511eea2dffd5acdf6d6db; _uetvid=6c76c7d01b6511ee8ec2a11cf202bd7b; nlbi_2807936_2147483392=SakDRHmwkXEYJKeWxRLPjgAAAABQg+Q3Y5H9kcBAqkZVxfN1; reese84=3:exfDceMepIp4UaWp/ExwvA==:r4WpmRn7ZiLNJxq+dwjqiM9z40RdCWZEyLJfQ1iyyV8t2pN9sL80gJcfuyg+2E5rQCm1JEWaBhl52xF/zLRkTLE44+bmoL1BPnbCeRKzUVtUwc/JZ02eB/OOIAmVsajVGpiG+aFPyDC3CRbEawAHH6OBlAduFHVEfDqxZ7ry/6bXzs1A97cf+zyrTl9qhrJ/ze37chQeFqrR//grsOmcX4yaHDcexSKB9tCxijw+gV9K0omsIXY/sSqCZ5YUHnNp/FPFLQhmrZmbPcidoJNyRn43sw2kuash/07XW4+gMizOhdKv9gq8fgLcq/f7liFU0hlczjHA38qrgYZy1teDzyJsEjyW7rVuwSHdSDP0d9L1owtY8GN8gw4ucF/bnaIzhOcBXN8Q+HtsdBsluloTJ/0Z58lCyiJ18kO2IRudK8Tdfd/CNUdE2joKUb+IjUZU6AYfjzGz7FlRDWJ3UNcW9Q==:27MOtinN9SNptBGyU7j8Jt/1twtN/SPCiZ+AOvDcbHY=; ln_or=eyIyMzg4ODk3IjoiZCJ9; _fbp=fb.1.1688583292361.87537795; _clck=1xptlkx|2|fd1|0|1281; _clsk=dkp5pg|1688583293156|1|1|v.clarity.ms/collect; mdLogger=false; kampyle_userid=7a50-797e-3339-464d-e264-7692-45be-0552; kampyleUserSession=1688583293405; kampyleUserSessionsCount=1; kampyleSessionPageCounter=1; ASP.NET_SessionId=xo50ztpwwwlbidqfilorzvpy; BrokerPopupCountryCodeIP=3331274501; Locations_Cookie=Locations_Cookie=MapView; OptanonAlertBoxClosed=2023-07-05T18:55:00.745Z; OptanonConsent=isGpcEnabled=0&datestamp=Wed+Jul+05+2023+21%3A55%3A00+GMT%2B0300+(%D0%92%D0%BE%D1%81%D1%82%D0%BE%D1%87%D0%BD%D0%B0%D1%8F+%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D0%B0%2C+%D0%BB%D0%B5%D1%82%D0%BD%D0%B5%D0%B5+%D0%B2%D1%80%D0%B5%D0%BC%D1%8F)&version=6.28.0&isIABGlobal=false&hosts=&consentId=257342f0-26fd-44be-a06d-d52063ffe8db&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0003%3A1%2CC0002%3A0%2CC0004%3A0; actualOptanonConsent=%2CC0001%2CC0003%2C; _ga=GA1.2.1025765507.1688583292; _gid=GA1.2.854761563.1688583302; _gat_%5Bobject%20Object%5D=1',
        'dnt': '1',
        'pragma': 'no-cache',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }
    folders_html = r"c:\DATA\iaai\product\*.json"
    files_html = glob.glob(folders_html)
    with open(f'data.csv', "w", newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=";")

        for i in files_html:
            pause_time = random.randint(1, 5)
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]

            proxi = {
                'http': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}',
                'https': f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'
            }
            with open(i, 'r') as f:
                data_json = json.load(f)
            print(i)
            name_lot = data_json['inventoryView']['attributes']['YearMakeModelSeries']
            lot_number = data_json['inventoryView']['attributes']['StockNumber']
            url_lot = f"https://www.iaai.com/VehicleDetail/{data_json['inventoryView']['attributes']['Id']}"
            urls_img_lot = data_json['inventoryView']['attributes']['KeyImageLink']
            response_img = requests.get(urls_img_lot, cookies=cookies, headers=headers, proxies=proxi)
            data_json_img = response_img.json()
            url_template = "https://vis.iaai.com/resizer?imageKeys={}&width=845&height=633"
            keys = [item["K"] for item in data_json_img["keys"]]
            image_urls = [url_template.format(key) for key in keys]
            image_url = ''
            for url in image_urls[:1]:
                image_url = url

            """После этого нужно получить ссылки на фото"""
            price_lot = data_json['auctionInformation']['biddingInformation']['buyNowPrice']
            odometer = data_json['inventoryView']['attributes']['ODOValue']
            drive_tyne_type = data_json['inventoryView']['vehicleDescription']['$values'][5]['value']
            vehicle_lot = data_json['inventoryView']['attributes']['InventoryType']
            try:
                engine_lot = data_json['inventoryView']['attributes']['EngineSize'].strip()
            except:
                engine_lot = None
            start_code_lot = data_json['inventoryView']['attributes']['StartsDesc']
            branchname_lot = data_json['inventoryView']['attributes']['BranchName']
            datas = [name_lot, lot_number, url_lot, price_lot, odometer, drive_tyne_type, vehicle_lot, engine_lot,
                     start_code_lot, branchname_lot, image_url]
            writer.writerow(datas)


if __name__ == '__main__':
    # get_request()
    # get_id_ad_and_url()
    # get_product()
    parsin()
