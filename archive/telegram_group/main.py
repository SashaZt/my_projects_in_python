from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError

api_id = '8771905'  # Замените на ваш API_ID
api_hash = '39debb7f571db5ad62288c20780af81c'  # Замените на ваш API_HASH
phone = '+380635623555'  # Замените на ваш номер телефона
username = 'https://t.me/milirud_official'  # Замените на вашу ссылку на группу (например, 'https://t.me/joinchat/AAAAAFf4hjtpr6eDZ-bjFg')
client = TelegramClient(phone, api_id, api_hash)

client.connect()
if not client.is_user_authorized():
    client.send_code_request(phone)
    try:
        client.sign_in(phone, input('Enter the code: '))
    except SessionPasswordNeededError:
        client.sign_in(password='SashaZt83')


# Получение информации о группе
entity = client.get_entity(username)
async for message in client.iter_messages('YourGroupName'):
    lines = message.text.split('\n')  # Разделить текст сообщения по символу новой строки
    if len(lines) > 8:  # Проверка, что количество строк больше 8
        print(f'Строка 1 {lines[0]}')
        print(f'Строка 2 {lines[1]}')
        print(f'Строка 3 {lines[2]}')
        print(f'Строка 4 {lines[3]}')
        print(f'Строка 5 {lines[4]}')
        print(f'Строка 6 {lines[5]}')
        print(f'Строка 7 {lines[7]}')
        print(f'Строка 8 {lines[8]}')
    if message.photo:
        path = await message.download_media("path_to_directory")  # Загружаем фото, если оно есть
        print(f"Photo saved at {path}")  # Выводим путь к сохраненному фото



# Получение сообщений
messages = client.iter_messages(entity)
for message in messages:
    lines = message.text.split('\n')  # Разделить текст сообщения по символу новой строки
    if len(lines) > 8:  # Проверка, что количество строк больше 8
        print(f'Строка 1 {lines[0]}')
        print(f'Строка 2 {lines[1]}')
        print(f'Строка 3 {lines[2]}')
        print(f'Строка 4 {lines[3]}')
        print(f'Строка 5 {lines[4]}')
        print(f'Строка 6 {lines[5]}')
        print(f'Строка 7 {lines[7]}')
        print(f'Строка 8 {lines[8]}')
    else:
        continue
