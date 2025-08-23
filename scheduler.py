import schedule
import time
import logging
from datetime import datetime
import traceback
from etl_energy_data import run_full_pipeline

def setup_logging():
    """Setup logging for the scheduler"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('energy_pipeline_scheduler.log'),
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
        
        # Optional: Send alert email/notification here
        # send_failure_notification(str(e))

def send_failure_notification(error_message):
    """Optional: Send notification when pipeline fails"""
    # You can implement email alerts, Slack notifications, etc.
    pass

def main():
    """Main scheduler function"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Starting Energy Data Pipeline Scheduler")
    logger.info("📅 Schedule: Every hour at minute 5")
    
    # Schedule the job to run every hour at 5 minutes past the hour
    # This gives some buffer time for API data to be available
    schedule.every().hour.at(":05").do(run_pipeline_job)
    
    # Optional: Run immediately on startup for testing
    logger.info("🔄 Running initial pipeline...")
    run_pipeline_job()
    
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