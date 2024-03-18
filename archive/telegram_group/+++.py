import time

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import asyncio

api_id = '8771905'
api_hash = '39debb7f571db5ad62288c20780af81c'
phone = '+380635623555'
username = 'https://t.me/milirud_official'
client = TelegramClient(phone, api_id, api_hash)

async def main():
    await client.connect()
    if not await client.is_user_authorized():
        await client.send_code_request(phone)
        try:
            await client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            await client.sign_in(password='SashaZt83')

    entity = await client.get_entity(username)


    async for message in client.iter_messages(entity):
        photo_counter = 0  # Инициализация счетчика фотографий

        if message.photo:
            await message.download_media(f"photo/{message.photo.id}")  # Загружаем фото, если оно есть
            time.sleep(2)
            photo_counter += 1  # Увеличиваем счетчик фотографий




        # if message.text is not None:
        #     lines = message.text.split('\n')  # Разделить текст сообщения по символу новой строки
        #     if message.photo:
        #         name_photo = f"_{photo_counter}.jpg"  # Использование счетчика в имени файла
        #         path = await message.download_media(f"photo/{name_photo}")  # Загружаем фото, если оно есть
        #         print(f"Photo saved at {path}")  # Выводим путь к сохраненному фото
        #         photo_counter += 1  # Увеличиваем счетчик фотографий

        # if len(lines) > 8:  # Проверка, что количество строк больше 8
        #     print(f'{lines[0]}')
        #     print(f'{lines[1]}')
        #     print(f'{lines[2]}')
        #     print(f'{lines[3]}')
        #     print(f'{lines[4]}')
        #     print(f'{lines[5]}')
        #     print(f'{lines[7]}')
        #     print(f'{lines[8]}')


asyncio.run(main())
