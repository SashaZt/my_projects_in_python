# import asyncio
# from telethon import TelegramClient, events, sync
#
# def get_api_id_and_hash():
#     api_id = '8771905'
#     api_hash = '39debb7f571db5ad62288c20780af81c'
#     return api_id, api_hash
#
# def create_telegram_client(api_id, api_hash, session_name):
#     client = TelegramClient(session_name, api_id, api_hash)
#     return client
#
# async def get_group_participants(client, group_name):
#     async for member in client.iter_participants(group_name):
#         print(member.id, member.first_name)
#
# async def main():
#     api_id, api_hash = get_api_id_and_hash()
#     client = create_telegram_client(api_id, api_hash, 'session_name')
#     await client.start()
#     await get_group_participants(client, 'название_группы')
#     await client.disconnect()
#
# if __name__ == '__main__':
#     asyncio.run(main())
from telethon.errors import SessionPasswordNeededError
from telethon.sync import TelegramClient


def connect_and_sign_in(phone, api_id, api_hash):
    client = TelegramClient(phone, api_id, api_hash)
    client.connect()

    if not client.is_user_authorized():
        # Запрашиваем сессию
        client.send_code_request(phone)
        try:
            client.sign_in(phone, input('Enter the code: '))
        except SessionPasswordNeededError:
            client.sign_in(password='SashaZt83')

    return client


def join_group(client, username):
    group = client.get_entity(username)
    client.join_chat(group)


def get_group_participants(client, username):
    group = client.get_entity(username)
    participants = client.get_participants(group)
    return participants


def print_participants(participants):
    for participant in participants:
        print(participant.id, participant.first_name)



def main():
    # Replace with your actual credentials
    api_id = '8771905'  # Замените на ваш API_ID
    api_hash = '39debb7f571db5ad62288c20780af81c'  # Замените на ваш API_HASH
    phone = '+380635623555'  # Замените на ваш номер телефона
    username = 'https://t.me/tnefor'

    client = connect_and_sign_in(phone, api_id, api_hash)
    participants = get_group_participants(client, username)
    print_participants(participants)


if __name__ == '__main__':
    main()
