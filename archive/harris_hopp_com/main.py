import csv
import glob
import json
import os
import random
import shutil
import sys
import time
from datetime import datetime
from tkinter import NO, N

import requests

current_directory = os.getcwd()
# Создайте полный путь к папке temp
temp_path = os.path.join(current_directory, "temp")
pages_path = os.path.join(temp_path, "pages")
ads_path = os.path.join(temp_path, "ads")


def load_config():
    if getattr(sys, "frozen", False):
        # Если приложение 'заморожено' с помощью PyInstaller
        application_path = os.path.dirname(sys.executable)
    else:
        # Обычный режим выполнения (например, во время разработки)
        application_path = os.path.dirname(os.path.abspath(__file__))

    filename_config = os.path.join(application_path, "config.json")

    with open(filename_config, "r") as config_file:
        config = json.load(config_file)

    return config


def creative_temp_folders():
    for folder in [temp_path, pages_path, ads_path]:
        if not os.path.exists(folder):
            os.makedirs(folder)


def delete_old_data():
    # Проверка существования директории и её удаление
    if os.path.exists(temp_path) and os.path.isdir(temp_path):
        try:
            shutil.rmtree(temp_path)
        except Exception as e:
            print(f"Failed to delete the directory {temp_path}. Reason: {e}")
    else:
        print(f"The directory {temp_path} does not exist or is not a directory.")


def ger_totalrecords():
    config = load_config()
    headers = config.get("headers", {})
    id_city = config.get("id_city", "")

    params = {
        "query": "",
        "page": "1",
        "pagesize": "50",
    }

    json_data = {
        "filters": {
            "sale": {
                "price": {
                    "start": "",
                    "end": "",
                },
                "date": {
                    "start": "",
                    "end": "",
                },
            },
            "land": {
                "area": {
                    "start": "",
                    "end": "",
                },
                "type": [],
            },
            "building": {
                "area": {
                    "start": "",
                    "end": "",
                },
                "style": [],
                "bedrooms": "",
                "bathrooms": "",
                "ownership": [],
            },
        },
    }
    response = requests.post(
       f"https://harris-hopp.com:8086/api/propertysearch/{id_city}",
        params=params,
        headers=headers,
        json=json_data,
    )
    json_data = response.json()
    pages = int(json_data["Pages"])

    return pages


def get_all_pages():
    config = load_config()
    headers = config.get("headers", {})
    time_a = config.get("time_a", "")
    time_b = config.get("time_b", "")
    id_city = config.get("id_city", "")
    pages = ger_totalrecords()
    for page in range(1, pages + 1):
        params = {
            "query": "",
            "page": page,
            "pagesize": "50",
        }

        json_data = {
            "filters": {
                "sale": {
                    "price": {
                        "start": "",
                        "end": "",
                    },
                    "date": {
                        "start": "",
                        "end": "",
                    },
                },
                "land": {
                    "area": {
                        "start": "",
                        "end": "",
                    },
                    "type": [],
                },
                "building": {
                    "area": {
                        "start": "",
                        "end": "",
                    },
                    "style": [],
                    "bedrooms": "",
                    "bathrooms": "",
                    "ownership": [],
                },
            },
        }
        filename_page = os.path.join(pages_path, f"page_{page}.json")
        if not os.path.exists(filename_page):
            response = requests.post(
                f"https://harris-hopp.com:8086/api/propertysearch/{id_city}",
                params=params,
                headers=headers,
                json=json_data,
            )
            json_data = response.json()
            with open(filename_page, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            sleep_time = random.randint(time_a, time_b)
            time.sleep(sleep_time)


def scrap_pages():
    filename_pages = os.path.join(pages_path, "*.json")
    filenames = glob.glob(filename_pages)
    all_account = []
    for filename in filenames:
        with open(filename, "r", encoding="utf-8") as f:
            data_json = json.load(f)
        json_search = data_json["SearchProperties"]
        for search in json_search:
            account = search["Account"]
            all_account.append(account)
    return all_account


def get_all_ads():
    all_account = scrap_pages()
    config = load_config()
    headers = config.get("headers", {})
    time_a = config.get("time_a", "")
    time_b = config.get("time_b", "")
    city = config.get("city", "")
    for accounts in all_account:
        params = {
            "city": city,
            "state": "Maine",
        }
        filename_page = os.path.join(ads_path, f"ads_{accounts}.json")
        if not os.path.exists(filename_page):
            response = requests.get(
                f"https://harris-hopp.com:8086/api/fullproperty/{accounts}",
                params=params,
                headers=headers,
            )
            json_data = response.json()
            with open(filename_page, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            sleep_time = random.randint(time_a, time_b)
            time.sleep(sleep_time)


def scrap_ads():
    filename_pages = os.path.join(ads_path, "*.json")
    filenames = glob.glob(filename_pages)
    heandler = ["Account", "Map/Lot", "Type", "Units"]
    with open("Additional+Assessments.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for filename in filenames:
            with open(filename, "r", encoding="utf-8") as f:
                data_json = json.load(f)
            if data_json.get("BuildingAdditions", None):
                additional_assessments = data_json.get("BuildingAdditions", [])
                for aa in additional_assessments:
                    account = aa.get("Account", None)
                    maplot = data_json.get("MapLot", None)
                    additiontype = aa.get("AdditionType", None)
                    units = aa.get("Units", None)
                    values = [account, maplot, additiontype, units]
                    writer.writerow(values)  # Дописываем значения из values
    heandler = [
        "Propty address",
        "Owner Name1",
        "Owner Name2",
        "Owner address",
        "CityStateZip",
        "Map/Lot",
        "Account",
        "Land",
        "Building",
        "Exempt",
        "Taxable",
        "Sales Date",
        "Sales Price",
        "Book & Page",
        "Sale Type",
        "Land Code",
        "Building Code",
        "Total Acreage",
        "Zone",
        "Type",
        "Area",
        "Attic",
        "Bath Style",
        "Building Units",
        "Condition",
        "Cool Type",
        "Economic Code",
        "Economic Percent Good",
        "Construction Grade",
        "Factor",
        "Finished Basement Grade",
        "Finished Basement Factor",
        "Foundation",
        "Heat Type",
        "Insulation",
        "Kitchen Style",
        "Layout",
        "Number of Additional Fixtures",
        "Number of Bedrooms",
        "Number of Fireplaces",
        "Number of Full Baths",
        "Number of Half Baths",
        "Number of Rooms",
        "Percent Heated",
        "Roof Surface",
        "Square Foot Basement Living",
        "Stories",
    ]
    with open("info.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=";")
        writer.writerow(heandler)  # Записываем заголовки только один раз
        for filename in filenames:
            with open(filename, "r", encoding="utf-8") as f:
                data_json = json.load(f)

            streetname = data_json["StreetName"]
            streetnumber = data_json["StreetNumber"]
            street = f"{streetnumber} {streetname}"

            owner_dict = data_json.get("Owners", [])
            first_owner = None
            second_owner = None
            formatted_date = None
            formatted_sales = None
            formatted_area = None
            formatted_percentheated = None
            formatted_economicpercent = None
            ownername_02 = None
            book_page = None
            formatted_building = None
            # Проверяем, есть ли элементы в списке
            if len(owner_dict) > 0:
                first_owner = owner_dict[0]  # Безопасно получаем первого владельца
            if len(owner_dict) > 1:
                second_owner = owner_dict[1]  # Безопасно получаем второго владельца

            # Инициализация переменных для хранения данных
            # ownername_01 = ownername_02 = owneraddress = city = state = zipcode = cityStateZipcode = None

            if first_owner:
                ownername_01 = first_owner.get("OwnerName", None)
                owneraddress = first_owner.get("Address1", None)
                city = first_owner.get("City", None)
                state = first_owner.get(
                    "State", None
                )  # Предполагается, что должно быть State
                zipcode = first_owner.get("ZipCode", None)
                cityStateZipcode = f"{city}, {state} {zipcode}"

            if second_owner:
                ownername_02 = second_owner.get("OwnerName", None)
            maplot = data_json.get("MapLot", None)
            account = data_json.get("Account", None)
            landvalue = data_json.get("LandValue", None)
            # Проверяем, что landvalue не None и является числом
            if landvalue is not None and isinstance(landvalue, int):
                # Форматируем значение с разделителем тысяч и добавляем символ доллара
                formatted_landvalue = "${:,.0f}".format(landvalue).replace(",", " ")
            else:
                formatted_landvalue = None

            totalexemption = data_json.get("TotalExemption", None)

            if totalexemption is not None and isinstance(totalexemption, int):
                # Форматируем значение с разделителем тысяч и добавляем символ доллара
                formatted_totalexemption = "${:,.0f}".format(totalexemption).replace(
                    ",", " "
                )
            else:
                formatted_totalexemption = None

            taxable = data_json.get("Taxable", None)
            if taxable is not None and isinstance(taxable, int):
                # Форматируем значение с разделителем тысяч и добавляем символ доллара
                formatted_taxable = "${:,.0f}".format(taxable).replace(",", " ")
            else:
                formatted_taxable = None

            buildings_dict = data_json.get("Buildings", [])

            if buildings_dict:  # Если список не пуст
                first_building = buildings_dict[0]

                buildingtype = first_building.get("BuildingType", None)
                area = first_building.get("Area", None)
                area = float(first_building.get("Area", None))
                if area is not None and (
                    isinstance(area, int) or isinstance(area, float)
                ):
                    # Форматируем значение с добавлением "sqft" на конце
                    formatted_area = f"{area} sqft"
                else:
                    formatted_area = None

                attic = first_building.get("Attic", None)
                bathstyle = first_building.get("BathStyle", None)
                dwellingunits = first_building.get("DwellingUnits", None)
                condition = first_building.get("Condition", None)
                cooltype = first_building.get("CoolType", None)
                economiccode = first_building.get("EconomicCode", None)
                economicpercent = float(first_building.get("EconomicPercent", None))
                if economicpercent is not None and (
                    isinstance(economicpercent, int)
                    or isinstance(economicpercent, float)
                ):
                    # Форматируем значение с добавлением символа процента на конце
                    formatted_economicpercent = f"{economicpercent}%"
                else:
                    formatted_economicpercent = None
                grade = first_building.get("Grade", None)
                factor = first_building.get("Factor", None)
                finishedbasementgrade = first_building.get(
                    "FinishedBasementGrade", None
                )
                finishedbasementfactor = first_building.get(
                    "FinishedBasementFactor", None
                )
                foundation = first_building.get("Foundation", None)
                heattype = first_building.get("HeatType", None)
                insulation = first_building.get("Insulation", None)
                kitchenstyle = first_building.get("KitchenStyle", None)
                layout = first_building.get("Layout", None)
                numberofadditionalfixtures = first_building.get(
                    "NumberOfAdditionalFixtures", None
                )
                bedrooms = first_building.get("Bedrooms", None)
                fireplaces = first_building.get("Fireplaces", None)
                fullbaths = first_building.get("FullBaths", None)
                halfbaths = first_building.get("HalfBaths", None)

                rooms = first_building.get("Rooms", None)

                percentheated = float(first_building.get("PercentHeated", None))
                if percentheated is not None and (
                    isinstance(percentheated, int) or isinstance(percentheated, float)
                ):
                    # Форматируем значение с добавлением символа процента на конце
                    formatted_percentheated = f"{percentheated}%"
                else:
                    formatted_percentheated = None
                roofsurface = first_building.get("RoofSurface", None)
                squarefootbasementliving = first_building.get(
                    "SquareFootBasementLiving", None
                )
                buildingstories = first_building.get("BuildingStories", None)

            else:
                # Установка всех значений в None, если список пуст
                buildingtype = None
                area = None
                attic = None
                bathstyle = None
                dwellingunits = None
                condition = None
                cooltype = None
                economiccode = None
                formatted_economicpercent = None
                grade = None
                factor = None
                finishedbasementgrade = None
                finishedbasementfactor = None
                foundation = None
                heattype = None
                insulation = None
                kitchenstyle = None
                layout = None
                numberofadditionalfixtures = None
                bedrooms = None
                fireplaces = None
                fullbaths = None
                halfbaths = None
                rooms = None
                formatted_percentheated = None
                roofsurface = None
                squarefootbasementliving = None
                buildingstories = None

            saletype_dict = data_json.get("Sales", [])
            if saletype_dict:  # Если список не пуст
                first_saletype = saletype_dict[0]
                saletype = first_saletype.get("SaleType", None)
                sales_date = first_saletype.get("SaleDate", None)
                date_obj = datetime.strptime(sales_date, "%Y-%m-%dT%H:%M:%S")
                formatted_date = (
                    date_obj.strftime("%m/%d/%Y").replace("/0", "/").lstrip("0")
                )

                sales_price = first_saletype.get("SalePrice", None)
                if sales_price is not None and isinstance(sales_price, (int, float)):
                    # Форматируем значение с разделителем тысяч и добавляем символ доллара
                    formatted_sales = "{:,.0f}$".format(sales_price).replace(",", " ")
                else:
                    formatted_sales = None

                book = first_saletype.get("Book", None)
                page = first_saletype.get("Page", None)
                if book is not None and book != "" and page != "" and page is not None:

                    book_page = f"Book: {book} Page: {page}"
                else:
                    book_page = None
            else:
                saletype = None
                sales_date = None
                sales_price = None
                book = None
                page = None

            landcode = data_json.get("LandCode", None)
            building = data_json.get("TotalBuildingValue", None)
            if building is not None and isinstance(building, int):
                # Форматируем значение с разделителем тысяч и добавляем символ доллара
                formatted_building = "${:,.0f}".format(building).replace(",", " ")
            else:
                formatted_building = None

            buildingcode = data_json.get("BuildingCode", None)
            totalacres = data_json["TotalAcres"]
            zone = data_json["Zone"]

            values = [
                street,
                ownername_01,
                ownername_02,
                owneraddress,
                cityStateZipcode,
                maplot,
                account,
                formatted_landvalue,
                formatted_building,
                formatted_totalexemption,
                formatted_taxable,
                formatted_date,
                formatted_sales,
                book_page,
                saletype,
                landcode,
                buildingcode,
                totalacres,
                zone,
                buildingtype,
                formatted_area,
                attic,
                bathstyle,
                dwellingunits,
                condition,
                cooltype,
                economiccode,
                formatted_economicpercent,
                grade,
                factor,
                finishedbasementgrade,
                finishedbasementfactor,
                foundation,
                heattype,
                insulation,
                kitchenstyle,
                layout,
                numberofadditionalfixtures,
                bedrooms,
                fireplaces,
                fullbaths,
                halfbaths,
                rooms,
                formatted_percentheated,
                roofsurface,
                squarefootbasementliving,
                buildingstories,
            ]
            writer.writerow(values)  # Дописываем значения из values


# if __name__ == "__main__":
#     creative_temp_folders()
#     get_all_pages()
#     get_all_ads()
#     scrap_ads()


if __name__ == "__main__":
    while True:
        # Запрос ввода от пользователя
        print(
            "Введите 1 для всех страниц сайта"
            "\nВведите 2 получения всех объявлений"
            "\nВведите 3 получаем csv"
            "\nВведите 9 для удаления временных файлов"
            "\nВведите 0 для закрытия программы"
        )
        user_input = int(input("Выберите действие: "))

        if user_input == 1:
            creative_temp_folders()
            get_all_pages()
            print("Получили все страницы \nПереходим к пункту 2")
        elif user_input == 2:

            get_all_ads()
            print("Получили все объявления \nПереходим к пункту 3")
        elif user_input == 3:
            scrap_ads()
            print("Файлы готовы \nПроверяйте данные")
        elif user_input == 9:
            delete_old_data()
            print("Файлы удалены, программа закрывается")
            break  # Выход из цикла, завершение программы
        elif user_input == 0:
            print("Программа завершена.")
            break  # Выход из цикла, завершение программы
        else:
            print("Неверный ввод, пожалуйста, введите корректный номер действия.")
