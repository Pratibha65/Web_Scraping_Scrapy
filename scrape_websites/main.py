import os
import time 
import pandas as pd
from website import get_official_website
 
def Read_Consignee(file_path: str) -> None:
    try:
        df=pd.read_csv(file_path)
    except FileNotFoundError:
        print(f'Error: File {file_path} not found.')
        return
    
    required_col = {"Consignee_Name", "Location"}
    if not required_col.issubset(df.columns):
        print(f"Error: Missing required columns {required_col - set(df.columns)} in input file.")
        return
    
    df["Company Website"] = None
    df["Phone Numbers"] = None
    df["Email"]= None
    
    for idx,row in df.iterrows():
        consignee_name = row.get("Consignee_Name", "").strip()
        location = row.get("Location", "").strip()

        if not consignee_name or not location:
            print(f"Skipping row {idx} due to missing consignee name or location.")
            continue

        print(f"Processing: {consignee_name} from {location}----------------------------------->\n")

        try:
            website_url = get_official_website(consignee_name,location)

            df.at[idx, "Company Website"] = website_url

            websites_df = df[["Company Website"]].dropna().drop_duplicates()
            websites_df.to_csv("Only_Websites.csv", index=False)
            
        except Exception as e:
            print(f"Error processing {consignee_name}: {e}")

        time.sleep(2)  

    
if __name__ == '__main__':
    Read_Consignee("Consignee1.csv")