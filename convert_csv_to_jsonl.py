import pandas as pd
import json
import glob
import os
from datetime import datetime

def convert_csv_to_jsonl(csv_file_path):
    """
    Convert a CSV file to JSONL format with proper datetime handling
    """
    print(f"🔄 Converting: {csv_file_path}")
    
    # Read CSV with semicolon separator
    df = pd.read_csv(csv_file_path, sep=';')
    
    # Convert datetime column to proper datetime format
    if 'datetime' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
    
    # Convert other datetime columns if they exist
    datetime_columns = ['updatedAt', 'createdAt']
    for col in datetime_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    # Generate output filename (replace .csv with .jsonl)
    output_file = csv_file_path.replace('.csv', '.jsonl')
    
    # Write to JSONL format
    with open(output_file, 'w') as f:
        for _, row in df.iterrows():
            # Convert row to dictionary
            row_dict = row.to_dict()
            
            # Convert datetime objects to ISO format strings
            for key, value in row_dict.items():
                if pd.notna(value) and hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
                elif pd.isna(value):
                    row_dict[key] = None
            
            # Write JSON line
            f.write(json.dumps(row_dict) + '\n')
    
    print(f"✅ Converted to: {output_file}")
    print(f"📊 Records: {len(df)}")
    return output_file

def convert_all_csv_files():
    """
    Convert all CSV files in the transformed folder to JSONL
    """
    print("🚀 Starting CSV to JSONL conversion")
    print("=" * 50)
    
    # Find all CSV files in transformed folder
    csv_files = glob.glob("transformed/*.csv")
    
    if not csv_files:
        print("❌ No CSV files found in transformed/ folder")
        return
    
    converted_files = []
    total_records = 0
    
    for csv_file in csv_files:
        try:
            output_file = convert_csv_to_jsonl(csv_file)
            converted_files.append(output_file)
            
            # Count records for summary
            with open(output_file, 'r') as f:
                record_count = sum(1 for line in f if line.strip())
                total_records += record_count
            
            print()
            
        except Exception as e:
            print(f"❌ Error converting {csv_file}: {e}")
            continue
    
    # Summary
    print("=" * 50)
    print(f"✅ Conversion completed!")
    print(f"📁 Files converted: {len(converted_files)}")
    print(f"📊 Total records: {total_records}")
    print("\n📋 Converted files:")
    for file in converted_files:
        print(f"   • {file}")

def convert_specific_files():
    """
    Convert specific CSV files (for your current case)
    """
    files_to_convert = [
        "transformed/carbon_intensity_transformed_20250822.csv",
        "transformed/power_breakdown_transformed_20250822.csv"
    ]
    
    print("🎯 Converting specific CSV files")
    print("=" * 50)
    
    for csv_file in files_to_convert:
        if os.path.exists(csv_file):
            try:
                convert_csv_to_jsonl(csv_file)
                print()
            except Exception as e:
                print(f"❌ Error converting {csv_file}: {e}")
        else:
            print(f"⚠️ File not found: {csv_file}")
    
    print("✅ Specific file conversion completed!")

def preview_converted_data(jsonl_file, num_lines=3):
    """
    Preview the converted JSONL data
    """
    print(f"\n👀 Preview of {jsonl_file}:")
    print("-" * 40)
    
    try:
        with open(jsonl_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= num_lines:
                    break
                if line.strip():
                    data = json.loads(line)
                    print(f"Record {i+1}:")
                    print(json.dumps(data, indent=2))
                    print()
    except Exception as e:
        print(f"❌ Error previewing file: {e}")

if __name__ == "__main__":
    # Option 1: Convert all CSV files in transformed folder
    # convert_all_csv_files()
    
    # Option 2: Convert specific files (your current case)
    convert_specific_files()
    
    # Option 3: Preview converted data
    preview_files = [
        "transformed/carbon_intensity_transformed_20250822.jsonl",
        "transformed/power_breakdown_transformed_20250822.jsonl"
    ]
    
    for file in preview_files:
        if os.path.exists(file):
            preview_converted_data(file, num_lines=2)