import requests

cookies = {
    "sid": "iddx1xqd4e4iwzoyl1tbdkiu",
    "uss": "4e3a002b-b10f-4f5a-83b1-2af3659855ff",
    "__RequestVerificationToken": "-daFHhNiGck4PTcLDV3OeqSHdp36Up1xo4uy_xDhkrzHV0h7oFsimLxyPC5aT2rMEs3Ee0XR-aiH8jtmOYuH2VLuPRR9ohhmXAxDBwojQr01",
    "_gid": "GA1.2.1589081303.1715416861",
    "_gat": "1",
    "_gcl_au": "1.1.1649775358.1715416861",
    "_dc_gtm_UA-38210263-4": "1",
    "_gat_UA-238453145-1": "1",
    "session_timer_104054": "1",
    "_fbp": "fb.1.1715416861473.1152719356",
    "_ga": "GA1.1.833406689.1715416861",
    "_tt_enable_cookie": "1",
    "_ttp": "vkj1jKVoQzkc1sxB-kJG93_LWyo",
    "_ga_6352MSYKNX": "GS1.1.1715416861.1.0.1715416867.54.0.0",
    "_ga_83HJKTVF69": "GS1.1.1715416861.1.0.1715416867.0.0.0",
    "_ga_ECXG0392JW": "GS1.1.1715416861.1.0.1715416867.0.0.0",
}

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "Connection": "keep-alive",
    "DNT": "1",
    "Referer": "https://auto1.by/search?pattern=OC47",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

params = {
    "pattern": "OC47",
}

response = requests.get(
    "https://auto1.by/search", params=params, cookies=cookies, headers=headers
)
