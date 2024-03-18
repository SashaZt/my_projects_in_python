import aiohttp
import asyncio
import aiofiles
import random
import os
import json
from proxi import proxies

async def get_request():
    ad = 19209
    page_ad = ad // 100
    start = 0
    page = 0

    cookies = {
        'visid_incap_242093': '2lrTgR4eQveOZYxHtsl506EysWQAAAAAQUIPAAAAAADWrp1XyedHe4hy3PH5ChFj',
        'incap_ses_520_242093': '5/F0XydE/R8nVz17p2k3B6EysWQAAAAAlzPw7Bl2xbYK00ZR8kHBRw==',
        'g2usersessionid': '0b4f61da6613900ecce840bc5d774668',
        'G2JSESSIONID': '2252CF46DA3C43D538E4B50FFB8F8E4B-n1',
        'userLang': 'en',
        'nlbi_242093': 'PkFwC+RgQBvfN/PqJDHybgAAAAACFWSEV03diFSBzt4ngLP3',
        'userCategory': 'PU',
        'timezone': 'Europe%2FKiev',
        'copartTimezonePref': '%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D',
        'nlbi_242093_2147483392': '91lXMF3ayEm+g0cvJDHybgAAAAAw5n+Qs3s5HwVwHHzHI+c1',
        'reese84': '3:tNxMkSq8Ol68LDSrb0VRlA==:6CeJopDQDK2bRm/J1RA4DXsxVE6QLFPtZIhszzxj6fDDRoK1x76W0l0/oiqh9F2JqSph2gnFUqv6e0qLOwvGOJHtavDHYM80oMogKlPevcZIXH7kRNYiZT05BSJItb6OY+evOjyhGvk9vTkYaIMKX6vEgCvwG5Znc4O2S6arHRe9M6CdyVTawnroXu1MfECba95VuKlqlHjvW6RAj87s2Fk6h9CNvRPAnnz/ClqqucbumBPdRD1W/3KZmDyiOQeh8Y+ADwUxAWjaUy1Eb6J5gpfA5Ie2gHcieucaBUpzl7W4kc227QSq251GwVdBQvlQYFtX/uvk4XUMmndX/DZVQaLEIf7OKg/bF+YHeoagABdWcPzMi3AmjlmHf5lrLCIyVlMiuGH2XJg9jlULPUgbVThEx1iU/r7Rx3aAl894GXnDTbXAXEhXln1bgUzyyXjGJMS2h+qNkUMp4/ESDRB8bdYeWnY5UL0TbfTn+y2e/xkCufbC9Fc/pf2yIKzb/3y2niRed+1YngSpwCjNc05jGw==:5Z2E+XXnzd8VWg3UBvF+bREK3owmWdeL4L7xuloEc1Y=',
        'search-table-rows': '20',
        '_gcl_au': '1.1.1816893115.1689334438',
        '_gid': 'GA1.2.321455638.1689334438',
        '_gat_UA-90930613-6': '1',
        '_ga': 'GA1.1.2059080137.1689334438',
        '_ga_VMJJLGQLHF': 'GS1.1.1689334437.1.1.1689334437.60.0.0',
        '_uetsid': '525789a0223a11ee948cbb4cd856506c',
        '_uetvid': '5257b190223a11ee85bc5187039b6058',
        '_fbp': 'fb.1.1689334438115.643435950',
        '_clck': 'irsd2v|2|fda|0|1290',
        '_tt_enable_cookie': '1',
        '_ttp': 'OEnfEXlwar09n07kynumHsw5yrn',
        '_cc_id': 'a8f61db4245b809c28280470ee6681b1',
        'panoramaId_expiry': '1689939238661',
        'panoramaId': '30f3b0e877945190fb8d78c2664516d5393809eca30229a45c0d5b7d22138292',
        'panoramaIdType': 'panoIndiv',
        'cto_bundle': 'Ym4yXF81bVlGV2Z5THhZWFhXQWU1bVdJR2ZPNFZPTXdobXhnYml4cHRpU0RwNnFteEVnMjJyT2E5UmFqa21tQWoxdDM0V0sxU28lMkZZTDZkYlU0eVZpbVNWRjNoQ21KSldhaEl1bVFFN0lIQlBjQWlLNnZiUjVaaSUyRnVpcE5wcGUyWUtFRzE',
        '_clsk': '199h2et|1689334438804|1|0|o.clarity.ms/collect',
        '__gads': 'ID=61dd735953f851d0:T=1689334439:RT=1689334439:S=ALNI_MYXT5R-y9vmjUIdfKURKhWMEK-lBA',
        '__gpi': 'UID=00000c3cb4674c7a:T=1689334439:RT=1689334439:S=ALNI_MbGBdUrKf4a_SbukMHcLXttUzrFRA',
        'FCNEC': '%5B%5B%22AKsRol8c9xsFy40V17qjodnZoZgpzBGX-M9Pj5Z53_n1FthePKywqLKdeSjA0ig6ORBnSSssZ19yp3cVErcjeGZMeFCS_ASASXCN3mWrisdaEmuwf4MpoEEThlHcO8_c-5umnLn34koR4JuBSa_67WWNVO4ly0Tvqw%3D%3D%22%5D%2Cnull%2C%5B%5D%5D',
        's_ppv': '100',
        's_fid': '114B8CE6739DA9E4-1D93001F484DEF80',
        's_depth': '1',
        's_pv': 'no%20value',
        's_nr': '1689334450407-New',
        's_vnum': '1691926450407%26vn%3D1',
        's_invisit': 'true',
        's_lv': '1689334450407',
        's_lv_s': 'First%20Visit',
    }

    headers = {
        'authority': 'www.copart.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru',
        'access-control-allow-headers': 'Content-Type, X-XSRF-TOKEN',
        'content-type': 'application/json',
        # 'cookie': 'visid_incap_242093=2lrTgR4eQveOZYxHtsl506EysWQAAAAAQUIPAAAAAADWrp1XyedHe4hy3PH5ChFj; incap_ses_520_242093=5/F0XydE/R8nVz17p2k3B6EysWQAAAAAlzPw7Bl2xbYK00ZR8kHBRw==; g2usersessionid=0b4f61da6613900ecce840bc5d774668; G2JSESSIONID=2252CF46DA3C43D538E4B50FFB8F8E4B-n1; userLang=en; nlbi_242093=PkFwC+RgQBvfN/PqJDHybgAAAAACFWSEV03diFSBzt4ngLP3; userCategory=PU; timezone=Europe%2FKiev; copartTimezonePref=%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D; nlbi_242093_2147483392=91lXMF3ayEm+g0cvJDHybgAAAAAw5n+Qs3s5HwVwHHzHI+c1; reese84=3:tNxMkSq8Ol68LDSrb0VRlA==:6CeJopDQDK2bRm/J1RA4DXsxVE6QLFPtZIhszzxj6fDDRoK1x76W0l0/oiqh9F2JqSph2gnFUqv6e0qLOwvGOJHtavDHYM80oMogKlPevcZIXH7kRNYiZT05BSJItb6OY+evOjyhGvk9vTkYaIMKX6vEgCvwG5Znc4O2S6arHRe9M6CdyVTawnroXu1MfECba95VuKlqlHjvW6RAj87s2Fk6h9CNvRPAnnz/ClqqucbumBPdRD1W/3KZmDyiOQeh8Y+ADwUxAWjaUy1Eb6J5gpfA5Ie2gHcieucaBUpzl7W4kc227QSq251GwVdBQvlQYFtX/uvk4XUMmndX/DZVQaLEIf7OKg/bF+YHeoagABdWcPzMi3AmjlmHf5lrLCIyVlMiuGH2XJg9jlULPUgbVThEx1iU/r7Rx3aAl894GXnDTbXAXEhXln1bgUzyyXjGJMS2h+qNkUMp4/ESDRB8bdYeWnY5UL0TbfTn+y2e/xkCufbC9Fc/pf2yIKzb/3y2niRed+1YngSpwCjNc05jGw==:5Z2E+XXnzd8VWg3UBvF+bREK3owmWdeL4L7xuloEc1Y=; search-table-rows=20; _gcl_au=1.1.1816893115.1689334438; _gid=GA1.2.321455638.1689334438; _gat_UA-90930613-6=1; _ga=GA1.1.2059080137.1689334438; _ga_VMJJLGQLHF=GS1.1.1689334437.1.1.1689334437.60.0.0; _uetsid=525789a0223a11ee948cbb4cd856506c; _uetvid=5257b190223a11ee85bc5187039b6058; _fbp=fb.1.1689334438115.643435950; _clck=irsd2v|2|fda|0|1290; _tt_enable_cookie=1; _ttp=OEnfEXlwar09n07kynumHsw5yrn; _cc_id=a8f61db4245b809c28280470ee6681b1; panoramaId_expiry=1689939238661; panoramaId=30f3b0e877945190fb8d78c2664516d5393809eca30229a45c0d5b7d22138292; panoramaIdType=panoIndiv; cto_bundle=Ym4yXF81bVlGV2Z5THhZWFhXQWU1bVdJR2ZPNFZPTXdobXhnYml4cHRpU0RwNnFteEVnMjJyT2E5UmFqa21tQWoxdDM0V0sxU28lMkZZTDZkYlU0eVZpbVNWRjNoQ21KSldhaEl1bVFFN0lIQlBjQWlLNnZiUjVaaSUyRnVpcE5wcGUyWUtFRzE; _clsk=199h2et|1689334438804|1|0|o.clarity.ms/collect; __gads=ID=61dd735953f851d0:T=1689334439:RT=1689334439:S=ALNI_MYXT5R-y9vmjUIdfKURKhWMEK-lBA; __gpi=UID=00000c3cb4674c7a:T=1689334439:RT=1689334439:S=ALNI_MbGBdUrKf4a_SbukMHcLXttUzrFRA; FCNEC=%5B%5B%22AKsRol8c9xsFy40V17qjodnZoZgpzBGX-M9Pj5Z53_n1FthePKywqLKdeSjA0ig6ORBnSSssZ19yp3cVErcjeGZMeFCS_ASASXCN3mWrisdaEmuwf4MpoEEThlHcO8_c-5umnLn34koR4JuBSa_67WWNVO4ly0Tvqw%3D%3D%22%5D%2Cnull%2C%5B%5D%5D; s_ppv=100; s_fid=114B8CE6739DA9E4-1D93001F484DEF80; s_depth=1; s_pv=no%20value; s_nr=1689334450407-New; s_vnum=1691926450407%26vn%3D1; s_invisit=true; s_lv=1689334450407; s_lv_s=First%20Visit',
        'dnt': '1',
        'origin': 'https://www.copart.com',
        'referer': 'https://www.copart.com/vehicleFinderSearch?searchStr=%7B%22MISC%22:%5B%22%23VehicleTypeCode:VEHTYPE_V%22,%22%23OdometerReading:%5B0%20TO%209999999%5D%22,%22%23LotYear:%5B2011%20TO%202024%5D%22%5D,%22sortByZip%22:false,%22buyerEnteredZip%22:null,%22milesAway%22:null%7D%20&displayStr=%5B0%20TO%209999999%5D,%5B2011%20TO%202024%5D&from=%2FvehicleFinder',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
        'x-xsrf-token': '39abe364-c11d-4373-8dc6-151b5c93c86c',
    }





    for i in range(0, 101):
        json_data = {
            'query': [
                '*',
            ],
            'filter': {
                'MISC': [
                    '#VehicleTypeCode:VEHTYPE_V',
                    '#OdometerReading:[0 TO 9999999]',
                    '#LotYear:[2011 TO 2024]',
                ],
            },
            'sort': [
                'member_damage_group_priority asc',
                'auction_date_type desc',
                'auction_date_utc asc',
            ],
            'page': page,
            'size': 100,
            'start': start,
            'watchListOnly': False,
            'freeFormSearch': False,
            'hideImages': False,
            'defaultSort': False,
            'specificRowProvided': False,
            'displayName': '',
            'searchName': '',
            'backUrl': '',
            'includeTagByField': {},
            'rawParams': {},
        }
        filename = f"c:\\DATA\\copart\\list\\data_{page}.json"
        if not os.path.exists(filename):
            # pause_time = random.randint(5, 10)
            proxy = random.choice(proxies)
            proxy_host = proxy[0]
            proxy_port = proxy[1]
            proxy_user = proxy[2]
            proxy_pass = proxy[3]

            proxi = f'http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}'

            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post('https://www.copart.com/public/lots/search-results',
                                            headers=headers, cookies=cookies, json=json_data,
                                            proxy=proxi) as response:
                        data = await response.json()
                        async with aiofiles.open(filename, 'w') as f:
                            await f.write(json.dumps(data))
                except:
                    continue
            # await asyncio.sleep(pause_time)
        page += 1
        start += 20

# Запуск асинхронной функции
loop = asyncio.get_event_loop()
loop.run_until_complete(get_request())
