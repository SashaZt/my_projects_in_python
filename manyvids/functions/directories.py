import os


def create_temp_directories(base_directory):
    temp_directory = "temp"
    # Создайте полный путь к папке temp
    temp_path = os.path.join(base_directory, temp_directory)

    # Список всех нужных подкаталогов
    directories = [
        "cookies",
        "login_pass",
        "daily_sales",
        "monthly_sales",
        "payout_history",
        "pending_custom",
        "chat",
    ]

    # Создание папок, если они не существуют
    for directory in directories:
        dir_path = os.path.join(temp_path, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    # Пути к папкам
    paths = {
        "cookies_path": os.path.join(temp_path, "cookies"),
        "login_pass_path": os.path.join(temp_path, "login_pass"),
        "daily_sales_path": os.path.join(temp_path, "daily_sales"),
        "monthly_sales_path": os.path.join(temp_path, "monthly_sales"),
        "payout_history_path": os.path.join(temp_path, "payout_history"),
        "pending_custom_path": os.path.join(temp_path, "pending_custom"),
        "chat_path": os.path.join(temp_path, "chat"),
    }

    return paths
