import schedule
import time
import logging
from logging import FileHandler, StreamHandler
from datetime import datetime, timedelta
import traceback
from src.etl_energy_data import run_full_pipeline
import os
import sys

# Add imports for EPİAŞ
sys.path.append(os.path.dirname(__file__))
from database.epias_consumption_manager import EPIASConsumptionCollector
from epias_energy_consumption_data import main as run_epias_pipeline, collect_last_n_days
from database.ml_database_setup import MLDatabaseSetup

def setup_logging():
    """Forcefully set up logging for the scheduler."""
    log_file = os.getenv('LOG_FILE', '/app/logs/energy_pipeline_scheduler.log')
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)

    print(f"📁 Setting up logging in: {log_dir}")
    print(f"📄 Log file: {log_file}")

    # Clear any existing handlers (important)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.setLevel(logging.INFO)

    # Create and attach file handler
    file_handler = FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # Also log to stdout
    stream_handler = StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(file_formatter)
    root_logger.addHandler(stream_handler)

    logging.info("✅ Logging system initialized and writing to log file.")

def run_pipeline_job():
    """Wrapper function to run the pipeline with error handling"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🕐 Starting scheduled pipeline run")
        start_time = datetime.now()
        
        # Run your existing pipeline
        run_full_pipeline()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Pipeline completed successfully in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")

def run_epias_current_hour():
    """Collect EPİAŞ consumption data accounting for 2-hour API delay"""
    logger = logging.getLogger(__name__)
    try:
        logger.info("🕐 Starting EPİAŞ hourly data collection (2 hours behind)")
        collector = EPIASConsumptionCollector()
        now = datetime.now()
        
        # Get the latest available data point (2 hours behind)
        latest_available_hour = now - timedelta(hours=2)
        
        # For LSTM prediction, we need 24 hours of data
        # So collect from 26 hours ago to 2 hours ago (24 hour window)
        start_time = latest_available_hour - timedelta(hours=23)  # 23 hours back + current = 24 hours
        end_time = latest_available_hour
        
        # Set precise time boundaries
        start_date = start_time.replace(minute=0, second=0, microsecond=0)
        end_date = end_time.replace(minute=59, second=59, microsecond=999999)
        
        start_date_str = start_date.strftime("%Y-%m-%dT%H:00:00Z")
        end_date_str = end_date.strftime("%Y-%m-%dT%H:00:00Z")
        
        print(f"🔄 Collecting EPİAŞ data for 24-hour window: {start_date_str} to {end_date_str}")
        print(f"📊 This gives us 24 hours of data to predict hour: {(latest_available_hour + timedelta(hours=1)).strftime('%H:00')}")
        
        df = collector.collect_and_save_consumption_data(
            start_date=start_date_str,
            end_date=end_date_str,
            save_to_csv=False,
            save_to_db=True
        )
        
        if not df.empty:
            print(f"✅ Collected {len(df)} records for 24-hour prediction window")
            logger.info(f"✅ EPİAŞ 24-hour data collected: {len(df)} records")
            
            # Validate we have exactly 24 hours of data
            if len(df) == 24:
                print(f"📈 Ready for LSTM prediction of hour: {(latest_available_hour + timedelta(hours=1)).strftime('%Y-%m-%d %H:00')}")
            else:
                logger.warning(f"⚠️ Expected 24 records, got {len(df)}. Check for missing data.")
                
        else:
            logger.warning(f"⚠️ No EPİAŞ data collected for the 24-hour window")
            
    except Exception as e:
        logger.error(f"❌ EPİAŞ 24-hour data collection failed: {e}")
        logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")

def run_epias_daily_pipeline():
    """Run the complete EPİAŞ pipeline (yesterday's data + CSV save)"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🕐 Starting daily EPİAŞ pipeline")
        print(f"\n{'='*60}")
        print(f"📊 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Running Daily EPİAŞ Pipeline")
        print(f"{'='*60}")
        
        # Run the main pipeline function
        run_epias_pipeline()
        
        print(f"✅ Daily EPİAŞ Pipeline completed successfully")
        logger.info("✅ Daily EPİAŞ Pipeline executed successfully")
        
    except Exception as e:
        logger.error(f"❌ Daily EPİAŞ Pipeline failed: {e}")
        logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
        print(f"❌ Daily EPİAŞ Pipeline failed: {e}")

def send_failure_notification(error_message):
    """Optional: Send notification when pipeline fails"""
    # You can implement email alerts, Slack notifications, etc.
    pass

def main():
    """Main scheduler function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    

    logger.info("🛠️ Running ML database setup")

    """ setup = MLDatabaseSetup()
    setup.setup_all_tables() """

    logger.info("✅ Database setup complete")  

    logger.info("🚀 Starting Energy Data Pipeline Scheduler")
    logger.info("📅 Electricity Maps Schedule: Every hour at minute 5")
    logger.info("📅 EPİAŞ Schedule: Daily at 02:00 + Hourly at minute 10")
    
    # Schedule the electricity maps job to run every hour at 5 minutes past the hour
    schedule.every().hour.at(":05").do(run_pipeline_job)
    
    # Schedule EPİAŞ jobs
    #schedule.every().day.at("02:00").do(run_epias_daily_pipeline)  # Daily complete pipeline
    schedule.every().hour.at(":10").do(run_epias_current_hour)    # Hourly updates
    
    # Optional: Run immediately on startup for testing
    logger.info("🔄 Running initial pipelines...")
    run_pipeline_job()
    run_epias_current_hour()
    
    print("\n📅 Complete Schedule:")
    print("   • Electricity Maps: Every hour at XX:05")
    print("   • EPİAŞ Daily Pipeline: Daily at 02:00 (yesterday's data + CSV)")
    print("   • EPİAŞ Hourly Updates: Every hour at XX:10")
    print("   • Timezone: Europe/Istanbul (UTC+3)")
    print("")
    
    logger.info("⏰ Scheduler is running... Press Ctrl+C to stop")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"💥 Scheduler crashed: {e}")
        raise

if __name__ == "__main__":
    main()