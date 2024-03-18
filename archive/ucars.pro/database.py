import aiomysql

async def connect_to_database():
    conn = await aiomysql.connect(
        host="162.55.63.6",
        user="car_db_user_001",
        password="wE8wH9jA3jfC5hK6hY6j",
        db="lot_database"
    )
    return conn
