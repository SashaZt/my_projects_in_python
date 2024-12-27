import csv
import json

import pandas as pd

# File paths
input_file = "output_contract_awards.json"
output_json = "output_contract_awards_cleaned.json"
output_csv = "output_contract_awards_cleaned.csv"
output_excel = "output_contract_awards_cleaned.xlsx"

# Load JSON file
with open(input_file, "r", encoding="utf-8") as file:
    data = json.load(file)

# Process data
processed_data = []
for record in data:
    if record.get("Successful Supplier") == "Migrated Supplier":
        # Process Supplier Name
        supplier_address = record.get("Supplier Address", "")
        if supplier_address:
            # Extract the first line containing name and DBA
            name_dba_part = supplier_address.split("\n")[0]
            if "dba:" in name_dba_part:
                name_parts = name_dba_part.split("dba:")
                record["Supplier Name"] = (
                    name_parts[0].replace("Successful Supplier:", "").strip()
                )
                record["Supplier DBA"] = name_parts[1].strip()
            else:
                record["Supplier Name"] = name_dba_part.replace(
                    "Successful Supplier:", ""
                ).strip()
                record["Supplier DBA"] = ""

        # Process Supplier Address
        address_lines = supplier_address.split("\n")
        record["Supplier Street"] = address_lines[2] if len(address_lines) > 2 else ""
        record["Supplier City"] = address_lines[3] if len(address_lines) > 3 else ""
        record["Supplier Province"] = address_lines[4] if len(address_lines) > 4 else ""
        record["Supplier Country"] = address_lines[5] if len(address_lines) > 5 else ""

    # Append record to processed data
    processed_data.append(record)

# Save processed data to JSON
with open(output_json, "w", encoding="utf-8") as file:
    json.dump(processed_data, file, indent=4, ensure_ascii=False)

# Save processed data to CSV
with open(output_csv, "w", newline="", encoding="utf-8") as file:
    csv_writer = csv.writer(file)
    # Write header
    csv_writer.writerow(
        [
            "Opportunity ID",
            "Opportunity Description",
            "Opportunity Type",
            "Issuing Organization",
            "Issuing Location",
            "Contact Email",
            "Currency",
            "Contract Value",
            "Successful Supplier",
            "Award Date",
            "Justification",
            "Supplier Name",
            "Supplier DBA",
            "Supplier Street",
            "Supplier City",
            "Supplier Province",
            "Supplier Country",
        ]
    )
    # Write records
    for record in processed_data:
        csv_writer.writerow(
            [
                record.get("Opportunity ID", ""),
                record.get("Opportunity Description", ""),
                record.get("Opportunity Type", ""),
                record.get("Issuing Organization", ""),
                record.get("Issuing Location", ""),
                record.get("Contact Email", ""),
                record.get("Currency", ""),
                record.get("Contract Value", ""),
                record.get("Successful Supplier", ""),
                record.get("Award Date", ""),
                record.get("Justification", ""),
                record.get("Supplier Name", ""),
                record.get("Supplier DBA", ""),
                record.get("Supplier Street", ""),
                record.get("Supplier City", ""),
                record.get("Supplier Province", ""),
                record.get("Supplier Country", ""),
            ]
        )

# Save processed data to Excel
df = pd.DataFrame(processed_data)
df.to_excel(output_excel, index=False, sheet_name="Data")

print("Processing complete. Cleaned data saved to JSON, CSV, and Excel.")
