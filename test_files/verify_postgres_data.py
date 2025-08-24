import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

def verify_postgres_data():
    """Verify what data is now available in PostgreSQL for Grafana"""
    load_dotenv()
    
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            database=os.getenv("POSTGRES_DB", "neutrino_energy"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        
        print("📊 PostgreSQL Database Verification")
        print("=" * 50)
        
        with conn.cursor() as cursor:
            # Check power data
            cursor.execute("SELECT COUNT(*) FROM power_data;")
            power_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(datetime), MAX(datetime) FROM power_data;")
            power_range = cursor.fetchone()
            
            print(f"🔋 Power Data:")
            print(f"   📊 Total records: {power_count:,}")
            print(f"   📅 Date range: {power_range[0]} → {power_range[1]}")
            
            # Check carbon data
            cursor.execute("SELECT COUNT(*) FROM carbon_intensity;")
            carbon_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT MIN(datetime), MAX(datetime) FROM carbon_intensity;")
            carbon_range = cursor.fetchone()
            
            print(f"\n🌡️ Carbon Intensity Data:")
            print(f"   📊 Total records: {carbon_count:,}")
            print(f"   📅 Date range: {carbon_range[0]} → {carbon_range[1]}")
            
            # Sample recent data
            print(f"\n📈 Recent Power Data (Last 5 hours):")
            cursor.execute("""
                SELECT datetime, percent_renewable, percent_fossil, total_generation 
                FROM power_data 
                ORDER BY datetime DESC 
                LIMIT 5;
            """)
            
            for row in cursor.fetchall():
                dt, renewable, fossil, total = row
                print(f"   {dt}: {renewable:.1f}% renewable, {fossil:.1f}% fossil, {total:,} MW")
            
            # Sample recent carbon data
            print(f"\n🌡️ Recent Carbon Data (Last 5 hours):")
            cursor.execute("""
                SELECT datetime, carbon_intensity, carbon_level 
                FROM carbon_intensity 
                ORDER BY datetime DESC 
                LIMIT 5;
            """)
            
            for row in cursor.fetchall():
                dt, intensity, level = row
                print(f"   {dt}: {intensity} gCO2/kWh ({level})")
        
        print(f"\n✅ PostgreSQL verification complete!")
        print(f"📊 Ready for Grafana visualization!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    verify_postgres_data()
