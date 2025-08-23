import json
import glob
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

# === STEP 1: FETCH AND SAVE RAW DATA ===
def fetch_and_save_raw_data():
    """Step 1: Fetch data from API and save raw JSONL files"""
    print(f"\n🔄 STEP 1: Fetching raw data at {datetime.utcnow().isoformat()}")
    
    try:
        headers = {"auth-token": AUTH_TOKEN}
        ts = datetime.utcnow().strftime("%Y%m%d")
        
        # === POWER BREAKDOWN DATA ===
        print("📡 Fetching power breakdown data...")
        power_response = requests.get(POWER_BREAKDOWN_URL, headers=headers)
        power_response.raise_for_status()
        power_data = power_response.json()
        
        print(f"📊 API returned {len(power_data['history'])} power records")
        
        # Save raw power data
        power_file = f"raw/power_breakdown_raw_{ts}.jsonl"
        with open(power_file, "w") as f:
            for item in power_data["history"]:
                f.write(json.dumps(item) + "\n")
        print(f"💾 Saved raw power data: {power_file}")
        
        # === CARBON INTENSITY DATA ===
        print("📡 Fetching carbon intensity data...")
        carbon_response = requests.get(CARBON_HISTORY_URL, headers=headers)
        carbon_response.raise_for_status()
        carbon_data = carbon_response.json()
        
        # Extract and flatten carbon data
        zone = carbon_data.get("zone")
        history = carbon_data.get("history", [])
        
        print(f"📊 API returned {len(history)} carbon records for zone {zone}")
        
        # Add zone to each record
        for entry in history:
            entry["zone"] = zone
            entry["temporalGranularity"] = carbon_data.get("temporalGranularity")
        
        # Save raw carbon data
        carbon_file = f"raw/carbon_intensity_raw_{ts}.jsonl"
        with open(carbon_file, "w") as f:
            for item in history:
                f.write(json.dumps(item) + "\n")
        print(f"💾 Saved raw carbon data: {carbon_file}")
        
        print("✅ Step 1 completed - Raw data saved")
        return power_file, carbon_file
        
    except Exception as e:
        print(f"❌ Error in Step 1: {e}")
        raise

# === STEP 2: TRANSFORM DATA ===
def transform_and_save_data():
    """Step 2: Transform all raw files and save to transformed folder"""
    print(f"\n🔄 STEP 2: Transforming data")
    
    # Find all raw files
    power_raw_files = glob.glob("raw/power_breakdown_raw_*.jsonl")
    carbon_raw_files = glob.glob("raw/carbon_intensity_raw_*.jsonl")
    
    transformed_files = []
    
    # Transform power files
    for raw_file in power_raw_files:
        print(f"🔄 Transforming power file: {raw_file}")
        
        # Load raw data
        raw_data = []
        with open(raw_file, "r") as f:
            for line in f:
                if line.strip():
                    raw_data.append(json.loads(line))
        
        # Transform
        power_df = transform_power_breakdown(raw_data)
        
        # Save transformed data
        date_part = raw_file.split("_")[-1].replace(".jsonl", "")
        transformed_file = f"transformed/power_breakdown_transformed_{date_part}.jsonl"
        
        with open(transformed_file, "w") as f:
            for _, row in power_df.iterrows():
                # Convert pandas row to dict and handle datetime
                row_dict = row.to_dict()
                row_dict["datetime"] = row_dict["datetime"].isoformat()
                f.write(json.dumps(row_dict) + "\n")
        
        print(f"💾 Saved transformed power data: {transformed_file}")
        transformed_files.append(transformed_file)
    
    # Transform carbon files
    for raw_file in carbon_raw_files:
        print(f"🔄 Transforming carbon file: {raw_file}")
        
        # Load raw data
        raw_data = []
        with open(raw_file, "r") as f:
            for line in f:
                if line.strip():
                    raw_data.append(json.loads(line))
        
        # Transform
        carbon_df = transform_carbon_intensity(raw_data)
        
        # Save transformed data
        date_part = raw_file.split("_")[-1].replace(".jsonl", "")
        transformed_file = f"transformed/carbon_intensity_transformed_{date_part}.jsonl"
        
        with open(transformed_file, "w") as f:
            for _, row in carbon_df.iterrows():
                # Convert pandas row to dict and handle datetime
                row_dict = row.to_dict()
                row_dict["datetime"] = row_dict["datetime"].isoformat()
                if pd.notna(row_dict.get("updatedAt")):
                    row_dict["updatedAt"] = row_dict["updatedAt"].isoformat()
                if pd.notna(row_dict.get("createdAt")):
                    row_dict["createdAt"] = row_dict["createdAt"].isoformat()
                f.write(json.dumps(row_dict) + "\n")
        
        print(f"💾 Saved transformed carbon data: {transformed_file}")
        transformed_files.append(transformed_file)
    
    print("✅ Step 2 completed - Data transformed")
    return transformed_files

# === STEP 3: LOAD TO DATABASE ===
def load_all_transformed_data_to_database():
    """Step 3: Load ALL transformed JSONL files to database (comprehensive approach)"""
    print(f"\n🔄 STEP 3: Loading ALL transformed data to database")
    print("=" * 60)
    
    repo = EnergyDataRepository()
    
    try:
        # Find ALL transformed JSONL files
        power_files = glob.glob("transformed/power_breakdown_transformed_*.jsonl")
        carbon_files = glob.glob("transformed/carbon_intensity_transformed_*.jsonl")
        
        print(f"📁 Found {len(power_files)} power files and {len(carbon_files)} carbon files")
        
        # === LOAD ALL POWER DATA ===
        all_power_records = []
        
        for transformed_file in sorted(power_files):
            print(f"📥 Reading power file: {transformed_file}")
            
            file_records = []
            with open(transformed_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            record = json.loads(line)
                            file_records.append(record)
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Skipping invalid JSON on line {line_num}: {e}")
            
            print(f"   📊 Loaded {len(file_records)} power records")
            all_power_records.extend(file_records)
        
        # Process all power data
        if all_power_records:
            print(f"\n🔄 Processing {len(all_power_records)} total power records...")
            
            # Convert to DataFrame 
            power_df = pd.DataFrame(all_power_records)
            power_df["datetime"] = pd.to_datetime(power_df["datetime"])
            
            print(f"   📊 Total power records to process: {len(power_df)}")
            print(f"   📅 Time range: {power_df['datetime'].min()} → {power_df['datetime'].max()}")
            
            # Upsert logic
            repo.save_power_data(power_df)
        
        # === LOAD ALL CARBON DATA ===
        all_carbon_records = []
        
        for transformed_file in sorted(carbon_files):
            print(f"\n📥 Reading carbon file: {transformed_file}")
            
            file_records = []
            with open(transformed_file, "r") as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            record = json.loads(line)
                            file_records.append(record)
                        except json.JSONDecodeError as e:
                            print(f"⚠️ Skipping invalid JSON on line {line_num}: {e}")
            
            print(f"   📊 Loaded {len(file_records)} carbon records")
            all_carbon_records.extend(file_records)
        
        # Process all carbon data 
        if all_carbon_records:
            print(f"\n🔄 Processing {len(all_carbon_records)} total carbon records...")
            
            # Convert to DataFrame - keep ALL records, let database handle duplicates
            carbon_df = pd.DataFrame(all_carbon_records)
            carbon_df["datetime"] = pd.to_datetime(carbon_df["datetime"])
            
            # Handle other datetime columns
            if "updatedAt" in carbon_df.columns:
                carbon_df["updatedAt"] = pd.to_datetime(carbon_df["updatedAt"])
            if "createdAt" in carbon_df.columns:
                carbon_df["createdAt"] = pd.to_datetime(carbon_df["createdAt"])
            
            print(f"   📊 Total carbon records to process: {len(carbon_df)}")
            print(f"   📅 Time range: {carbon_df['datetime'].min()} → {carbon_df['datetime'].max()}")
            
            # Upsert logic
            repo.save_carbon_data(carbon_df)
        
        # === SUMMARY ===
        print(f"\n✅ ALL transformed data loaded successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error loading transformed data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        repo.close()

# === MAIN PIPELINE ===
def run_full_pipeline():
    """Run the complete pipeline: Fetch → Transform → Load"""
    print("🚀 Starting Full Data Pipeline")
    print("=" * 50)
    
    try:
        # Step 1: Fetch raw data
        fetch_and_save_raw_data()
        
        # Step 2: Transform data
        transform_and_save_data()
        
        # Step 3: Load to database
        load_all_transformed_data_to_database()
        
        print("\n🎉 Pipeline completed successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"💥 Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

# === INDIVIDUAL STEP FUNCTIONS ===
def run_step_1_only():
    """Run only Step 1: Fetch and save raw data"""
    fetch_and_save_raw_data()

def run_step_2_only():
    """Run only Step 2: Transform existing raw data"""
    transform_and_save_data()

def run_step_3_only():
    """Run only Step 3: Load existing transformed data to database"""
    load_all_transformed_data_to_database()

# === EXISTING TRANSFORM FUNCTIONS ===
def transform_power_breakdown(raw_data: list) -> pd.DataFrame:
    """Transforms raw power breakdown JSON into flat, clean DataFrame."""
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
    """Transforms raw carbon intensity JSON into flat, clean DataFrame."""
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


 
if __name__ == "__main__":
    # Run the full pipeline
    run_full_pipeline()


    # run_step_1_only()  # Just fetch
    # run_step_2_only()  # Just transform
    # run_step_3_only()  # Just load to DB
