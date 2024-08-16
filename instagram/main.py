import instaloader
import csv
import time
from instaloader.exceptions import (
    TwoFactorAuthRequiredException,
    LoginRequiredException,
    QueryReturnedBadRequestException,
)

# Данные для авторизации
username = "CartersZt"
password = "DbrnjhbZ88"
# Целевой профиль
profile_name = "aiza.fai"


# Создание экземпляра Instaloader
loader = instaloader.Instaloader()

try:
    # Логин
    loader.login(username, password)

except TwoFactorAuthRequiredException:
    # Если требуется двухфакторная аутентификация, попросим ввести 6-значный код
    two_factor_code = input(
        "Введите 6-значный код для входа, сгенерированный в приложении для аутентификации: "
    )
    loader.two_factor_login(two_factor_code)


# Обработка ошибки challenge_required
try:
    time.sleep(5)  # Пауза перед запросом профиля
    profile = instaloader.Profile.from_username(loader.context, profile_name)

    # Открытие CSV файла для записи
    with open(
        f"{profile_name}_followers.csv", mode="w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["Username", "Full Name", "Profile URL"])

        # Извлечение подписчиков
        followers = profile.get_followers()

        # Сохранение подписчиков в CSV
        for follower in followers:
            writer.writerow(
                [
                    follower.username,
                    follower.full_name,
                    f"https://instagram.com/{follower.username}",
                ]
            )

        print(
            f"Подписчики профиля {profile_name} успешно сохранены в {profile_name}_followers.csv"
        )

except QueryReturnedBadRequestException as e:
    print(f"Ошибка: {str(e)}. Необходимо пройти подтверждение на стороне Instagram.")
except LoginRequiredException as e:
    print(f"Ошибка: {str(e)}. Для получения списка подписчиков необходима авторизация.")
