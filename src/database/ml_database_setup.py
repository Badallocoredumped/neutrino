"""
ML Database Setup
Creates all necessary PostgreSQL tables for the ML prediction pipeline:
- epias_power_consumption (input data from EPİAŞ API)
- predictions (ML model outputs)
- evaluation_metrics (model performance tracking)
- model_metadata (model versions and info)
"""

import os
import psycopg2
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLDatabaseSetup:
    """Setup all PostgreSQL tables for ML prediction pipeline"""
    
    def __init__(self):
        """Initialize PostgreSQL connection"""
        self.pg_conn = None
        
    def connect(self):
        """Establish connection to PostgreSQL database"""
        try:
            self.pg_conn = psycopg2.connect(
                host=os.getenv("POSTGRES_HOST_DEV"),
                database=os.getenv("POSTGRES_DB_DEV"),
                user=os.getenv("POSTGRES_USER_DEV"),
                password=os.getenv("POSTGRES_PASSWORD_DEV"),
                port=os.getenv("POSTGRES_PORT_DEV")
            )
            self.pg_conn.autocommit = True
            logger.info("✅ Connected to PostgreSQL for ML database setup")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.pg_conn:
            self.pg_conn.close()
            logger.info("🔌 Disconnected from PostgreSQL")
    
    def create_consumption_table(self):
        """Create EPİAŞ power consumption table (input data)"""
        try:
            cursor = self.pg_conn.cursor()
            
            consumption_table_sql = """
            CREATE TABLE IF NOT EXISTS epias_power_consumption (
                id SERIAL PRIMARY KEY,
                datetime TIMESTAMP WITH TIME ZONE NOT NULL,
                consumption_mwh NUMERIC NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(datetime)
            );
            """
            
            cursor.execute(consumption_table_sql)
            logger.info("✅ Created epias_power_consumption table")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating consumption table: {e}")
            return False
    
    def create_predictions_table(self):
        """Create predictions table (ML model outputs)"""
        try:
            cursor = self.pg_conn.cursor()
            
            predictions_table_sql = """
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                datetime TIMESTAMP WITH TIME ZONE NOT NULL,
                predicted_consumption_mwh NUMERIC NOT NULL,
                model_version VARCHAR(50) NOT NULL,
                prediction_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence_score DECIMAL(3,2),
                prediction_horizon_hours INTEGER DEFAULT 1,
                UNIQUE(datetime, model_version, prediction_horizon_hours)
            );
            """
            
            cursor.execute(predictions_table_sql)
            logger.info("✅ Created predictions table")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating predictions table: {e}")
            return False
    
    def create_evaluation_metrics_table(self):
        """Create evaluation metrics table (model performance)"""
        try:
            cursor = self.pg_conn.cursor()
            
            metrics_table_sql = """
            CREATE TABLE IF NOT EXISTS evaluation_metrics (
                id SERIAL PRIMARY KEY,
                evaluation_date TIMESTAMP WITH TIME ZONE NOT NULL,
                model_version VARCHAR(50) NOT NULL,
                mae NUMERIC,
                rmse NUMERIC,
                mape NUMERIC,
                r2_score NUMERIC,
                data_points_count INTEGER,
                evaluation_period_start TIMESTAMP WITH TIME ZONE,
                evaluation_period_end TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(evaluation_date, model_version)
            );
            """
            
            cursor.execute(metrics_table_sql)
            logger.info("✅ Created evaluation_metrics table")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating evaluation_metrics table: {e}")
            return False
    
    def create_model_metadata_table(self):
        """Create model metadata table (model info and versions)"""
        try:
            cursor = self.pg_conn.cursor()
            
            metadata_table_sql = """
            CREATE TABLE IF NOT EXISTS model_metadata (
                model_version VARCHAR(50) PRIMARY KEY,
                model_type VARCHAR(50) NOT NULL,
                target_variable VARCHAR(50) DEFAULT 'consumption_mwh',
                training_start_date TIMESTAMP WITH TIME ZONE,
                training_end_date TIMESTAMP WITH TIME ZONE,
                feature_columns TEXT[],
                hyperparameters JSONB,
                training_mae NUMERIC,
                validation_mae NUMERIC,
                training_r2 NUMERIC,
                validation_r2 NUMERIC,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
            """
            
            cursor.execute(metadata_table_sql)
            logger.info("✅ Created model_metadata table")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating model_metadata table: {e}")
            return False
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        try:
            cursor = self.pg_conn.cursor()
            
            indexes = [
                # Consumption table indexes
                "CREATE INDEX IF NOT EXISTS idx_consumption_datetime ON epias_power_consumption(datetime);",
                "CREATE INDEX IF NOT EXISTS idx_consumption_created_at ON epias_power_consumption(created_at);",
                
                # Predictions table indexes
                "CREATE INDEX IF NOT EXISTS idx_predictions_datetime ON predictions(datetime);",
                "CREATE INDEX IF NOT EXISTS idx_predictions_model_version ON predictions(model_version);",
                "CREATE INDEX IF NOT EXISTS idx_predictions_horizon ON predictions(prediction_horizon_hours);",
                "CREATE INDEX IF NOT EXISTS idx_predictions_generated_at ON predictions(prediction_generated_at);",
                
                # Evaluation metrics indexes
                "CREATE INDEX IF NOT EXISTS idx_metrics_model_version ON evaluation_metrics(model_version);",
                "CREATE INDEX IF NOT EXISTS idx_metrics_evaluation_date ON evaluation_metrics(evaluation_date);",
                
                # Model metadata indexes
                "CREATE INDEX IF NOT EXISTS idx_metadata_active ON model_metadata(is_active);",
                "CREATE INDEX IF NOT EXISTS idx_metadata_created_at ON model_metadata(created_at);"
            ]
            
            for index_sql in indexes:
                cursor.execute(index_sql)
            
            logger.info("✅ Created all indexes")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating indexes: {e}")
            return False
    
    def setup_all_tables(self):
        """Setup all ML prediction tables and indexes"""
        logger.info("🚀 Starting ML database setup...")
        
        if not self.connect():
            logger.error("❌ Database connection failed")
            return False
        
        try:
            # Create all tables
            success = (
                self.create_consumption_table() and
                self.create_predictions_table() and
                self.create_evaluation_metrics_table() and
                self.create_model_metadata_table() and
                self.create_indexes()
            )
            
            if success:
                logger.info("🎉 All ML prediction tables created successfully!")
                self.verify_setup()
            else:
                logger.error("❌ Some tables failed to create")
                
            return success
            
        finally:
            self.disconnect()
    
    def verify_setup(self):
        """Verify that all tables were created successfully"""
        try:
            cursor = self.pg_conn.cursor()
            
            # Check if all tables exist
            expected_tables = [
                'epias_power_consumption',
                'predictions',
                'evaluation_metrics', 
                'model_metadata'
            ]
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN %s
            """, (tuple(expected_tables),))
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"📋 Existing tables: {existing_tables}")
            
            missing_tables = set(expected_tables) - set(existing_tables)
            if missing_tables:
                logger.warning(f"⚠️  Missing tables: {missing_tables}")
            else:
                logger.info("✅ All ML prediction tables verified successfully")
                
                # Count records in each table
                for table in existing_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    logger.info(f"📊 {table}: {count} records")
            
            cursor.close()
            
        except Exception as e:
            logger.error(f"❌ Error verifying tables: {e}")
    
    def drop_all_tables(self):
        """Drop all ML tables (use with caution!)"""
        if not self.connect():
            return False
        
        try:
            cursor = self.pg_conn.cursor()
            
            tables_to_drop = [
                'predictions',
                'evaluation_metrics',
                'model_metadata',
                'epias_power_consumption'
            ]
            
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                logger.info(f"🗑️ Dropped table: {table}")
            
            logger.info("🗑️ All ML tables dropped")
            cursor.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Error dropping tables: {e}")
            return False
        finally:
            self.disconnect()


def main():
    """Main function to setup ML database"""
    setup = MLDatabaseSetup()
    
    # Setup all tables
    print("🎯 Setting up ML prediction database...")
    if setup.setup_all_tables():
        print("\n✅ ML database setup completed successfully!")
        print("📊 Your ML prediction pipeline is ready!")
        print("\n🏗️ Created tables:")
        print("  • epias_power_consumption (input data)")
        print("  • predictions (model outputs)")
        print("  • evaluation_metrics (performance tracking)")
        print("  • model_metadata (model versions)")
    else:
        print("\n❌ ML database setup failed")


if __name__ == "__main__":
    main()