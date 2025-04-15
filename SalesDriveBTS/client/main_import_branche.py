import json
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

def load_branches_from_json(json_file_path, db_config):
    """
    Загрузить данные о филиалах из JSON файла в базу данных PostgreSQL
    
    Args:
        json_file_path (str): Путь к JSON файлу с филиалами
        db_config (dict): Конфигурация подключения к БД
    """
    try:
        # Читаем JSON файл
        with open(json_file_path, 'r', encoding='utf-8') as file:
            branches_data = json.load(file)
        
        # Подключаемся к БД
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        
        # Подготавливаем данные для вставки
        values = []
        for branch in branches_data:
            values.append((
                branch['branche_id'],
                branch['branche_name'],
                branch['address'],
                branch['regionId'],
                branch['cityId']
            ))
        
        # Используем более эффективный метод вставки данных
        insert_query = """
            INSERT INTO branches 
            (branch_id, branch_name, address, region_id, city_id) 
            VALUES %s
            ON CONFLICT (branch_id) DO UPDATE 
            SET 
                branch_name = EXCLUDED.branch_name,
                address = EXCLUDED.address,
                region_id = EXCLUDED.region_id,
                city_id = EXCLUDED.city_id,
                updated_at = CURRENT_TIMESTAMP
        """
        
        # Используем execute_values для массовой вставки (более эффективно)
        execute_values(cursor, insert_query, values)
        
        # Фиксируем изменения и закрываем соединение
        connection.commit()
        print(f"Загружено {len(branches_data)} филиалов в базу данных")
        
    except psycopg2.Error as e:
        print(f"Ошибка PostgreSQL: {e}")
    except FileNotFoundError:
        print(f"Файл {json_file_path} не найден")
    except json.JSONDecodeError:
        print(f"Ошибка при разборе JSON файла {json_file_path}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")
    finally:
        if 'connection' in locals() and connection:
            cursor.close()
            connection.close()
            print("Соединение с БД закрыто")

# Конфигурация для подключения к PostgreSQL
db_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'your_database',
    'user': 'your_username',
    'password': 'your_password'
}

# Путь к файлу с данными о филиалах
json_file_path = 'all_branches.json'

# Загрузка данных
if __name__ == '__main__':
    load_branches_from_json(json_file_path, db_config)