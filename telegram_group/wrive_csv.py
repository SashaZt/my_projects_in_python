import csv
import os
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

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
            await client.sign_in(password='your_password')
    entity = await client.get_entity(username)

    # Инициализируем файл CSV
    with open('messages.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Message_ID", "Sender_ID", "Text"])

        # Итерация по сообщениям
        async for message in client.iter_messages(entity):
            # Записываем сообщение в CSV
            writer.writerow([message.id, message.sender_id, message.text])

            # Если есть фото в сообщении, скачиваем его
            if message.photo:
                filename = os.path.join("photo_folder", f"{message.id}.jpg")
                await message.download_media(file=filename)


with client:
    client.loop.run_until_complete(main())
