import aiofiles
import asyncio
import json
from pathlib import Path
from configuration.logger_setup import logger
from database import DatabaseInitializer


current_directory = Path.cwd()
temp_directory = "temp"
temp_path = current_directory / temp_directory
log_directory = temp_path / "log"
data_directory = temp_path / "data"
ringostat_directory = data_directory / "ringostat"

# Create directories if they do not exist
log_directory.mkdir(parents=True, exist_ok=True)
data_directory.mkdir(parents=True, exist_ok=True)
ringostat_directory.mkdir(parents=True, exist_ok=True)

async def read_json_file(file_path, db_initializer):
    async with aiofiles.open(file_path, mode='r') as file:
        content = await file.read()
        try:
            data = json.loads(content)
            contacts = await db_initializer.get_all_contact_data()
            phone_number = data["additional_call_data"]["userfield"]

            # По умолчанию статус клиента - "Новий"
            client_status = "Новий"
            client_id = None

            # Проверяем номера телефонов в базе данных
            for contact in contacts:
                client_id_bd = contact.get("contact_id")
                phone_number_bd = contact.get("phone_number")
                
                if phone_number_bd == phone_number:
                    client_id = client_id_bd
                    client_status = "Существует"
                    break

            # Создаем словарь с данными для записи
            all_data = {
                "id_call": data["uniqueid"],
                "date_and_time": data["calldate"],
                "client_id": client_id,
                "phone_number": phone_number,
                "company_number": data["additional_call_data"]["dst"],
                "call_type": data["additional_call_data"]["call_type"],
                "client_status": client_status,
                "interaction_status": "Договір",
                "employee": "Хтось",
                "commentary": "commentary",
                "action": data["additional_call_data"].get("action", "Нет действия")  # Example usage
            }
            success = await db_initializer.insert_call_data(all_data)
            if success:
                logger.info(f"Данные успешно добавлены в БД: {all_data}")
            else:
                logger.error(f"Ошибка при добавлении данных в БД: {all_data}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка чтения файла {file_path}: {e}")


async def write_contact(db_initializer):
    contact_data = {
        "name": "Иван",
        "surname": "Иванов",
        "formal_title": "Г-н"
    }
    success = await db_initializer.insert_contact(contact_data)
    if success:
        logger.info("Контакт успешно добавлен")
    else:
        logger.error("Ошибка при добавлении контакта")

async def write_contact_phone_number(db_initializer):
    phone_data = {
        "contact_id": 1,  # Предполагается, что такой контакт существует
        "phone_number": "380931112233"
    }
    success = await db_initializer.insert_contact_phone_number(phone_data)
    if success:
        logger.info("Номер телефона успешно добавлен")
    else:
        logger.error("Ошибка при добавлении номера телефона")

async def write_contact_email(db_initializer):
    email_data = {
        "contact_id": 1,  # Предполагается, что такой контакт существует
        "email": "ivan@example.com"
    }
    success = await db_initializer.insert_contact_email(email_data)
    if success:
        logger.info("Email успешно добавлен")
    else:
        logger.error("Ошибка при добавлении Email")

async def write_contact_bank_account(db_initializer):
    bank_account_data = {
        "contact_id": 1,  # Предполагается, что такой контакт существует
        "bank_name": "Bank of Ivan",
        "account_number": "123456789",
        "currency": "RUB"
    }
    success = await db_initializer.insert_contact_bank_account(bank_account_data)
    if success:
        logger.info("Банковский счет успешно добавлен")
    else:
        logger.error("Ошибка при добавлении банковского счета")

async def write_contact_manager(db_initializer):
    manager_data = {
        "contact_id": 1,  # Предполагается, что такой контакт существует
        "manager_contact_id": 2  # Предполагается, что такой менеджер существует
    }
    success = await db_initializer.insert_contact_manager(manager_data)
    if success:
        logger.info("Менеджер успешно добавлен")
    else:
        logger.error("Ошибка при добавлении менеджера")

async def write_contact_status(db_initializer):
    status_data = {
        "contact_id": 1,  # Предполагается, что такой контакт существует
        "status_description": "Активный"
    }
    success = await db_initializer.insert_contact_status(status_data)
    if success:
        logger.info("Статус контакта успешно добавлен")
    else:
        logger.error("Ошибка при добавлении статуса контакта")

async def write_contact_interaction_history(db_initializer):
    interaction_data = {
        "contact_id": 1,  # Предполагается, что такой контакт существует
        "interaction_type": "Звонок",
        "interaction_date": "2024-08-13 14:00:00",
        "commentary": "Обсудили условия договора"
    }
    success = await db_initializer.insert_contact_interaction_history(interaction_data)
    if success:
        logger.info("История взаимодействия успешно добавлена")
    else:
        logger.error("Ошибка при добавлении истории взаимодействия")

async def write_contact_address(db_initializer):
    address_data = {
        "contact_id": 1,  # Предполагается, что такой контакт существует
        "address_line1": "вул. Шевченка, б. 10",
        "address_line2": "кв. 5",
        "city": "Київ",
        "state": "",
        "zip_code": "123456",
        "country": "Україна"
    }
    success = await db_initializer.insert_contact_address(address_data)
    if success:
        logger.info("Адрес успешно добавлен")
    else:
        logger.error("Ошибка при добавлении адреса")



async def main():
    db_initializer = DatabaseInitializer()
    await db_initializer.create_pool()  # Убедитесь, что пул создан перед использованием
    
    # List all JSON files in the ringostat directory
    json_files = ringostat_directory.glob('*.json')
    
    # Read and print each JSON file's content
    read_tasks = [read_json_file(file, db_initializer) for file in json_files]
    await asyncio.gather(*read_tasks)

    # await write_contact(db_initializer)
    # await write_contact_phone_number(db_initializer)
    # await write_contact_email(db_initializer)
    # await write_contact_bank_account(db_initializer)
    # await write_contact_manager(db_initializer)
    # await write_contact_status(db_initializer)
    # await write_contact_interaction_history(db_initializer)
    # await write_contact_address(db_initializer)

    await db_initializer.close_pool()

# Run the main function
if __name__ == '__main__':
    asyncio.run(main())
