import json
import os
from datetime import datetime
import glob


current_directory = os.getcwd()
temp_directory = "temp"
temp_path = os.path.join(current_directory, temp_directory)
all_hotels = os.path.join(temp_path, "all_hotels")

# Создание директории, если она не существует
os.makedirs(all_hotels, exist_ok=True)


def parsing():
    folder = os.path.join(all_hotels, "*.json")
    files_json = glob.glob(folder)
    for item in files_json[:1]:
        with open(item, "r", encoding="utf-8") as f:
            raw_json_str = f.read()
            data_json = json.loads(raw_json_str)
        for j in data_json[:1]:
            # id_blocking = j["BloczekId"]
            # basic_information = j["BazoweInformacje"]
            # imprezaid = basic_information["ImprezaID"]
            # hotelid = basic_information["HotelID"]
            # kluczprodukthotel = basic_information["KluczProduktHotel"]
            # kodproduktu = basic_information["KodProduktu"]
            # typwycieczki = basic_information["TypWycieczki"]
            # lokalizacje = basic_information["Lokalizacje"]

            basic_information = j.get("BazoweInformacje", {})
            przystanki = j.get("Przystanki", [])
            iata_codes = [przystanek["Iata"] for przystanek in przystanki if "Iata" in przystanek]

            summary_info = {
                "id_blocking": j.get("BloczekId", None),
                "basic_information": basic_information,
                "iata_codes": iata_codes,
                "imprezaid": basic_information.get("ImprezaID", None),
                "hotelid": basic_information.get("HotelID", None),
                "kluczprodukthotel": basic_information.get("KluczProduktHotel", None),
                "kodproduktu": basic_information.get("KodProduktu", None),
                "typwycieczki": basic_information.get("TypWycieczki", None),
                "lokalizacje": basic_information.get("Lokalizacje", None),
                "gwiazdkihotelu": j.get("GwiazdkiHotelu", None),
                "nazwahoteluwww": j.get("NazwaHoteluWWW", None),
                "ofertanazwa": j.get("OfertaNazwa", None),
                "params": j.get("Params", None),
            }
            with open("summary_info.json", "w", encoding="utf-8") as file:
                json.dump(summary_info, file, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    parsing()
