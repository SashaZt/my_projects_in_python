import re

curl_command = """
curl -X POST 'https://www.synevo.ua/api/test/tests-by-loc' \
  -H 'Host: www.synevo.ua' \
  -H 'Connection: keep-alive' \
  -H 'Content-Length: 13' \
  -H 'sec-ch-ua: ' \
  -H 'X-CSRF-TOKEN: lqQeioTO1KWx3T3SLyFa0rKjpxw99T7ldRwRsYns' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36' \
  -H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' \
  -H 'Accept: */*' \
  -H 'X-Requested-With: XMLHttpRequest' \
  -H 'sec-ch-ua-platform: ""' \
  -H 'Origin: https://www.synevo.ua' \
  -H 'Sec-Fetch-Site: same-origin' \
  -H 'Sec-Fetch-Mode: cors' \
  -H 'Sec-Fetch-Dest: empty' \
  -H 'Referer: https://www.synevo.ua/ua/tests' \
  -H 'Accept-Encoding: gzip, deflate, br' \
  -H 'Accept-Language: ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7' \
  -H 'Cookie: cookiesession1=678A3ED6FB24570B342E4259277B8505; XSRF-TOKEN=eyJpdiI6IjlcL1FjWjNcL1wvXC8wK1Awbm40aHBrV1NBPT0iLCJ2YWx1ZSI6IldSVmd2UTVWTWJyQTd3XC9qd0JrVFN2cWw4U0daTHRobmZpTE1rQjJXQ1ZTZ0tDY3JqbGtTdkRKOFhsSFV5NVdpIiwibWFjIjoiYzM4NDQ0ZjE0OGEyZWU5MmRhYjEyZTdhNTgwMjMxMjc0ZWVmNGEwMGUwMTcyYzU4OWYxOWE1OGY2Y2UyZTM3NiJ9; laravel_session=eyJpdiI6IkE0Qm1yTk8zZ0Zvd0pUQmdaaEVqaXc9PSIsInZhbHVlIjoiXC9vY0JxQVUxTWZQR2ZTN0djSzNjTjA4TFU0VmdKb2l5VExDd0Z6SGp4UGMzOURTRjFVVFZHRlphaG9LbFJ2YmUiLCJtYWMiOiI3ZTdlZWM5OGExNjEzYzNhYjg2NzVlNGYwZTc3NWY0OWVkZWM4NmI0MTQ5YWMyYTdiNTkyZTUyODZkYWFiYTBiIn0%3D' \
"""

# Extracting cookies
cookies_match = re.search(r"Cookie:\s(.*?)'", curl_command)
if cookies_match:
    cookies_str = cookies_match.group(1)
    cookies_list = cookies_str.split('; ')
    cookies = {cookie.split('=')[0]: cookie.split('=')[1] for cookie in cookies_list}

# Extracting headers
headers_match = re.findall(r"-H '(.*?)'", curl_command)
headers = {header.split(': ')[0]: header.split(': ')[1] for header in headers_match}

print("Cookies:", cookies)
print("Headers:", headers)
