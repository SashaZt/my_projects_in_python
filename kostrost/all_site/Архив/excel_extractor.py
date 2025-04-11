import json

import pandas as pd


def extract_column_a_from_excel(file_path):
    """
    Extract data from column A of each sheet in an Excel file.
    Returns data in the format:
    [
        {
            "Название листа": [
                {
                    "url": value
                },
                ...
            ]
        },
        ...
    ]
    """
    # Read the Excel file
    xl = pd.ExcelFile(file_path)

    # Get all sheet names
    sheet_names = xl.sheet_names

    # Initialize result list
    result = []

    # Process each sheet
    for sheet_name in sheet_names:
        # Read only column A from the sheet
        df = pd.read_excel(file_path, sheet_name=sheet_name, usecols=[0])

        # Create list of dictionaries for column A values
        urls = []
        for value in df.iloc[:, 0].dropna():
            urls.append({"url": str(value)})

        # Create sheet entry
        sheet_entry = {sheet_name: urls}

        # Add to result
        result.append(sheet_entry)

    return result


if __name__ == "__main__":
    # This code runs when the script is executed directly
    # Replace with your file path
    file_path = "thomann.xlsx"

    # Extract data
    extracted_data = extract_column_a_from_excel(file_path)

    # Save to file
    with open("extracted_urls.json", "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)

    print("Data extracted and saved to extracted_urls.json")
