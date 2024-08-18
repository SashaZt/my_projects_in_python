import requests
import json
from configuration.logger_setup import logger

cookies = {
    "gk_suid": "49043625",
    "OptanonAlertBoxClosed": "2024-05-01T10:32:14.248Z",
    "OptanonConsent": "groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1",
    "gki": "feature_search_gk_debug: false, list_keyboard_nav: false,",
    "bcp": "4a40d28e-8255-42e6-8cee-b1694ec50a24",
    "bcp_generated": "1723962149408",
    "_cs_mk_aa": "0.10592626189837073_1723964158532",
    "gpv": "behance.net:search:users",
    "sign_up_prompt": "true",
}

headers = {
    "accept": "*/*",
    "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
    "content-type": "application/json",
    # 'cookie': 'gk_suid=49043625; OptanonAlertBoxClosed=2024-05-01T10:32:14.248Z; OptanonConsent=groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1; gki=feature_search_gk_debug: false, list_keyboard_nav: false,; bcp=4a40d28e-8255-42e6-8cee-b1694ec50a24; bcp_generated=1723962149408; _cs_mk_aa=0.10592626189837073_1723964158532; gpv=behance.net:search:users; sign_up_prompt=true',
    "dnt": "1",
    "origin": "https://www.behance.net",
    "priority": "u=1, i",
    "referer": "https://www.behance.net/search/users/design%20graphic%20designer?country=US",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "x-bcp": "4a40d28e-8255-42e6-8cee-b1694ec50a24",
    "x-newrelic-id": "VgUFVldbGwsFU1BRDwUBVw==",
    "x-requested-with": "XMLHttpRequest",
}


def get_html():
    response = requests.get(
        "https://www.behance.net/linnaadesign", cookies=cookies, headers=headers
    )

    # Проверка кода ответа
    if response.status_code == 200:
        # Сохранение HTML-страницы целиком
        with open("proba.html", "w", encoding="utf-8") as file:
            file.write(response.text)
    print(response.status_code)


def get_json():
    json_data = {
        "query": "\n      query GetUserSearchResults($query: query, $filter: SearchResultFilter, $first: Int! = 48, $after: String) {\n        search(query: $query, type: USER, filter: $filter, first: $first, after: $after, alwaysHasNext: true) {\n          pageInfo {\n            hasNextPage\n            endCursor\n          }\n          nodes {\n            ... on User {\n              __typename\n              id\n              firstName\n              username\n              url\n              isProfileOwner\n              isFeaturedFreelancer\n              isResponsiveToHiring\n              country\n              images {\n                size_50 {\n                  ...ImageFields\n                }\n                size_100 {\n                  ...ImageFields\n                }\n                size_115 {\n                  ...ImageFields\n                }\n                size_230 {\n                  ...ImageFields\n                }\n                size_138 {\n                  ...ImageFields\n                }\n                size_276 {\n                  ...ImageFields\n                }\n              }\n              displayName\n              location\n              creativeFields {\n                name\n                id\n                url\n              }\n              isFollowing\n              allowsContactFromAnyone\n              subscriptionProduct {\n                unitAmount\n                currency\n              }\n              isMessageButtonVisible\n              availabilityInfo {\n                isAvailableFullTime\n                isOpenToRelocation\n                isLookingForRemote\n                isAvailableFreelance\n                compensationMin\n                currency\n                availabilityTimeline\n                buttonCTAType\n                hiringTimeline {\n                  key\n                  label\n                }\n              }\n              stats {\n                appreciations\n                views\n                followers\n              }\n              projects(first: 5) {\n                nodes {\n                  url\n                  slug\n                  covers {\n                    size_202 {\n                      url\n                    }\n                    size_404 {\n                      url\n                    }\n                    size_808 {\n                      url\n                    }\n\n                    size_202_webp {\n                      url\n                    }\n                    size_404_webp {\n                      url\n                    }\n                    size_max_808_webp {\n                      url\n                    }\n                  }\n                }\n              }\n              freelanceProjectUserInfo {\n                ...reviewsFields\n              }\n              ...creatorProBadgeFields\n            }\n          }\n          metaContent {\n            totalEntityCount\n            csam {\n              isCSAMViolation\n              description\n              helpResource\n              reportingOption\n            }\n          }\n        }\n      }\n      fragment ImageFields on ImageRendition {\n        url\n        width\n        height\n      }\n      \n  fragment reviewsFields on FreelanceProjectUserInfo {\n    completedProjectCount\n    completedProjects {\n      id\n      modifiedOn\n      status\n      hirer {\n        username\n        displayName\n        id\n        images {\n          size_230 {\n            url\n          }\n        }\n        url\n      }\n      creator {\n        username\n        displayName\n        id\n        images {\n          size_230 {\n            url\n          }\n        }\n        url\n      }\n    }\n    reviews {\n      review\n      id\n      freelanceProject {\n        id\n        status\n        modifiedOn\n      }\n      reviewer {\n        id\n        username\n        displayName\n        id\n        images {\n          size_230 {\n            url\n          }\n        }\n        url\n      }\n    }\n  }\n\n      \n  fragment creatorProBadgeFields on User {\n    creatorPro {\n      initialSubscriptionDate\n      isActive\n    }\n  }\n\n    ",
        "variables": {
            "query": "design graphic designer",
            "filter": {
                "country": "US",
            },
            "first": 48,
            "after": "NzI=",
        },
    }

    response = requests.post(
        "https://www.behance.net/v3/graphql",
        cookies=cookies,
        headers=headers,
        json=json_data,
    )

    # Проверка кода ответа
    if response.status_code == 200:
        json_data = response.json()
        # filename = os.path.join(json_path, f"0.json")
        with open("proba.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)  # Записываем в файл
    else:
        print(response.status_code)


def download_xml():
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "ru,en-US;q=0.9,en;q=0.8,uk;q=0.7,de;q=0.6",
        "cache-control": "no-cache",
        "dnt": "1",
        "pragma": "no-cache",
        "priority": "u=0, i",
        "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    }
    save_path = "image_sitemap_00006.xml"
    url = "https://zorrov.com/image_sitemap_00006.xml"
    # Отправка GET-запроса на указанный URL
    response = requests.get(url, headers=headers)

    # Проверка успешности запроса
    if response.status_code == 200:
        # Сохранение содержимого в файл
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"Файл успешно сохранен в: {save_path}")
    else:
        print(f"Ошибка при скачивании файла: {response.status_code}")


if __name__ == "__main__":
    # get_html()
    get_json()
    # download_xml()
