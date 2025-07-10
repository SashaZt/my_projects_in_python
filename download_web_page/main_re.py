import re


def clean_title(original_title):
    # Отрезаем всё после слова Key (включительно)
    title_part = re.split(r"\bKey\b", original_title, flags=re.IGNORECASE)[0]

    # Убираем скобки, Xbox и т.п.
    title_clean = re.sub(r"\(.*?\)", "", title_part, flags=re.IGNORECASE)
    title_clean = re.sub(
        r"(?i)\b(XBOX LIVE|Xbox Live|Xbox One|Xbox)\b", "", title_clean
    )

    # Убираем лишние пробелы
    title_clean = re.sub(r"\s{2,}", " ", title_clean).strip()
    title_clean = title_clean.rstrip(":")

    return title_clean


# Пример
titles = [
    "Assassin's Creed Triple Pack: Black Flag, Unity, Syndicate XBOX LIVE Key ARGENTINA",
    "Assassin's Creed Triple Pack: Black Flag, Unity, Syndicate (Xbox One) Xbox Live Key EUROPE",
    "Assassin's Creed Triple Pack (Xbox One) Xbox Live Key EUROPE",
    "Assassin's Creed Triple Pack: Black Flag, Unity, Syndicate XBOX LIVE Key TURKEY",
    "Assassin's Creed Triple Pack: Black Flag, Unity, Syndicate (Xbox One) Xbox Live Key UNITED STATES",
]

for t in titles:
    cleaned = clean_title(t)
    print(f"Название: {cleaned}")
