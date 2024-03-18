import json

import requests
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hbold, hunderline, hcode, hlink
from bs4 import BeautifulSoup
from aiogram.dispatcher.filters import Text
from fake_useragent import UserAgent

from config import TOKEN_API

useragent = UserAgent()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot)


#
# @dp.message_handler(commands='start')
# async def echo(message: types.Message):
#     url = 'https://vehiclebid.info/ru/search?page=4002'
#     header = {
#         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
#         "user-agent": f"{useragent.random}"
#     }
#     session = requests.Session()
#     session.proxies = {
#         'http': 'http://80.77.34.218:9999',
#         'https': 'http://80.77.34.218:9999',
#     }
#     resp = session.get(url, headers=header)
#     soup = BeautifulSoup(resp.text, 'lxml')
#     # Получаем таблицу всех товаров
#     table = soup.find('div', attrs={'class': 'chakra-stack css-owjkmg'}).find_all('a')
#     # Получаем список всех url на карточки
#     for item in table:
#         url_cart = item.find('img').get('src')
#         name_cart = item.find('div', attrs={'class': 'chakra-card__body css-1idwstw'}).find('h2', attrs={
#             'class': 'chakra-heading css-18j379d'}).text
#         vin_cart = item.find('div', attrs={'class': 'chakra-card__body css-1idwstw'}).find('p', attrs={
#             'class': 'chakra-text css-0'}).text
#         car_dict = {
#             'url_cart': url_cart,
#             'name_cart': name_cart,
#             'vin_cart': vin_cart
#         }
#         with open("card.json", 'a') as file:
#             json.dump(car_dict, file, indent=4, ensure_ascii=False)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    start_buttons = ['ACURA', 'ALFA Romeo', 'ASTON MARTTIN', 'AUDI']
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)

    await message.answer('Выберите категорию', reply_markup=keyboard)
    # with open('card.json', encoding='utf-8') as file:
    #     dict_car = json.load(file)
    # # print(dict_car)
    # for v in dict_car[0:1]:
    #     list_car = f"{v['url_cart']}\n" \
    #                f"{v['name_cart']}\n" \
    #                f"{v['vin_cart']}\n" \
    #                f"{v['lot_cart']}\n" \
    #                f"{v['data_cart']}\n" \
    #                f"{v['speed_cart']}\n" \
    #                f"{v['price_cart']}\n"
    #
    #     await message.answer(list_car)


@dp.message_handler(Text(equals='ACURA'))
async def get_discount_acura(message: types.Message):
    await message.answer('Подождите пожалуйста...')


if __name__ == '__main__':
    executor.start_polling(dp)
