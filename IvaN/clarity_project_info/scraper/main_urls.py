import pandas as pd

# Reading the input CSV file
df = pd.read_csv("all.csv")

# Generating URLs based on the 'id' column
base_url = "https://clarity-project.info/edr/"
df["url"] = base_url + df["id"].astype(str) + "/yearly-finances"

# Creating a new DataFrame with only the 'url' column
result_df = df[["url"]]

# Saving the result to a new CSV file
result_df.to_csv("all_edrs.csv", index=False)
