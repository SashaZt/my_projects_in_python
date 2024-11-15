from datetime import datetime

from configuration.logger_setup import logger


def apply_single_filter(data, field, condition, value):
    if field == "call_date":
        filter_date = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        if condition == "больше чем":
            return [
                record
                for record in data
                if datetime.strptime(record.get(field), "%Y-%m-%d %H:%M:%S")
                > filter_date
            ]
        elif condition == "меньше чем":
            return [
                record
                for record in data
                if datetime.strptime(record.get(field), "%Y-%m-%d %H:%M:%S")
                < filter_date
            ]
        elif condition == "больше или равно":
            return [
                record
                for record in data
                if datetime.strptime(record.get(field), "%Y-%m-%d %H:%M:%S")
                >= filter_date
            ]
        elif condition == "меньше или равно":
            return [
                record
                for record in data
                if datetime.strptime(record.get(field), "%Y-%m-%d %H:%M:%S")
                <= filter_date
            ]
    else:
        if condition == "равно":
            return [record for record in data if record.get(field) == value]
        elif condition == "не равно":
            return [record for record in data if record.get(field) != value]
        elif condition == "содержит":
            return [record for record in data if value in record.get(field, "")]
        elif condition == "не содержит":
            return [record for record in data if value not in record.get(field, "")]
        elif condition == "начинается с":
            return [
                record for record in data if record.get(field, "").startswith(value)
            ]
        elif condition == "заканчивается на":
            return [record for record in data if record.get(field, "").endswith(value)]
    return data


def apply_combined_filter(data, filters):
    filtered_data = data
    for i, filter_data in enumerate(filters):
        field, condition, value, operator = filter_data
        if field and condition and value:
            logger.info(
                f"Applying filter {i + 1}: field={field}, condition={condition}, value={value}, operator={operator}"
            )
            current_filtered = apply_single_filter(
                filtered_data, field, condition, value
            )
            if operator == "И":
                filtered_data = [
                    record for record in filtered_data if record in current_filtered
                ]
            elif operator == "ИЛИ":
                filtered_data = list({*filtered_data, *current_filtered})
    return filtered_data
