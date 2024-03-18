import traceback
import aiofiles
import csv
import datetime
import mysql.connector
import aiohttp
import asyncio
import os
from bs4 import BeautifulSoup

cookies = {
    '_ga': 'GA1.1.1877634419.1684588744',
    '__gads': 'ID=44a75626fff762fd-221fc7b6e1dd001a:T=1684588742:RT=1684588742:S=ALNI_MbrVuywU_pclGo22ghdMa9tZkKa-g',
    '__gpi': 'UID=00000c18a0db2a0e:T=1684588742:RT=1684588742:S=ALNI_MZbONx5nQi2oxly5gKcYbLpJF_slA',
    'SLG_G_WPT_TO': 'ru',
    '__cf_bm': 'xEKQ.QTq.fxpp22gWNwikkKvwPAI.21Mqurxm3YaC4M-1684588744-0-AYzXZdUEqfcB31x9Zo+uZ0ptanEflCnzueeV+TCbOdOmLM0STo7uhyTn6alAN6foP27FFrPDdlSubkJM7bZvrxhuj9kOFIa2zEmGdOuYb0B5',
    'SLG_GWPT_Show_Hide_tmp': '1',
    'SLG_wptGlobTipTmp': '1',
    'XSRF-TOKEN': 'eyJpdiI6InN3SkNpak5aQlIvSGpaL3BXWHhVY0E9PSIsInZhbHVlIjoiMklrSnJFY0l6bHRIZzhZa3FSdVFyQUVGT2F3VU12NVovVGRseW9FaDZ4eDU3bDcxcnVKTzR1NmIva0o1aDVVM05xNFd0ZlVzblFKeVgxMnlrQjUwaE12OVhac04xZWNDTHpJN2VpQmF6TUE0RTJwRklMSEl6V09qeW5LbnIwVGciLCJtYWMiOiJmYzQwZTdmNDJhYjFhY2MyNDIzNDcyZThhNDExZjgzY2U1MDg3NjE0ZGEwYzI2MDk3ZTFkNGU5MmIyYWU2YjJhIiwidGFnIjoiIn0%3D',
    'ucars_session': 'eyJpdiI6IlJZYnhrY0JGbXFkZzBnUG1GMVh6MGc9PSIsInZhbHVlIjoiaGZzVmRzcFZSRzVDRm1lWUI4RDdIR3pRMXZtdHhkRytQeEZJS25EOU9XOFUvTVQxTDR2dWZleURRY1dUNUpUOUhOS1BSTFpzWXdTK2htbnpxeWVKdWdJa2xtRnNNQmM3Z0R5WEF1RldYbkpUUzlGYjlTbVlGZTE5cEhuRzVBZVQiLCJtYWMiOiIwNGNlMzhhYjMyZTg2MTQ0ZDk3ZTk0NTAyNjFjYWZiMzY4NjQ4Mjk0MmFmN2I3YWMyZDRhNDY1MThiMGU4YThmIiwidGFnIjoiIn0%3D',
    '_ga_QYNZZE6GRT': 'GS1.1.1684588743.1.1.1684589216.0.0.0',
}
headers = {
    'authority': 'ucars.pro',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cache-control': 'max-age=0',
    # 'cookie': '_ga=GA1.1.1877634419.1684588744; __gads=ID=44a75626fff762fd-221fc7b6e1dd001a:T=1684588742:RT=1684588742:S=ALNI_MbrVuywU_pclGo22ghdMa9tZkKa-g; __gpi=UID=00000c18a0db2a0e:T=1684588742:RT=1684588742:S=ALNI_MZbONx5nQi2oxly5gKcYbLpJF_slA; SLG_G_WPT_TO=ru; __cf_bm=xEKQ.QTq.fxpp22gWNwikkKvwPAI.21Mqurxm3YaC4M-1684588744-0-AYzXZdUEqfcB31x9Zo+uZ0ptanEflCnzueeV+TCbOdOmLM0STo7uhyTn6alAN6foP27FFrPDdlSubkJM7bZvrxhuj9kOFIa2zEmGdOuYb0B5; SLG_GWPT_Show_Hide_tmp=1; SLG_wptGlobTipTmp=1; XSRF-TOKEN=eyJpdiI6InN3SkNpak5aQlIvSGpaL3BXWHhVY0E9PSIsInZhbHVlIjoiMklrSnJFY0l6bHRIZzhZa3FSdVFyQUVGT2F3VU12NVovVGRseW9FaDZ4eDU3bDcxcnVKTzR1NmIva0o1aDVVM05xNFd0ZlVzblFKeVgxMnlrQjUwaE12OVhac04xZWNDTHpJN2VpQmF6TUE0RTJwRklMSEl6V09qeW5LbnIwVGciLCJtYWMiOiJmYzQwZTdmNDJhYjFhY2MyNDIzNDcyZThhNDExZjgzY2U1MDg3NjE0ZGEwYzI2MDk3ZTFkNGU5MmIyYWU2YjJhIiwidGFnIjoiIn0%3D; ucars_session=eyJpdiI6IlJZYnhrY0JGbXFkZzBnUG1GMVh6MGc9PSIsInZhbHVlIjoiaGZzVmRzcFZSRzVDRm1lWUI4RDdIR3pRMXZtdHhkRytQeEZJS25EOU9XOFUvTVQxTDR2dWZleURRY1dUNUpUOUhOS1BSTFpzWXdTK2htbnpxeWVKdWdJa2xtRnNNQmM3Z0R5WEF1RldYbkpUUzlGYjlTbVlGZTE5cEhuRzVBZVQiLCJtYWMiOiIwNGNlMzhhYjMyZTg2MTQ0ZDk3ZTk0NTAyNjFjYWZiMzY4NjQ4Mjk0MmFmN2I3YWMyZDRhNDY1MThiMGU4YThmIiwidGFnIjoiIn0%3D; _ga_QYNZZE6GRT=GS1.1.1684588743.1.1.1684589216.0.0.0',
    'referer': 'https://ucars.pro/ru/live-auctions?status=1&page=3',
    'sec-ch-ua': '"Chromium";v="112", "Not_A Brand";v="24", "Opera";v="98"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': '(Linux; Android 7.0;) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)',
}
url_list = [
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tacura\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\talfa_romeo\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\taudi\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tbentley\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tbmw\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tbuick\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tcadillac\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tchery\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tchevorlet\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tcitroen\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tdodge\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tferrari\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tfiat\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tford\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tgeely\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tgenesis\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tgmc\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\thonda\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\thummer\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\thyundai\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tinfiniti\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tisuzu\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2019\t&year-to=\t2019',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2020\t&year-to=\t2020',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2021\t&year-to=\t2021',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2022\t&year-to=\t2022',
    'https://ucars.pro/ru/sales-history/\tjaguar\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2023\t&year-to=\t2023',
    'https://ucars.pro/ru/sales-history/\tjeep\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2014\t&year-to=\t2014',
    'https://ucars.pro/ru/sales-history/\tjeep\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2015\t&year-to=\t2015',
    'https://ucars.pro/ru/sales-history/\tjeep\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2016\t&year-to=\t2016',
    'https://ucars.pro/ru/sales-history/\tjeep\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2017\t&year-to=\t2017',
    'https://ucars.pro/ru/sales-history/\tjeep\t?odometer-from=\t0\t&odometer-to=\t50000\t&year-from=\t2018\t&year-to=\t2018']

bad_urls = []


async def load_bad_urls():
    if os.path.exists('bad_url.csv'):
        async with aiofiles.open('bad_url.csv', 'r') as csv_file:
            content = await csv_file.read()  # Прочитайте весь файл
            csv_reader = csv.reader(content.splitlines())  # Итерируйтесь по строкам
            bad_urls.extend([row[0] for row in csv_reader])


async def write_bad_url(link):
    if link not in bad_urls:
        bad_urls.append(link)
        async with aiofiles.open('bad_url.csv', 'a') as csv_file:
            writer = csv.writer(csv_file)
            await csv_file.write(f'{link}\n')  # Запишите строку в файл


async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()


async def check_bad_links(link):
    # Если файл не существует, то ссылка точно новая
    if not os.path.exists('bad_url.csv'):
        return False
    async with aiofiles.open('bad_url.csv', 'r') as csv_file:
        content = await csv_file.read()  # Прочитайте весь файл
        csv_reader = csv.reader(content.splitlines())  # Итерируйтесь по строкам
        for row in csv_reader:
            if link in row:
                return True
    return False


async def get_links():
    connector = aiohttp.TCPConnector(ssl=False, limit=None)
    async with aiohttp.ClientSession(cookies=cookies, headers=headers, connector=connector) as session:
        for url in url_list:
            response = await fetch(session, url)
            soup = BeautifulSoup(response, 'lxml')
            try:
                pagination = int(soup.find('ul', class_='pagination').find_all('li')[-2].text)
            except:
                continue

            tasks = []
            for i in range(1, pagination + 1):
                new_url = url.replace('page=2', f'page={i}')
                task = asyncio.create_task(fetch(session, new_url))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            for response in responses:
                soup = BeautifulSoup(response, 'lxml')
                thumbs = soup.find_all('a', class_='vehicle-card__thumb')
                for thumb in thumbs:
                    link = thumb.get('href')
                    # Если ссылка уже в списке плохих ссылок, пропустить её
                    if await check_bad_links(link):
                        continue
                    print(f'Новая ссылка {link}')
                    yield link


async def process_link(link):
    async with aiohttp.ClientSession(cookies=cookies, headers=headers) as session:
        response = await fetch(session, link)
        soup = BeautifulSoup(response, 'lxml')

        pill = soup.find_all('div', class_='pill')
        title = soup.find('div', class_='headline').text if soup.find('div', class_='headline') else None
        tablets = soup.find_all('table', class_='card__table')
        try:
            table1, table2, table3, table4 = tablets[2], tablets[3], tablets[0], tablets[1]
        except:
            return

        tds_list1 = [td.text for row in table1.find_all('tr') for i, td in enumerate(row.find_all('td')) if i % 2 == 1]
        tds_list2 = [td.text for row in table2.find_all('tr') for i, td in enumerate(row.find_all('td')) if i % 2 == 1]
        tds_list3 = [td.text for row in table3.find_all('tr') for i, td in enumerate(row.find_all('td')) if i % 2 == 1]
        tds_list4 = [td.text for row in table4.find_all('tr') for i, td in enumerate(row.find_all('td')) if i % 2 == 1]

        vin = pill[0].text[5:]
        number = pill[1].text

        price = soup.find('span', class_='lot__bidding-digits').text

        imgs = soup.find_all('img', class_='lot__slider-image')
        image_urls = [img_tag['data-splide-lazy'] if 'data-splide-lazy' in img_tag.attrs else img_tag['src'] for img_tag
                      in imgs]

        auction, country, branch, dealer, pos, date, time = tds_list1[:7]
        docks, loss, crush, second_crush, state, odometer, retail, fix = tds_list2[:8]
        type_auto, year, mark, model, color = tds_list3[:5]
        body, drive, fuel, engine, transmission = tds_list4[:5]
        print(auction)
        print(image_urls)
        conn = mysql.connector.connect(
            host="localhost",  # Адрес хоста базы данных
            user="car_db_user_001",  # Имя пользователя базы данных
            password="wE8wH9jA3jfC5hK6hY6j",  # Пароль пользователя базы данных
            database="lot_database"  # Имя базы данных
        )
        cursor = conn.cursor()
        if auction == 'Copart':
            select_query = """
                SELECT * FROM lot_copart WHERE vin = %(vin)s AND number = %(number)s
            """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                            INSERT INTO lot_copart (
                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                            )
                            VALUES (
                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                            )
                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)

            conn.commit()
        elif auction == 'IAAI':
            select_query = """
                    SELECT * FROM lot_iaai WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_iaai (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()


        elif auction == 'Impact':
            select_query = """
                    SELECT * FROM lot_impact WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_impact (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Emirates Auction':
            select_query = """
                    SELECT * FROM lot_emirates_auction WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_emirates_auction (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Auction Wini':
            select_query = """
                    SELECT * FROM lot_auction_wini WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_auction_wini (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart UK':
            select_query = """
                    SELECT * FROM lot_copart_uk WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_uk (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart MEA':
            select_query = """
                    SELECT * FROM lot_copart_mea WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_mea (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart US':
            select_query = """
                    SELECT * FROM lot_copart_us WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_us (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart CA':
            select_query = """
                    SELECT * FROM lot_copart_ca WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_ca (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart GB':
            select_query = """
                    SELECT * FROM lot_copart_gb WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_gb (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart IE':
            select_query = """
                    SELECT * FROM lot_copart_ie WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_ie (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart AE':
            select_query = """
                    SELECT * FROM lot_copart_ae WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_ae (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart OM':
            select_query = """
                    SELECT * FROM lot_copart_om WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_om (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Copart BH':
            select_query = """
                    SELECT * FROM lot_copart_bh WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_copart_bh (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'IAAI UK':
            select_query = """
                    SELECT * FROM lot_iaai_uk WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_iaai_uk (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'IAAI US':
            select_query = """
                    SELECT * FROM lot_iaai_us WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_iaai_us (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'IAAI CA':
            select_query = """
                    SELECT * FROM lot_iaai_ca WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_iaai_ca (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'IAAI GB':
            select_query = """
                    SELECT * FROM lot_iaai_gb WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_iaai_gb (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'IAAI AE':
            select_query = """
                    SELECT * FROM lot_iaai_ae WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_iaai_ae (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'IAAI QA':
            select_query = """
                    SELECT * FROM lot_iaai_qa WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_iaai_qa (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Impact CA':
            select_query = """
                    SELECT * FROM lot_impact_ca WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_impact_ca (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Impact GB':
            select_query = """
                    SELECT * FROM lot_impact_gb WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_impact_gb (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Usa':
            select_query = """
                    SELECT * FROM lot_usa WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_usa (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Canada':
            select_query = """
                    SELECT * FROM lot_canada WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_canada (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Great Britain':
            select_query = """
                    SELECT * FROM lot_great_britain WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_great_britain (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Ireland':
            select_query = """
                    SELECT * FROM lot_ireland WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_ireland (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Uae':
            select_query = """
                    SELECT * FROM lot_uae WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_uae (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Oman':
            select_query = """
                    SELECT * FROM lot_oman WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_oman (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Bahrain':
            select_query = """
                    SELECT * FROM lot_bahrain WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_bahrain (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Korea':
            select_query = """
                    SELECT * FROM lot_korea WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_korea (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()

        elif auction == 'Qatar':
            select_query = """
                    SELECT * FROM lot_qatar WHERE vin = %(vin)s AND number = %(number)s
                """
            select_values = {'vin': vin, 'number': number}
            cursor.execute(select_query, select_values)
            existing_records = cursor.fetchall()

            if not existing_records:
                insert_query = """
                                            INSERT INTO lot_qatar (
                                                price, vin, title, number, auction, country, branch, dealer, pos, date, time,
                                                docks, loss, crush, second_crush, state, odometer, retail, fix,
                                                type_auto, year, mark, model, color, body, drive, fuel, engine, transmission, url_cars
                                            )
                                            VALUES (
                                                %(price)s, %(vin)s, %(title)s, %(number)s, %(auction)s, %(country)s, %(branch)s, %(dealer)s,
                                                %(pos)s, %(date)s, %(time)s, %(docks)s, %(loss)s, %(crush)s, %(second_crush)s, %(state)s,
                                                %(odometer)s, %(retail)s, %(fix)s, %(type_auto)s, %(year)s, %(mark)s, %(model)s, %(color)s,
                                                %(body)s, %(drive)s, %(fuel)s, %(engine)s, %(transmission)s, %(url_cars)s
                                            )
                                        """

                insert_values = {
                    'price': price, 'vin': vin, 'title': title, 'number': number, 'auction': auction,
                    'country': country,
                    'branch': branch, 'dealer': dealer, 'pos': pos, 'date': date, 'time': time, 'docks': docks,
                    'loss': loss, 'crush': crush, 'second_crush': second_crush, 'state': state, 'odometer': odometer,
                    'retail': retail, 'fix': fix, 'type_auto': type_auto, 'year': year, 'mark': mark, 'model': model,
                    'color': color, 'body': body, 'drive': drive, 'fuel': fuel, 'engine': engine,
                    'transmission': transmission, 'url_cars': ', '.join(image_urls)[:2000]
                }

                cursor.execute(insert_query, insert_values)
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{insert_values}_записаны в таблицу")
            else:
                print(f"Аукцион_{auction}_{datetime.datetime.now()}_{select_values}_присутствует_в_БД")
                await write_bad_url(link)
            conn.commit()
        """Выкачка фото"""
        # folder_name = number
        # folder_path = os.path.join(f"/var/www/www-root/data/www/vinhistory.bid/uploads/images/{auction}", folder_name)
        # if not os.path.exists(folder_path):
        #     os.makedirs(folder_path)
        # for url in image_urls:
        #     async with session.get(url) as response:
        #         if response.status == 200:
        #             image_name = url.split("/")[-1]
        #             file_name, _ = os.path.splitext(image_name)
        #             file_path = os.path.join(folder_path, f'{file_name}.jpg')
        #             if os.path.exists(file_path):
        #                 continue
        #             try:
        #                 with open(file_path, "wb") as file:
        #                     while True:
        #                         chunk = await response.content.read(1024)
        #                         if not chunk:
        #                             break
        #                         file.write(chunk)
        #             except:
        #                 pass
        cursor.close()
        conn.close()


async def main():
    while True:
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="car_db_user_001",
                password="wE8wH9jA3jfC5hK6hY6j",
                database="lot_database"
            )
            cursor = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS lot_copart (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_iaai (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_impact (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_emirates_auction (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_auction_wini (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_uk (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_mea (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_us (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_ca (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_gb (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_ie (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_ae (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_om (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_copart_bh (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_iaai_uk (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_iaai_us (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_iaai_ca (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_iaai_gb (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_iaai_ae (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_iaai_qa (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_impact_ca (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_impact_gb (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_usa (
                price DECIMAL(10, 2),
                vin VARCHAR(255),
                title VARCHAR(255),
                number INT,
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date DATE,
                time TIME,
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer INT,
                retail DECIMAL(10, 2),
                fix DECIMAL(10, 2),
                type_auto VARCHAR(255),
                year INT,
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_canada (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_great_britain (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_ireland (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_uae (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_oman (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_bahrain (
                price DECIMAL(10, 2),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_korea (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            CREATE TABLE IF NOT EXISTS lot_qatar (
                price VARCHAR(255),
                vin VARCHAR(255),
                title VARCHAR(255),
                number VARCHAR(255),
                auction VARCHAR(255),
                country VARCHAR(255),
                branch VARCHAR(255),
                dealer VARCHAR(255),
                pos VARCHAR(255),
                date VARCHAR(255),
                time VARCHAR(255),
                docks VARCHAR(255),
                loss VARCHAR(255),
                crush VARCHAR(255),
                second_crush VARCHAR(255),
                state VARCHAR(255),
                odometer VARCHAR(255),
                retail VARCHAR(255),
                fix VARCHAR(255),
                type_auto VARCHAR(255),
                year VARCHAR(255),
                mark VARCHAR(255),
                model VARCHAR(255),
                color VARCHAR(255),
                body VARCHAR(255),
                drive VARCHAR(255),
                fuel VARCHAR(255),
                engine VARCHAR(255),
                transmission VARCHAR(255),
                url_cars VARCHAR(4000)
            );
            """

            async for link in get_links():
                await process_link(link)

            conn.close()

        except (aiohttp.ClientError, mysql.connector.Error) as e:
            print(f"Произошла ошибка: {str(e)}")
            traceback.print_exc()
            print("Продолжение работы...")

        except Exception as e:
            print(f"Произошла неизвестная ошибка: {str(e)}")
            traceback.print_exc()
            print("Продолжение работы...")

        await asyncio.sleep(10)


# Запуск асинхронной функции
asyncio.run(main())
