import requests
import json
import urllib.parse


def make_request(base_url, params):
    """Делает HTTP запрос и возвращает JSON"""
    try:
        # Кодируем параметры, заменяя '+' на '%20' для пробелов
        query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        url = f"{base_url}?{query_string}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None


def save_json(data, filename):
    """Сохраняет данные в JSON файл"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    base_url = "https://allegro.parser.best/allegro/parser.php"

    # Задаем параметры отдельно
    params = {
        "category": "255099",
        "page": "1",
        "api_key": "xHt2mU3v6qHtm62XG6cJ",
        "method": "search",
        "sort": "",
        "query": "audi A8 D4",
        "price_from": "50",
    }

    # Делаем первый запрос
    initial_response = make_request(base_url, params)
    if not initial_response or not initial_response.get("success"):
        print("Ошибка начального запроса")
        return

    # Получаем категорию и последнюю доступную страницу
    category = params.get("category")
    last_page = initial_response.get("lastAvailablePage", 1)

    # Сохраняем первый ответ
    filename = f"{category}_01.json"
    save_json(initial_response, filename)
    print(f"Сохранен файл: {filename}")

    # Обрабатываем остальные страницы
    for page in range(2, last_page + 1):
        # Обновляем параметр page
        params["page"] = str(page)

        # Делаем запрос
        response = make_request(base_url, params)
        if response and response.get("success"):
            # Формируем имя файла (01, 02, ..., 08)
            filename = f"{category}_{str(page).zfill(2)}.json"
            save_json(response, filename)
            print(f"Сохранен файл: {filename}")
        else:
            print(f"Ошибка при запросе страницы {page}")


if __name__ == "__main__":
    main()
