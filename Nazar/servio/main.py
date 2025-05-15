import json
import re
import sys

from bs4 import BeautifulSoup


def extract_guest_table(json_data):
    """
    Извлекает HTML-таблицу tlbLivingGuests из JSON-строки.
    """
    try:
        # Парсим JSON
        data = json.loads(json_data)
        html_content = data.get("d", "")

        if not html_content:
            return None

        # Ищем таблицу tlbLivingGuests с помощью регулярного выражения
        # Извлекаем от <table id='tlbLivingGuests' до </table>
        pattern = r"<table id='tlbLivingGuests'.*?</table>"
        match = re.search(pattern, html_content, re.DOTALL)

        if match:
            return match.group(0)
        else:
            return None
    except json.JSONDecodeError:
        print("Ошибка: Неверный формат JSON")
        return None


def parse_guest_data(html_table):
    """
    Парсит HTML-таблицу tlbLivingGuests и возвращает список словарей с данными гостей.
    """
    if not html_table:
        return []

    # Парсим HTML с помощью BeautifulSoup
    soup = BeautifulSoup(html_table, "lxml")

    # Находим таблицу
    table = soup.find("table", id="tlbLivingGuests")
    if not table:
        return []

    # Получаем все строки таблицы, кроме заголовка
    rows = table.find_all("tr", class_="notfirstrow")

    # Список для хранения результатов
    guests = []

    # Обрабатываем каждую строку
    for row in rows:
        # Проверяем, что это не групповая бронь (нет префикса G в номере счета)
        account_cell = row.find("td", {"valign": "middle", "align": "left"})
        if not account_cell or account_cell.find("span").text.startswith("G"):
            continue

        # Получаем все ячейки строки
        cells = row.find_all("td")
        if len(cells) < 18:  # Проверяем, что строка содержит достаточно ячеек
            continue

        # Извлекаем данные
        guest = {
            "№": cells[0].text.strip(),
            "О/рахунок": (
                cells[1].find("span").text.strip() if cells[1].find("span") else ""
            ),
            "Готель": (
                cells[2].find("span", id="lblHotel").text.strip()
                if cells[2].find("span", id="lblHotel")
                else ""
            ),
            "ПІБ": "",
            "Заїзд": cells[4].text.strip(),
            "Виїзд": cells[5].text.strip(),
            "Др/Дт/ДО": cells[6]
            .text.strip()
            .replace("</span>", "")
            .replace("<span>", ""),
            "Кат.": (
                cells[7].find("span", id="lblAgentAccountCategory").text.strip()
                if cells[7].find("span", id="lblAgentAccountCategory")
                else ""
            ),
            "Комент.": (
                cells[8].find("span", id="lblComment").text.strip()
                if cells[8].find("span", id="lblComment")
                else ""
            ),
            "До спл., грн.": cells[9].text.strip(),
            "Кімн.": "",
            "Прайс.": (
                cells[11].find("span", id="lblPriceList").text.strip()
                if cells[11].find("span", id="lblPriceList")
                else ""
            ),
            "Компанія-оператор": cells[12].text.strip(),
            "Група": cells[13].text.strip(),
            "Гр.": (
                cells[14].find("span", id="lblCountry").text.strip()
                if cells[14].find("span", id="lblCountry")
                else ""
            ),
            "Статус": (
                cells[15].find("span", id="lblStatus").text.strip()
                if cells[15].find("span", id="lblStatus")
                else ""
            ),
            "Тип опл.": cells[16].text.strip(),
        }

        # Формируем поле ПІБ (ФИО + телефон)
        name = (
            cells[3].find("span", id="lblGuestName").text.strip()
            if cells[3].find("span", id="lblGuestName")
            else ""
        )
        phone = (
            cells[3].find("span", id="lblContactPhone").text.strip()
            if cells[3].find("span", id="lblContactPhone")
            else ""
        )
        guest["Телефон"] = phone.strip()
        guest["ПІБ"] = f"{name}".strip()

        # Формируем поле Кімн. (номер комнаты + тип номера)
        room_number = cells[10].find("b").text.strip() if cells[10].find("b") else ""
        room_type = (
            cells[10].find("span", id="lblRoomType").text.strip()
            if cells[10].find("span", id="lblRoomType")
            else ""
        )
        guest["Кімн."] = f"{room_number} {room_type}".strip()

        # Добавляем гостя в список
        guests.append(guest)

    return guests


# Пример использования
if __name__ == "__main__":
    # Пример JSON-данных (вставь свои данные)
    try:
        # Читаем JSON из файла
        with open("test.json", "r", encoding="utf-8") as file:
            json_data = file.read()

        # Извлекаем HTML-таблицу
        html_table = extract_guest_table(json_data)

        if not html_table:
            print("Ошибка: Не удалось извлечь таблицу tlbLivingGuests")
            sys.exit(1)

        # Парсим данные гостей
        guests = parse_guest_data(html_table)

        # Выводим результат (первые 5 записей для примера)
        for guest in guests[:5]:
            print(guest)

        # Выводим общее количество записей
        print(f"\nВсего обработано гостей: {len(guests)}")

    except Exception as e:
        print(f"Ошибка: {str(e)}")
