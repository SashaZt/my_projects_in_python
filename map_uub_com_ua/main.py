import requests
import json
import pandas as pd

headers = {
    "accept": "*/*",
    "accept-language": "uk",
    "cache-control": "no-cache",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://map.uub.com.ua/client",
    "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "same-origin",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "x-csrftoken": "undefined",
    "x-requested-with": "XMLHttpRequest",
}

params = ""


# занимается только взаимодействием с API
class CompanyAPI:
    def __init__(self, headers, params) -> None:
        self.headers = headers
        self.params = params

    # получение списка компаний
    def get_list_company(self):
        response = requests.get(
            "https://map.uub.com.ua/api/v1/catalog/elevator/list/",
            params=self.params,
            headers=self.headers,
        )
        # Проверка кода ответа
        if response.status_code == 200:
            json_data = response.json()
            all_companies = json_data.get("data", {}).get("items", [])
            company_labels = [
                company.get("label", "")
                for company in all_companies
                if isinstance(company, dict)
            ]
            return company_labels
        return None

    # данных по каждой компании
    def get_company_data(self, company_label):
        response = requests.get(
            f"https://map.uub.com.ua/api/v1/catalog/elevator/{company_label}/retrieve/",
            headers=self.headers,
        )
        if response.status_code == 200:
            return response.json()
        return None


class DataProcessor:
    def __init__(self, headers, params) -> None:
        self.api = CompanyAPI(headers, params)

    def process_companies(self):
        company_labels = self.api.get_list_company()
        if not company_labels:
            return []

        all_results = []
        for company in company_labels:
            json_data = self.api.get_company_data(company)
            if json_data:
                result_dict = self._parse_company_data(json_data)
                all_results.append(result_dict)
        return all_results

    def _parse_company_data(self, json_data):
        item_data = json_data.get("data", {}).get("item", {})
        shipments = item_data.get("shipments", [])

        shipment_avto = (
            "+" if any(s.get("title", "") == "Авто" for s in shipments) else None
        )
        shipment_zd = (
            "+" if any(s.get("title", "") == "З/д" for s in shipments) else None
        )

        # Безопасное извлечение "E-mail"
        emails = item_data.get("json_emails", [])
        email_title = (
            emails[0].get("title", "") if emails and isinstance(emails[0], dict) else ""
        )

        result_dict = {
            "Компанія": item_data.get("owner", ""),
            "Зберігання, тон": item_data.get("storage", 0),
            "ЕДРПОУ": item_data.get("register_code", ""),
            "Відвантаження авто": shipment_avto,
            "Відвантеження з/д": shipment_zd,
            "Назва елеватора": item_data.get("company", ""),
            "Область": item_data.get("location_description", ""),
            "Адреса": item_data.get("address", ""),
            "Контакти": item_data.get("contacts", ""),
            "E-mail": email_title,
        }
        return result_dict

    def write_to_excel(self, all_results):
        if not all_results:
            print("Нет данных для записи.")
            return

        df = pd.DataFrame(all_results)
        df.to_excel("output.xlsx", index=False, sheet_name="Data")


# Пример использования
processor = DataProcessor(headers, params)
all_results = processor.process_companies()
processor.write_to_excel(all_results)
