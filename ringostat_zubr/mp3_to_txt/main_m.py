import requests

api_key = "bb92ee43-b90e-4516-9483-63ae06351b64"

url = "https://api.fireflies.ai/graphql"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

query = """
data = '{"query": "query Bite($biteId: ID!) { bite(id: $biteId) { user_id name status summary } }", "variables": {"biteId": "your_bite_id"}}'
"""

response = requests.post(url, headers=headers, json={"query": query})

if response.status_code == 200:
    data = response.json()
    if "data" in data and "meetings" in data["data"]:
        for meeting in data["data"]["meetings"]:
            print(f"ID: {meeting['id']}")
            print(f"Title: {meeting['title']}")
            print(f"Date: {meeting['date']}")
            print(f"Duration: {meeting['duration']} minutes")
            print("-" * 50)
    else:
        print("Нет данных о встречах.")
else:
    print(f"Ошибка: {response.status_code}")
    print(response.text)
