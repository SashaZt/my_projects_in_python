import requests

# r = requests.post(
#     url="https://async.scraperapi.com/jobs",
#     json={"apiKey": "5edddbdddb89aed6e9d529c4ff127e8f", "url": "https://allegro.pl/"},
# )
# print(r.text)


r = requests.get(
    url="https://async.scraperapi.com/jobs/f3ec1d14-6842-4edb-8d2d-765347ba6349"
)
print(r.text)
