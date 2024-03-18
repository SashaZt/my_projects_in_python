url = 'https://www.copart.com/public/lots/vehicle-finder-search-results'

params = {
}

cookies = {
    # 'visid_incap_242093': 'OBoGm0RQSMy8Aijzr3OI0dENFWUAAAAAQUIPAAAAAAAuenCqyMxs/LPsnhpnWm0z',
    'incap_ses_325_242093': 'if9kSahpvnKCUmwseKKCBIZ9FmUAAAAAsshxwkL/pYSeYB94NE4tBQ==', #Нужный параметр
    # 'g2usersessionid': '0b4f61da6613900ecce840bc5d774668',
    # 'G2JSESSIONID': '276C9B5F13CCF40E2B9A3B1037185775-n1',
    'userLang': 'en',
    # 'nlbi_242093': '46OLViP2OjlUM5M0JDHybgAAAAAJuBpTMmknrWaNRukj5ANU',
    'userCategory': 'PU',
    'timezone': 'Europe%2FKiev',
    # 'copartTimezonePref': '%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D',
    # 'g2app.search-table-rows': '20',
}

headers = {
    'Host': 'www.copart.com',
    'Connection': 'keep-alive',
    # 'Content-Length': '330',
    'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'X-XSRF-TOKEN': '0802fc3f-d953-45af-96bf-0ef8a954d65e',
    'sec-ch-ua-mobile': '?0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/plain, */*',
    'X-Requested-With': 'XMLHttpRequest',
    'Access-Control-Allow-Headers': 'Content-Type, X-XSRF-TOKEN',
    'sec-ch-ua-platform': '"Windows"',
    'Origin': 'https://www.copart.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Referer': 'https://www.copart.com/vehicleFinderSearch?displayStr=%5B0%20TO%209999999%5D,%5B2011%20TO%202024%5D&from=%2FvehicleFinder&searchCriteria=%7B%22query%22:%5B%22*%22%5D,%22filter%22:%7B%22NLTS%22:%5B%22expected_sale_assigned_ts_utc:%5BNOW%2FDAY-1DAY%20TO%20NOW%2FDAY%5D%22%5D%7D,%22searchName%22:%22%22,%22watchListOnly%22:false,%22freeFormSearch%22:false%7D',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    # 'Cookie': 'visid_incap_242093=vB/ZArstT1mS/1cLb10rPI0RFWUAAAAAQUIPAAAAAAD8HCBbsZznwqSRtVwuWTGU; incap_ses_325_242093=0F/eIWmZWyIu3sIreKKCBI0RFWUAAAAABjOwbcU4hHukhEBhWlogSQ==; g2usersessionid=713bc97ef3fb607e35728bb615a1ad66; G2JSESSIONID=E4697C803F0248B1BDCB43E1726AEEAA-n1; userLang=en; nlbi_242093=F1eHeoFfin7abvSZJDHybgAAAADvotmdoZmyKZh+IxJEktdm; userCategory=PU; timezone=Europe%2FKiev; copartTimezonePref=%7B%22displayStr%22%3A%22GMT%2B3%22%2C%22offset%22%3A3%2C%22dst%22%3Atrue%2C%22windowsTz%22%3A%22Europe%2FKiev%22%7D; g2app.search-table-rows=20',
}
