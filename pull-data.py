import json
from pprint import pprint
from webbrowser import Mozilla
from dotenv import load_dotenv
import requests
import os
load_dotenv(dotenv_path=".env", override=True)


# Config
CAS_URL = "https://giris.epias.com.tr/cas/v1/tickets"
REALTIME_GEN_URL = "https://seffaflik.epias.com.tr/electricity-service/v1/generation/data/realtime-generation"

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
    headers = HEADERS_GETDATA.copy()

    headers["TGT"] = tgt  
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    response = requests.post(REALTIME_GEN_URL, headers=headers, json=params)
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        return response.json()
    return None



# Example usage
if __name__ == "__main__":

    
    tgt = get_tgt(username, password)
    print(tgt)
    data = get_realtime_generation_data(tgt, start_date, end_date)
    pprint(data)