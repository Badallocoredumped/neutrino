import os
import psycopg2
from dotenv import load_dotenv

def test_postgres_connection():
    """Test PostgreSQL connection and create database if needed"""
    load_dotenv()
    
    try:
        # First try to connect to the specific database
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            database=os.getenv("POSTGRES_DB", "grafana_energy"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            port=os.getenv("POSTGRES_PORT", "5432")
        )
        print("✅ Connected to PostgreSQL database successfully!")
        
        # Test if we can create tables
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"📊 PostgreSQL version: {version[0]}")
            
        conn.close()
        return True
        
    except psycopg2.OperationalError as e:
        if "does not exist" in str(e):
            print(f"⚠️ Database 'grafana_energy' does not exist. Creating it...")
            try:
                # Connect to default postgres database to create our database
                conn = psycopg2.connect(
                    host=os.getenv("POSTGRES_HOST", "localhost"),
                    database="postgres",
                    user=os.getenv("POSTGRES_USER", "postgres"),
                    password=os.getenv("POSTGRES_PASSWORD", "password"),
                    port=os.getenv("POSTGRES_PORT", "5432")
                )
                conn.autocommit = True
                
                with conn.cursor() as cursor:
                    cursor.execute("CREATE DATABASE grafana_energy;")
                    print("✅ Database 'grafana_energy' created successfully!")
                
                conn.close()
                return True
                
            except Exception as create_error:
                print(f"❌ Failed to create database: {create_error}")
                return False
        else:
            print(f"❌ PostgreSQL connection failed: {e}")
            print("\n🔧 Please check:")
            print("1. PostgreSQL is installed and running")
            print("2. Database credentials in .env file are correct")
            print("3. PostgreSQL server is accessible on localhost:5432")
            return False
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_postgres_connection()
