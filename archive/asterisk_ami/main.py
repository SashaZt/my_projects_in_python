import asyncio

from panoramisk import Manager, Message

from config import secret, username, host

manager = Manager(
    host=host,
    port=5038,
    username=username,
    secret=secret
)


async def originate_call(number, extension):
    action = Message({
        'Action': 'Originate',
        'Channel': f'SIP/{number}',
        'Context': 'default',
        'Exten': extension,
        'Priority': 1,
        'Async': 'yes',
    })
    response = await manager.send_action(action)
    return response


async def redirect_call(channel_id, extension):
    action = Message({
        'Action': 'Redirect',
        'Channel': channel_id,
        'Exten': extension,
        'Context': 'default',
        'Priority': 1,
    })
    response = await manager.send_action(action)
    return response


async def on_startup():
    await manager.connect()

    # Инициируем звонок
    response = await originate_call('0635623555', '777')
    print(response)

    # Предполагаем, что мы получили ID канала откуда-то
    channel_id = 'SIP/10314552-00000679'

    # Перенаправляем звонок на оператора
    response = await redirect_call(channel_id, '777')
    print(response)


# Запускаем event loop
if __name__ == '__main__':
    asyncio.run(on_startup())
