import requests
from config import open_weather_token
import datetime
import json
def main():
    city_z = 'Zhytomyr'
    city_n = 'Novohrad-Volynskyi'
    city_v = 'Lutsk'
    url_z = f'https://api.openweathermap.org/data/2.5/weather?q={city_z}&appid={open_weather_token}&units=metric'
    url_n = f'https://api.openweathermap.org/data/2.5/weather?q={city_n}&appid={open_weather_token}&units=metric'
    url_v = f'https://api.openweathermap.org/data/2.5/weather?q={city_v}&appid={open_weather_token}&units=metric'

    response = requests.get(url_z)

    # проверка на успешный ответ
    if response.status_code == 200:
        info = response.json()  # Парсим JSON и получаем словарь

        # сохраняем JSON в файл
        with open('output.json', 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=4)
    else:
        print(f"Error {response.status_code}: {response.text}")
def unix_time_to_datetime(unix_time):
    return datetime.datetime.fromtimestamp(unix_time)

def parsin():
    with open('output.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    weather_data = data['weather'][0]['description']
    temp_data = data['main']['temp']
    unix_time = data['dt']
    dates = unix_time_to_datetime(unix_time)
    city = data['name']
    print(weather_data, temp_data, city,dates)


if __name__ == '__main__':
    # main()
    parsin()
