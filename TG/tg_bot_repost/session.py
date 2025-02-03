import re
from pathlib import Path

from config import logger, session_directory


def validate_phone_number(phone_number: str) -> str:
    if not re.match(r"^\+\d{10,15}$", phone_number):
        raise ValueError("❌ Номер телефона должен быть в формате +1234567890.")
    return phone_number


def get_session_name():
    sessions = list(session_directory.glob("*.session"))

    if sessions:
        logger.info("📌 Доступные сессии:")
        for i, session in enumerate(sessions, 1):
            logger.info(f"{i}. {session.stem}")

        choice = input(
            " Выберите номер сессии или введите новый номер телефона: "
        ).strip()
        try:
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(sessions):
                phone_number = sessions[choice_idx].stem
            else:
                phone_number = validate_phone_number(
                    input("📞 Введите новый номер телефона: ").strip()
                )
        except ValueError:
            phone_number = validate_phone_number(choice)
    else:
        logger.error("❌ Нет сохраненных сессий.")
        phone_number = validate_phone_number(
            input("📞 Введите номер телефона: ").strip()
        )

    session_name = session_directory / f"{phone_number}.session"
    logger.info(f"✅ Используется сессия: {session_name}")
    return phone_number, str(session_name)
