import requests
import json


def get_json_data():

    # url = f"https://betatransfer.io/excel/cascades/{id_accounts}/accounts"
    url = "https://betatransfer.io/excel/cascades"
    token = "pLaZ2zGFtbKt8UOdw6EAfpIBWwbsGETd"
    headers = {"Authorization": f"Basic {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        datas = response.json()
        for data in datas[:1]:
            id_cascada = data["id"]
            name_account = data["name"]
            url = (f"https://betatransfer.io/excel/cascades/698/accounts",)
            response = requests.get(url, headers=headers)
            if response.status_code == 200:

                datas = response.json()
                print(response)
            else:
                print("Failed to retrieve data:", response.status_code)

        # filename = "json_data.json"
        # with open(filename, "w", encoding="utf-8") as file:
        #     json.dump(datas, file, ensure_ascii=False, indent=4)
    else:
        print("Failed to retrieve data:", response.status_code)


def pars_json():
    filename = "json_data.json"
    with open(filename, "r", encoding="utf-8") as file:
        datas = json.load(file)
    for data in datas[:1]:
        id_cascada = data["id"]
        name_account = data["name"]


if __name__ == "__main__":
    get_json_data()
    # pars_json()
