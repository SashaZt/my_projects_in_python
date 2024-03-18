import asyncio
import logging

import panoramisk
from panoramisk import Manager

from models import ColdCall

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Список доступных операторов
available_operators = []

# Очередь звонков клиентов, ожидающих соединения с оператором
waiting_calls = []
manager = None


def initialize_manager(host, port, username, secret, ping_delay):
    global manager
    manager = Manager(
        host=host,
        port=port,
        username=username,
        secret=secret,
        ping_delay=ping_delay
    )
    logger.info("Manager initialized")


client_list = []


async def load_client_list(db_session):
    global client_list
    result = db_session.query(ColdCall.nomer).all()
    client_list = [item.nomer for item in result]
    print("Загруженный список клиентов:", client_list)


async def connect_call_to_operator(manager, client_number, operator_extension):
    action = panoramisk.Message({
        'Action': 'Originate',
        'Channel': f'Local/{client_number}@from-internal',  # Инициируем вызов на номер клиента
        'Context': 'from-internal',  # Указываем контекст для внутреннего перенаправления
        'Exten': operator_extension,  # Указываем внутренний номер оператора для перенаправления
        'Priority': 1,
        'Timeout': 10000,
        'Async': 'true',
        'CallerID': f'Operator <{operator_extension}>',  # Опционально: установка CallerID для вызова
    })

    response = await manager.send_action(action)
    return response



async def handle_extension_status(manager: panoramisk.Manager, message: panoramisk.Message) -> None:
    if message.event != 'ExtensionStatus':
        return  # Если событие не соответствует, выходим из функции

    status_code = int(message['Status'])
    extension = message['Exten']

    if status_code == 0 and waiting_calls:  # Если оператор свободен и есть ожидающие звонки
        client_number = waiting_calls.pop(0)
        await connect_call_to_operator(manager, client_number, extension)

async def handle_all_messages(manager: panoramisk.Manager, message: panoramisk.Message) -> None:
    await handle_extension_status(manager, message)
    # Добавьте здесь вызовы других функций для обработки других типов сообщений

async def originate_call_to_client(manager, client_number):
    # Инициирование вызова клиенту
    action = panoramisk.Message({
        'Action': 'Originate',
        'Channel': f'Local/{client_number}@from-internal',  # Замените на ваш исходящий контекст
        'Context': 'from-internal',  # Замените на контекст ожидания соединения
        'Exten': 's',
        'Priority': 1,
        'Async': 'true',
    })

    await manager.send_action(action)
    waiting_calls.append(client_number)  # Добавление клиента в очередь ожидания




# ami_handler.py
async def call_clients(manager):
    global client_list
    for client_number in client_list:
        print('Звонок клиенту:', client_number)
        await originate_call_to_client(manager, client_number)
        await asyncio.sleep(10)  # Краткая пауза между звонками


async def main(host, port, username, secret, ping_delay):
    manager = Manager(
        host=host,
        port=port,
        username=username,
        secret=secret,
        ping_delay=ping_delay
    )
    await manager.connect()
    manager.register_event('*', handle_all_messages)
    asyncio.create_task(call_clients(manager))
    while True:
        await asyncio.sleep(1)
