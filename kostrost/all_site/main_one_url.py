import json

import pandas as pd


def extract_one_url_from_each_sheet(file_path):
    """
    Extract only one URL from column A of each sheet in an Excel file.
    Returns data in the format:
    [
        {
            "Название листа": [
                {
                    "url": value
                }
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

        # Create a list with just the first URL value (if exists)
        urls = []
        # Take only the first non-NaN value
        first_values = df.iloc[:, 0].dropna()
        if len(first_values) > 0:
            first_value = first_values.iloc[0]
            urls.append({"url": str(first_value)})

        # Create sheet entry
        sheet_entry = {sheet_name: urls}

        # Add to result
        result.append(sheet_entry)

    return result


if __name__ == "__main__":
    # Replace with your file path
    file_path = "thomann.xlsx"

    # Extract data
    extracted_data = extract_one_url_from_each_sheet(file_path)

    # Save to file
    with open("test_one_url.json", "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=4, ensure_ascii=False)

    print("Data extracted and saved to test_one_url.json")

    # Print extracted URLs for verification
    print("\nExtracted URLs:")
    for sheet_data in extracted_data:
        for sheet_name, urls in sheet_data.items():
            url_count = len(urls)
            url_info = urls[0]["url"] if url_count > 0 else "No URL found"
            print(f"Sheet: {sheet_name}, URL: {url_info}")
