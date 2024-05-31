import string
import secrets
import pyperclip


def generate_password(length):
    if length < 4:  # Ensure the password length is sufficient
        raise ValueError("Длина пароля должна быть не менее 4 символов.")

    # Define character sets
    lower_case = string.ascii_lowercase
    upper_case = string.ascii_uppercase
    digits = string.digits
    special_chars = string.punctuation

    # Ensure the password includes at least one character from each set
    password = [
        secrets.choice(lower_case),
        secrets.choice(upper_case),
        secrets.choice(digits),
        secrets.choice(special_chars),
    ]

    # Fill the rest of the password length with a mix of all character sets
    all_chars = lower_case + upper_case + digits + special_chars
    password += [secrets.choice(all_chars) for _ in range(length - 4)]

    # Shuffle the password list to ensure randomness
    secrets.SystemRandom().shuffle(password)

    # Convert the list to a string
    return "".join(password)


def main():
    while True:
        try:
            length = int(input("Введите желаемую длину пароля:"))
            password = generate_password(length)
            print(f"Сгенерированный пароль:\n{password}")
            user_response = (
                input("Вам нравится этот пароль? (yes/no): ").strip().lower()
            )
            if user_response == "yes":
                pyperclip.copy(password)
                print("Пароль скопирован в буфер обмена.")
                break
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
