import telegram
import asyncio
from telegram.error import BadRequest

# указываем токен бота и создаем объект bot
bot = telegram.Bot(token='6211681959:AAHobX_RZaxpm5ON_dER547hRU0tOFQrfrY')

async def get_chat_title(chat_id):
    chat = await bot.get_chat(chat_id=chat_id)
    chat_title = chat.title
    return chat_title

async def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    chat_title = await get_chat_title('-1001747602328')
    print(chat_title)

if __name__ == '__main__':
    asyncio.run(main())


#
# async def get_chat_title(chat_id):
#     chat = await bot.get_chat(chat_id=chat_id)
#     chat_title = chat.title
#     return chat_title
#
# loop = asyncio.get_event_loop()
# chat_title = loop.run_until_complete(get_chat_title('1001747602328'))
#
# print(chat_title)