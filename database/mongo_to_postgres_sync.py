import os
import pandas as pd
import pymongo
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

class MongoToPostgresSync:
    """Sync MongoDB data to PostgreSQL for Grafana visualization"""
    
    def __init__(self):
        load_dotenv()
        
        # MongoDB connection
        self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
        self.mongo_db = self.mongo_client["neutrino_energy"]
        
        # PostgreSQL connection
        self.pg_conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=os.getenv("POSTGRES_PORT")
        )
        
        self.setup_postgres_tables()
    
    def setup_postgres_tables(self):
        """Create PostgreSQL tables for energy data"""
        
        power_table_sql = """
        CREATE TABLE IF NOT EXISTS power_data (
            id SERIAL PRIMARY KEY,
            datetime TIMESTAMP WITH TIME ZONE NOT NULL,
            zone VARCHAR(10) NOT NULL,
            power_consumption_total INTEGER,
            production_nuclear INTEGER,
            production_geothermal INTEGER,
            production_biomass INTEGER,
            production_coal INTEGER,
            production_wind INTEGER,
            production_solar INTEGER,
            production_hydro INTEGER,
            production_gas INTEGER,
            production_oil INTEGER,
            production_unknown INTEGER,
            production_hydro_discharge INTEGER,
            production_battery_discharge INTEGER,
            fossil_total INTEGER,
            renewable_total INTEGER,
            total_generation INTEGER,
            percent_renewable DECIMAL(5,2),
            percent_fossil DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(datetime, zone)
        );
        """
        
        carbon_table_sql = """
        CREATE TABLE IF NOT EXISTS carbon_intensity (
            id SERIAL PRIMARY KEY,
            datetime TIMESTAMP WITH TIME ZONE NOT NULL,
            zone VARCHAR(10) NOT NULL,
            carbon_intensity INTEGER,
            updated_at_source TIMESTAMP WITH TIME ZONE,
            created_at_source TIMESTAMP WITH TIME ZONE,
            emission_factor_type VARCHAR(50),
            is_estimated BOOLEAN,
            estimation_method VARCHAR(100),
            temporal_granularity VARCHAR(20),
            carbon_level VARCHAR(20),
            hours_since_update DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(datetime, zone)
        );
        """
        
        # Create indexes for better query performance
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_power_datetime ON power_data(datetime);",
            "CREATE INDEX IF NOT EXISTS idx_power_zone ON power_data(zone);",
            "CREATE INDEX IF NOT EXISTS idx_carbon_datetime ON carbon_intensity(datetime);",
            "CREATE INDEX IF NOT EXISTS idx_carbon_zone ON carbon_intensity(zone);"
        ]
        
        with self.pg_conn.cursor() as cursor:
            cursor.execute(power_table_sql)
            cursor.execute(carbon_table_sql)
            
            for index_sql in indexes_sql:
                cursor.execute(index_sql)
                
            self.pg_conn.commit()
        
        print("✅ PostgreSQL tables created/verified")
    
    def sync_power_data(self):
        """Sync power data from MongoDB to PostgreSQL"""
        print("🔄 Syncing power data...")
        
        # Get all power data from MongoDB
        power_collection = self.mongo_db["power_data"]
        mongo_data = list(power_collection.find())
        
        if not mongo_data:
            print("⚠️ No power data found in MongoDB")
            return
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(mongo_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Prepare data for PostgreSQL
        insert_sql = """
        INSERT INTO power_data (
            datetime, zone, power_consumption_total,
            production_nuclear, production_geothermal, production_biomass,
            production_coal, production_wind, production_solar, production_hydro,
            production_gas, production_oil, production_unknown,
            production_hydro_discharge, production_battery_discharge,
            fossil_total, renewable_total, total_generation,
            percent_renewable, percent_fossil
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (datetime, zone) DO UPDATE SET
            power_consumption_total = EXCLUDED.power_consumption_total,
            production_nuclear = EXCLUDED.production_nuclear,
            production_geothermal = EXCLUDED.production_geothermal,
            production_biomass = EXCLUDED.production_biomass,
            production_coal = EXCLUDED.production_coal,
            production_wind = EXCLUDED.production_wind,
            production_solar = EXCLUDED.production_solar,
            production_hydro = EXCLUDED.production_hydro,
            production_gas = EXCLUDED.production_gas,
            production_oil = EXCLUDED.production_oil,
            production_unknown = EXCLUDED.production_unknown,
            production_hydro_discharge = EXCLUDED.production_hydro_discharge,
            production_battery_discharge = EXCLUDED.production_battery_discharge,
            fossil_total = EXCLUDED.fossil_total,
            renewable_total = EXCLUDED.renewable_total,
            total_generation = EXCLUDED.total_generation,
            percent_renewable = EXCLUDED.percent_renewable,
            percent_fossil = EXCLUDED.percent_fossil,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        with self.pg_conn.cursor() as cursor:
            for _, row in df.iterrows():
                cursor.execute(insert_sql, (
                    row['datetime'], row['zone'], row.get('powerConsumptionTotal'),
                    row.get('production_nuclear', 0), row.get('production_geothermal', 0),
                    row.get('production_biomass', 0), row.get('production_coal', 0),
                    row.get('production_wind', 0), row.get('production_solar', 0),
                    row.get('production_hydro', 0), row.get('production_gas', 0),
                    row.get('production_oil', 0), row.get('production_unknown', 0),
                    row.get('production_hydro discharge', 0), row.get('production_battery discharge', 0),
                    row.get('fossil_total', 0), row.get('renewable_total', 0),
                    row.get('total_generation', 0), row.get('percent_renewable', 0),
                    row.get('percent_fossil', 0)
                ))
            
            self.pg_conn.commit()
        
        print(f"✅ Synced {len(df)} power records to PostgreSQL")
    
    def sync_carbon_data(self):
        """Sync carbon data from MongoDB to PostgreSQL"""
        print("🔄 Syncing carbon data...")
        
        # Get all carbon data from MongoDB
        carbon_collection = self.mongo_db["carbon_intensity"]
        mongo_data = list(carbon_collection.find())
        
        if not mongo_data:
            print("⚠️ No carbon data found in MongoDB")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(mongo_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Handle datetime fields
        if 'updatedAt' in df.columns:
            df['updatedAt'] = pd.to_datetime(df['updatedAt'])
        if 'createdAt' in df.columns:
            df['createdAt'] = pd.to_datetime(df['createdAt'])
        
        insert_sql = """
        INSERT INTO carbon_intensity (
            datetime, zone, carbon_intensity, updated_at_source, created_at_source,
            emission_factor_type, is_estimated, estimation_method, temporal_granularity,
            carbon_level, hours_since_update
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (datetime, zone) DO UPDATE SET
            carbon_intensity = EXCLUDED.carbon_intensity,
            updated_at_source = EXCLUDED.updated_at_source,
            created_at_source = EXCLUDED.created_at_source,
            emission_factor_type = EXCLUDED.emission_factor_type,
            is_estimated = EXCLUDED.is_estimated,
            estimation_method = EXCLUDED.estimation_method,
            temporal_granularity = EXCLUDED.temporal_granularity,
            carbon_level = EXCLUDED.carbon_level,
            hours_since_update = EXCLUDED.hours_since_update,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        with self.pg_conn.cursor() as cursor:
            for _, row in df.iterrows():
                cursor.execute(insert_sql, (
                    row['datetime'], row['zone'], row.get('carbonIntensity'),
                    row.get('updatedAt'), row.get('createdAt'),
                    row.get('emissionFactorType'), row.get('isEstimated'),
                    row.get('estimationMethod'), row.get('temporalGranularity'),
                    row.get('carbon_level'), row.get('hours_since_update')
                ))
            
            self.pg_conn.commit()
        
        print(f"✅ Synced {len(df)} carbon records to PostgreSQL")
    
    def run_full_sync(self):
        """Run complete sync from MongoDB to PostgreSQL"""
        try:
            print("🚀 Starting MongoDB → PostgreSQL sync")
            self.sync_power_data()
            self.sync_carbon_data()
            print("✅ Sync completed successfully!")
            
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            raise
        finally:
            self.mongo_client.close()
            self.pg_conn.close()

if __name__ == "__main__":
    sync = MongoToPostgresSync()
    sync.run_full_sync()
