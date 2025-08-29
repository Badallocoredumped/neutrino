import json
from pprint import pprint
from webbrowser import Mozilla
from dotenv import load_dotenv
import requests
import os
import pandas as pd
load_dotenv(dotenv_path=".env", override=True)





# Config
CAS_URL = "https://giris.epias.com.tr/cas/v1/tickets"
REALTIME_GEN_URL = "https://seffaflik.epias.com.tr/electricity-service/technical/tr/index.html#_realtime-consumption",
TGT = "TGT-9461130-NU4vmKb6tJhEMOEVYir-0GPlUVOk-4N6pUEeqS-1ymp3yUNB-kTfu-4hbNQ0uofOCv0-cas-7dc76c888-d9cdw"

HEADERS_TGT = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/plain"
}
HEADERS_GETDATA = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language":"en",
    "Accept": "application/json",
    "TGT": TGT
}

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

start_date = "2024-09-10T00:00:00+03:00"
end_date = "2024-09-10T00:00:00+03:00"

def get_tgt(username, password):
    """
    Get TGT (Ticket Granting Ticket) for the user
    """
    data = {
        "username": username,
        "password": password
    }
    response = requests.post(CAS_URL, headers=HEADERS_TGT, data=data)
    print("Status Code:", response.status_code)
    
    if response.status_code in [200, 201]:
        tgt = response.text.strip()
        return tgt
    return None

def get_realtime_generation_data(tgt, start_date, end_date):
    """
    Get real-time generation data for the specified date range
    """
    """ headers = HEADERS_GETDATA.copy()

    headers["TGT"] = tgt   """
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    response = requests.post(REALTIME_GEN_URL, headers=HEADERS_GETDATA, json=params)
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        return response.json()
    return None



def save_generation_to_csv(data, filename="generation_data.csv"):
    """
    Save generation data to CSV file
    
    Args:
        data (dict): The JSON response from the API
        filename (str): The output CSV filename
    """
    if not data:
        print("No data to save")
        return
    
    try:
        # Check if data has the expected structure
        if 'body' in data and 'generationList' in data['body']:
            # Extract the generation list
            generation_list = data['body']['generationList']
            
            # Convert to DataFrame
            df = pd.DataFrame(generation_list)
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Data saved to {filename}")
            print(f"Saved {len(df)} records")
            
            # Display first few rows
            print("\nFirst 5 rows:")
            print(df.head())
            
        else:
            # If structure is different, save the entire data
            print("Unexpected data structure, saving raw data...")
            df = pd.json_normalize(data)
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"Raw data saved to {filename}")
            
    except Exception as e:
        print(f"Error saving to CSV: {e}")
        # Fallback: save as JSON
        with open(filename.replace('.csv', '.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Data saved as JSON instead: {filename.replace('.csv', '.json')}")


# Example usage
if __name__ == "__main__":

    
    """ tgt = get_tgt(username, password)
    print(tgt) """
    data = get_realtime_generation_data("TGT-9461130-NU4vmKb6tJhEMOEVYir-0GPlUVOk-4N6pUEeqS-1ymp3yUNB-kTfu-4hbNQ0uofOCv0-cas-7dc76c888-d9cdw", start_date, end_date)
    print(data)
    #save_generation_to_csv(data)