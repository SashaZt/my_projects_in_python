cookies = {
    '55d52f4edaff497bee53fa40ef47c28a': '-',
    '_ga_K0BLLR9VYJ': 'GS1.1.1691059355.1.0.1691059355.60.0.0',
    '_gcl_au': '1.1.1934139630.1691059355',
    '_ga': 'GA1.3.1392180992.1691059355',
    '_gid': 'GA1.3.302367913.1691059355',
    '_dc_gtm_UA-117509752-1': '1',
}

headers = {
    'authority': 'demex.com.ua',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru',
    'cache-control': 'no-cache',
    # 'cookie': '55d52f4edaff497bee53fa40ef47c28a=-; _ga_K0BLLR9VYJ=GS1.1.1691059355.1.0.1691059355.60.0.0; _gcl_au=1.1.1934139630.1691059355; _ga=GA1.3.1392180992.1691059355; _gid=GA1.3.302367913.1691059355; _dc_gtm_UA-117509752-1=1',
    'dnt': '1',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
}
headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in cookies.items()])