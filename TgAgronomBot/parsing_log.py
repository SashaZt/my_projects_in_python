import re
import os
import pandas as pd

current_directory = os.getcwd()
temp_directory = "temp"
temp_path = os.path.join(current_directory, temp_directory)
log_directory = os.path.join(temp_path, "log")
log_file_path = os.path.join(log_directory, "log_message.log")


def parse_log_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        log_data = file.readlines()

    phone_pattern = re.compile(
        r"\+?\d{1,3}?[-.\s]?\(?\d{2,3}\)?[-.\s]?\d{2,3}[-.\s]?\d{2,3}[-.\s]?\d{2,4}"
    )
    raw_materials_pattern = re.compile(
        r"\b(?:сырье|raw materials|material)\b", re.IGNORECASE
    )
    region_pattern = re.compile(r"\b(?:region|регион)\s*\d+\b", re.IGNORECASE)
    message_pattern = re.compile(r".*")

    # Extracting data
    phones = phone_pattern.findall(" ".join(log_data))
    raw_materials = raw_materials_pattern.findall(" ".join(log_data))
    regions = region_pattern.findall(" ".join(log_data))

    # Combine message lines into complete messages
    combined_messages = []
    current_message = []
    for line in log_data:
        line = line.strip()
        if not line:
            continue
        if re.match(r"\d{4}-\d{2}-\d{2}", line):
            if current_message:
                combined_messages.append(" ".join(current_message))
            current_message = [line]
        else:
            current_message.append(line)
    if current_message:
        combined_messages.append(" ".join(current_message))

    # Prepare results
    results = {
        "Phones": phones,
        "Raw Materials": raw_materials,
        "Regions": regions,
        "Messages": combined_messages,
    }

    # Convert to DataFrame for better readability
    df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in results.items()]))

    return df


df = parse_log_file(log_file_path)

# Extract all non-empty messages
non_empty_messages = df["Messages"].dropna().tolist()
for i, message in enumerate(non_empty_messages, 1):
    print(f"Message {i}: {message}")
