import json
from pprint import pprint
from dotenv import load_dotenv
import requests
import os
import pandas as pd
from datetime import datetime

from database.energy_data_repository import EnergyDataRepository


load_dotenv(dotenv_path=".env", override=True)

POWER_BREAKDOWN_URL = os.getenv("POWER_BREAKDOWN_HISTORY_URL")
CARBON_HISTORY_URL = os.getenv("CARBON_HISTORY_URL")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")

os.makedirs("raw", exist_ok=True)
os.makedirs("transformed", exist_ok=True)

def transform_power_breakdown(raw_data: list) -> pd.DataFrame:
    """
    Transforms raw power breakdown JSON into flat, clean DataFrame.
    """
    records = []
    for entry in raw_data:
        flat = {
            "datetime": entry.get("datetime"),
            "zone": entry.get("zone"),
            "powerConsumptionTotal": entry.get("powerConsumptionTotal"),
        }

        # Unpack the power production breakdown
        breakdown = entry.get("powerProductionBreakdown", {})
        for k, v in breakdown.items():
            # Handle None values convert to 0 for calculations
            flat[f"production_{k}"] = v if v is not None else 0

        # Compute totals with None handling
        fossil_sources = ["coal", "gas", "oil"]
        renewable_sources = ["wind", "solar", "hydro", "biomass", "geothermal"]

        # Use 0 if value is None
        flat["fossil_total"] = sum(
            breakdown.get(source, 0) or 0 for source in fossil_sources
        )
        flat["renewable_total"] = sum(
            breakdown.get(source, 0) or 0 for source in renewable_sources
        )

        # Calculate total generation with None handling
        total_gen = sum(v or 0 for v in breakdown.values())
        flat["total_generation"] = total_gen
        
        # % renewable
        flat["percent_renewable"] = (
            round(100 * flat["renewable_total"] / total_gen, 2) if total_gen > 0 else 0
        )
        
        # % fossil
        flat["percent_fossil"] = (
            round(100 * flat["fossil_total"] / total_gen, 2) if total_gen > 0 else 0
        )

        records.append(flat)

    df = pd.DataFrame(records)
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df

def transform_carbon_intensity(raw_data: list) -> pd.DataFrame:
    """
    Transforms raw carbon intensity JSON into flat, clean DataFrame.
    """
    records = []
    for entry in raw_data:
        flat = {
            "datetime": entry.get("datetime"),
            "zone": entry.get("zone"),
            "carbonIntensity": entry.get("carbonIntensity"),
            "updatedAt": entry.get("updatedAt"),
            "createdAt": entry.get("createdAt"),
            "emissionFactorType": entry.get("emissionFactorType"),
            "isEstimated": entry.get("isEstimated"),
            "estimationMethod": entry.get("estimationMethod"),
            "temporalGranularity": entry.get("temporalGranularity")
        }
        
        # Add computed fields
        carbon_intensity = entry.get("carbonIntensity", 0)
        
        # Categorize carbon intensity levels
        if carbon_intensity < 200:
            flat["carbon_level"] = "Low"
        elif carbon_intensity < 400:
            flat["carbon_level"] = "Medium"
        elif carbon_intensity < 600:
            flat["carbon_level"] = "High"
        else:
            flat["carbon_level"] = "Very High"
        
        # Calculate time since update (in hours)
        if entry.get("updatedAt") and entry.get("datetime"):
            updated_time = pd.to_datetime(entry["updatedAt"])
            data_time = pd.to_datetime(entry["datetime"])
            flat["hours_since_update"] = round((updated_time - data_time).total_seconds() / 3600, 2)
        else:
            flat["hours_since_update"] = None

        records.append(flat)

    df = pd.DataFrame(records)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["updatedAt"] = pd.to_datetime(df["updatedAt"])
    df["createdAt"] = pd.to_datetime(df["createdAt"])
    return df

def save_data_to_csv(data, filename):
    df = pd.DataFrame(data)
    ts = datetime.utcnow().strftime("%Y%m%d")
    output_file = f"{filename.rstrip('.csv')}_{ts}.csv"
    df.to_csv(output_file, sep=";", index=False)
    print(f"Saved CSV: {output_file}")

def save_data_to_jsonl(data, filename, folder):
    ts = datetime.utcnow().strftime("%Y%m%d")
    output_file = f"{folder}/{filename.rstrip('.jsonl')}_{ts}.jsonl"
    with open(output_file, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    print(f"Saved JSONL: {output_file}")

def load_data_from_jsonl(filename):
    """
    Load data from .jsonl file (one JSON object per line)
    """
    data = []
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if line:  # Skip empty lines
                data.append(json.loads(line))
    return data

def fetch_and_save_data():
    print(f"\n⏰ Job started at {datetime.utcnow().isoformat()}")

    try:
        # --- POWER BREAKDOWN ---
        response = requests.get(POWER_BREAKDOWN_URL, headers={"auth-token": AUTH_TOKEN})
        response.raise_for_status()
        power_data = response.json()
        print(len(power_data))
        pprint(power_data)

        # This is already a single data point — just wrap in list
        save_data_to_jsonl(power_data["history"], "power_breakdown_history.jsonl", folder="raw")

        # --- CARBON INTENSITY ---
        response = requests.get(CARBON_HISTORY_URL, headers={"auth-token": AUTH_TOKEN})
        response.raise_for_status()
        carbon_data = response.json()
        #pprint(carbon_data)

        # Flatten 'history' with metadata
        zone = carbon_data.get("zone")
        granularity = carbon_data.get("temporalGranularity")
        history = carbon_data.get("history", [])

        for entry in history:
            entry["zone"] = zone
            entry["temporalGranularity"] = granularity

        save_data_to_jsonl(history, "carbon_intensity_history.jsonl", folder="raw")

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
    except Exception as ex:
        print(f"Unexpected error: {ex}")

def fetch_transform_and_store_data():
    """Fetch, transform, and store data in MongoDB"""
    print(f"\n⏰ Job started at {datetime.utcnow().isoformat()}")
    
    # Initialize database repository
    repo = EnergyDataRepository()
    
    try:
        # --- POWER BREAKDOWN ---
        response = requests.get(POWER_BREAKDOWN_URL, headers={"auth-token": AUTH_TOKEN})
        response.raise_for_status()
        power_data = response.json()
        
        # Save raw data
        save_data_to_jsonl(power_data["history"], "power_breakdown_history.jsonl", folder="raw")
        
        # Transform and store in MongoDB
        power_df = transform_power_breakdown(power_data["history"])
        repo.save_power_data(power_df)
        
        # --- CARBON INTENSITY ---
        response = requests.get(CARBON_HISTORY_URL, headers={"auth-token": AUTH_TOKEN})
        response.raise_for_status()
        carbon_data = response.json()
        
        # Flatten and save raw data
        zone = carbon_data.get("zone")
        granularity = carbon_data.get("temporalGranularity")
        history = carbon_data.get("history", [])
        
        for entry in history:
            entry["zone"] = zone
            entry["temporalGranularity"] = granularity
        
        save_data_to_jsonl(history, "carbon_intensity_history.jsonl", folder="raw")
        
        # Transform and store in MongoDB
        carbon_df = transform_carbon_intensity(history)
        repo.save_carbon_data(carbon_df)
        
        print("✅ Data successfully stored in MongoDB")
        
    except Exception as e:
        print(f"❌ Error in data processing: {e}")
    finally:
        repo.close()

def start_schedule():
    scheduler = BlockingScheduler()
    scheduler.add_job(fetch_and_save_data, trigger="interval", hours=1)
    print("📅 Scheduler started: job will run every hour.")
    scheduler.start()

if __name__ == "__main__":


    fetch_transform_and_store_data()

    """ # Test both transformations
    #fetch_and_save_data()
    
    # Load and transform carbon data
    print("=== CARBON INTENSITY DATA ===")
    carbon_data = load_data_from_jsonl("carbon_intensity_history_20250822.jsonl")
    print(f"Loaded {len(carbon_data)} carbon records")
    
    carbon_df = transform_carbon_intensity(carbon_data)
    print("Carbon DataFrame:")
    print(carbon_df.head())
    print(f"\nCarbon columns: {carbon_df.columns.tolist()}")
    
    # Save to CSV
    save_data_to_csv(carbon_df, "carbon_intensity_transformed.csv", folder="transformed")

    # Load and transform power data (if you have it)
    print("\n=== POWER BREAKDOWN DATA ===")
    try:
        power_data = load_data_from_jsonl("power_breakdown_history_20250822.jsonl")
        print(f"Loaded {len(power_data)} power records")
        
        power_df = transform_power_breakdown(power_data)
        print("Power DataFrame:")
        print(power_df.head())
        print(f"\nPower columns: {power_df.columns.tolist()}")
        
        # Save to CSV
        save_data_to_csv(power_df, "power_breakdown_transformed.csv", folder="transformed")

    except FileNotFoundError:
        print("Power breakdown file not found - skipping") """