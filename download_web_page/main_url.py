import urllib.parse

# Исходный URL
url = "https://auth2.ebay.com/oauth2/ThirdPartyAuthSucessFailure?isAuthSuccessful=true&code=v%5E1.1%23i%5E1%23r%5E1%23p%5E3%23I%5E3%23f%5E0%23t%5EUl41XzI6Mzk2OTBBQTU5ODU4ODE3MjkwMDVGMTk5NzBBRUFCODVfMF8xI0VeMTI4NA%3D%3D&expires_in=299"

# Парсим URL и получаем параметры
parsed_url = urllib.parse.urlparse(url)
params = urllib.parse.parse_qs(parsed_url.query)

# Извлекаем значение параметра 'code'
code = params["code"][0]

print(code)
