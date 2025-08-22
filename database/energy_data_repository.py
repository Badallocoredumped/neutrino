from .mongodb_client import MongoDBClient
from datetime import datetime
import pandas as pd

class EnergyDataRepository:
    def __init__(self):
        self.mongo_client = MongoDBClient()
        self.mongo_client.connect()
        self.mongo_client.create_indexes()
    
    def save_power_data(self, power_df: pd.DataFrame):
        """Save power breakdown data to MongoDB"""
        documents = power_df.to_dict('records')
        
        # Add metadata
        for doc in documents:
            doc['inserted_at'] = datetime.utcnow()
            doc['data_type'] = 'power_breakdown'
        
        # Save to MongoDB
        mongo_result = self.mongo_client.insert_documents("power_data", documents.copy())
        return mongo_result
    
    def save_carbon_data(self, carbon_df: pd.DataFrame):
        """Save carbon intensity data to MongoDB"""
        documents = carbon_df.to_dict('records')
        
        # Add metadata
        for doc in documents:
            doc['inserted_at'] = datetime.utcnow()
            doc['data_type'] = 'carbon_intensity'
        
        # Save to MongoDB
        mongo_result = self.mongo_client.insert_documents("carbon_intensity", documents.copy())
        return mongo_result
    
    def get_latest_power_data(self, hours=24):
        """Get power data from last N hours"""
        return self.mongo_client.find_latest_records("power_data", limit=hours)
    
    def get_latest_carbon_data(self, hours=24):
        """Get carbon data from last N hours"""
        return self.mongo_client.find_latest_records("carbon_intensity", limit=hours)
    
    def get_power_data_by_zone(self, zone, start_date, end_date):
        """Get power data for specific zone and date range"""
        collection = self.mongo_client.get_collection("power_data")
        query = {
            "zone": zone,
            "datetime": {"$gte": start_date, "$lte": end_date}
        }
        return list(collection.find(query).sort("datetime", 1))
    
    def get_carbon_summary_stats(self, zone=None):
        """Get carbon intensity summary statistics"""
        collection = self.mongo_client.get_collection("carbon_intensity")
        
        pipeline = []
        if zone:
            pipeline.append({"$match": {"zone": zone}})
        
        pipeline.extend([
            {
                "$group": {
                    "_id": "$zone",
                    "avg_carbon_intensity": {"$avg": "$carbonIntensity"},
                    "min_carbon_intensity": {"$min": "$carbonIntensity"},
                    "max_carbon_intensity": {"$max": "$carbonIntensity"},
                    "count": {"$sum": 1}
                }
            }
        ])
        
        return list(collection.aggregate(pipeline))
    
    def close(self):
        """Close database connections"""
        self.mongo_client.disconnect()