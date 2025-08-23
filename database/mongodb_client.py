from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

class MongoDBClient:
    def __init__(self):
        self.connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        self.database_name = os.getenv("MONGODB_DATABASE")
        self.client = None
        self.db = None
    
    def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            # Test connection
            self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {self.database_name}")
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client is not None:
            self.client.close()
            print("🔌 MongoDB connection closed")
    
    def get_collection(self, collection_name):
        """Get a specific collection"""
        if self.db is None:
            raise Exception("Database not connected")
        return self.db[collection_name]
    
    def insert_documents(self, collection_name, documents):
        """Insert multiple documents"""
        collection = self.get_collection(collection_name)
        
        # Convert pandas timestamps to datetime objects
        for doc in documents:
            for key, value in doc.items():
                if pd.isna(value):
                    doc[key] = None
                elif isinstance(value, pd.Timestamp):
                    doc[key] = value.to_pydatetime()
        
        result = collection.insert_many(documents)
        print(f"📥 Inserted {len(result.inserted_ids)} documents into {collection_name}")
        return result.inserted_ids
    
    def find_latest_records(self, collection_name, limit=10):
        """Get latest records by datetime"""
        collection = self.get_collection(collection_name)
        cursor = collection.find().sort("datetime", -1).limit(limit)
        return list(cursor)
    
    def find_by_date_range(self, collection_name, start_date, end_date):
        """Find records within date range"""
        collection = self.get_collection(collection_name)
        query = {
            "datetime": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        return list(collection.find(query).sort("datetime", 1))
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Power data indexes
            power_collection = self.get_collection("power_data")
            power_collection.create_index([("datetime", 1)])
            power_collection.create_index([("zone", 1)])
            power_collection.create_index([("datetime", 1), ("zone", 1)])
            
            # Carbon intensity indexes
            carbon_collection = self.get_collection("carbon_intensity")
            carbon_collection.create_index([("datetime", 1)])
            carbon_collection.create_index([("zone", 1)])
            carbon_collection.create_index([("datetime", 1), ("zone", 1)])
            
            print("📊 Database indexes created successfully")
        except Exception as e:
            print(f"❌ Error creating indexes: {e}")