import schedule
import time
import logging
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
    """Setup logging for the scheduler"""
    # Use the environment variable, fallback to /app/logs for Docker
    log_file = os.getenv(
        'LOG_FILE',
        '/app/logs/energy_pipeline_scheduler.log'
    )
    # Create log file path
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    print(f"📁 Setting up logging in: {log_dir}")
    print(f"📄 Log file: {log_file}")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

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
    """Collect today's EPİAŞ consumption data (all hours for the day)"""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🕐 Starting EPİAŞ daily data collection (all hours for today)")
        
        collector = EPIASConsumptionCollector()
        today = datetime.now().strftime("%Y-%m-%d")
        start_date = f"{today}T00:00:00+03:00"
        end_date = f"{today}T23:00:00+03:00"
        
        print(f"🔄 Collecting EPİAŞ data for: {start_date} to {end_date}")
        
        df = collector.collect_and_save_consumption_data(
            start_date=start_date,
            end_date=end_date,
            save_to_csv=False,
            save_to_db=True
        )
        
        if not df.empty:
            print(f"✅ Collected {len(df)} records for {today}")
            logger.info(f"✅ EPİAŞ daily data collected: {len(df)} records for {today}")
        else:
            logger.warning(f"⚠️ No EPİAŞ data collected for {today}")
        
    except Exception as e:
        logger.error(f"❌ EPİAŞ daily data collection failed: {e}")
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
    setup = MLDatabaseSetup()
    setup.setup_all_tables()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Energy Data Pipeline Scheduler")
    logger.info("📅 Electricity Maps Schedule: Every hour at minute 5")
    logger.info("📅 EPİAŞ Schedule: Daily at 02:00 + Hourly at minute 10")
    
    # Schedule the electricity maps job to run every hour at 5 minutes past the hour
    schedule.every().hour.at(":05").do(run_pipeline_job)
    
    # Schedule EPİAŞ jobs
    schedule.every().day.at("02:00").do(run_epias_daily_pipeline)  # Daily complete pipeline
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