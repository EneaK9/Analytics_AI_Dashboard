"""
Internal Scheduler for API Sync and SKU Analysis Jobs
This runs INSIDE the FastAPI application - no external cron needed!
Perfect for deployment on any platform (Heroku, Render, etc.)
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our cron job modules
import api_sync_cron
import sku_analysis_cron

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/internal_scheduler.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class InternalScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        logger.info("Internal Scheduler initialized - PERFECT VERSION!")
    
    def start_scheduler(self):
        """Start the internal scheduler with all cron jobs"""
        try:
            # API Sync Job - Every 2 hours
            self.scheduler.add_job(
                func=self._run_api_sync,
                trigger=IntervalTrigger(hours=2),
                id='api_sync_job',
                name='API Sync Job (Every 2 hours)',
                replace_existing=True,
                max_instances=1,  # Only one instance at a time
                next_run_time=datetime.now()  # Start immediately
            )
            
            # SKU Analysis Job - Every 2 hours (offset by 30 minutes)
            self.scheduler.add_job(
                func=self._run_sku_analysis,
                trigger=IntervalTrigger(hours=2, minutes=30),  # Offset by 30 minutes
                id='sku_analysis_job', 
                name='SKU Analysis Job (Every 2 hours + 30min offset)',
                replace_existing=True,
                max_instances=1,
                next_run_time=datetime.now().replace(minute=30, second=0, microsecond=0)
            )
            
            # Start the scheduler
            self.scheduler.start()
            
            logger.info("INTERNAL SCHEDULER STARTED SUCCESSFULLY!")
            logger.info("API Sync: Every 2 hours (starting now)")
            logger.info("SKU Analysis: Every 2 hours (starting in 30 minutes)")
            logger.info("All jobs will run automatically - NO EXTERNAL CRON NEEDED!")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            raise
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Internal scheduler stopped")
    
    def get_jobs_status(self):
        """Get status of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    async def _run_api_sync(self):
        """Wrapper to run API sync job"""
        try:
            logger.info("STARTING SCHEDULED API SYNC JOB...")
            
            # Create and run the API sync cron job
            api_cron = api_sync_cron.APISyncCronJob()
            results = await api_cron.run_full_sync()
            
            logger.info(f"API Sync completed: {results}")
            
        except Exception as e:
            logger.error(f"API Sync job failed: {str(e)}")
    
    async def _run_sku_analysis(self):
        """Wrapper to run SKU analysis job"""
        try:
            logger.info("STARTING SCHEDULED SKU ANALYSIS JOB...")
            
            # Run SKU analysis for all clients
            await asyncio.to_thread(sku_analysis_cron.run_sku_analysis_for_all_clients)
            
            logger.info("SKU Analysis completed")
            
        except Exception as e:
            logger.error(f"SKU Analysis job failed: {str(e)}")

# Global scheduler instance
scheduler_instance = InternalScheduler()

def start_internal_scheduler():
    """Function to start the scheduler - called from FastAPI app"""
    scheduler_instance.start_scheduler()

def stop_internal_scheduler():
    """Function to stop the scheduler"""
    scheduler_instance.stop_scheduler()

def get_scheduler_status():
    """Get scheduler status"""
    return scheduler_instance.get_jobs_status()

# For testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        logger.info("Testing Internal Scheduler...")
        scheduler_instance.start_scheduler()
        
        # Keep running for testing
        while True:
            await asyncio.sleep(60)  # Check every minute
    
    asyncio.run(main())
