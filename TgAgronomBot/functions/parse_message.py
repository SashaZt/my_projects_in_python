import re


def parse_message(message, product_keywords, region_keywords):
    # Паттерн для номеров телефонов
    phone_pattern = re.compile(
        r"\+?\d{1,3}?[-.\s]?\(?\d{2,3}\)?[-.\s]?\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,4}",
        re.MULTILINE,
    )

    # Извлечение данных
    phones = [
        "".join(re.findall(r"\+?\d+", phone))
        for phone in phone_pattern.findall(message)
    ]
    phones = ", ".join(phones) if phones else None

    # Найти ключевые слова для сырья в сообщении
    raw_materials = []
    for material, keywords in product_keywords.items():
        if any(keyword.lower() in message.lower() for keyword in keywords):
            raw_materials.append(material)
    raw_materials = ", ".join(raw_materials) if raw_materials else None

    # Найти ключевые слова для регионов в сообщении
    regions = []
    for region, keywords in region_keywords.items():
        if any(keyword.lower() in message.lower() for keyword in keywords):
            regions.append(region)
    regions = ", ".join(regions) if regions else None

    # Объединение строк сообщений в полные сообщения
    log_data = message.split("\n")
    combined_messages = []
    current_message = []

    for line in log_data:
        line = line.strip()
        if not line:
            continue
        # Проверка на дату в формате ГГГГ-ММ-ДД
        if re.match(r"\d{4}-\d{2}-\d{2}", line):
            if current_message:
                combined_message = " ".join(current_message)
                combined_message = re.sub(
                    r"\s+", " ", combined_message
                )  # Удаление всех переводов строки
                combined_messages.append(combined_message)
            current_message = [line]
        else:
            current_message.append(line)

    if current_message:
        combined_message = " ".join(current_message)
        combined_message = re.sub(
            r"\s+", " ", combined_message
        )  # Удаление всех переводов строки
        combined_messages.append(combined_message)

    combined_messages = ", ".join(combined_messages) if combined_messages else None

    # Подготовка результатов
    results = {
        "Phones": phones,
        "Raw Materials": raw_materials,
        "Regions": regions,
        "Messages": combined_messages,
    }

    return results
