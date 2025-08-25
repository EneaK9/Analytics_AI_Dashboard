"""
Internal Scheduler for API Sync and SKU Analysis Jobs
This runs INSIDE the FastAPI application - no external cron needed!
Perfect for deployment on any platform (Heroku, Render, etc.)
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import asyncio
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our cron job modules
import api_sync_cron
import sku_analysis_cron
import analytics_refresh_cron

# Set up logging with safe file handling
handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler, but don't fail if logs directory doesn't exist
try:
    os.makedirs('logs', exist_ok=True)
    handlers.append(logging.FileHandler('logs/internal_scheduler.log', encoding='utf-8'))
except (OSError, PermissionError) as e:
    # Fall back to stdout-only logging in deployment environments
    print(f"Warning: Could not create scheduler log file, using stdout only: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

class InternalScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        logger.info("Internal Scheduler initialized - PERFECT VERSION!")
    
    def start_scheduler(self):
        """Start the internal scheduler with all cron jobs"""
        try:
            logger.info("ATTEMPTING TO START INTERNAL SCHEDULER...")
            logger.info(f"Current process ID: {os.getpid()}")
            logger.info(f"Current working directory: {os.getcwd()}")
            
            # API Sync Job - Daily at 4 AM
            logger.info("Scheduling API sync job to run daily at 4:00 AM")
            
            self.scheduler.add_job(
                func=self._run_api_sync,
                trigger=CronTrigger(hour=4, minute=0),  # Daily at 4 AM
                id='api_sync_job',
                name='API Sync Job (Daily at 4:00 AM)',
                replace_existing=True,
                max_instances=1,  # Only one instance at a time
                next_run_time=None  # Let scheduler determine next run
            )
            logger.info("API sync job scheduled successfully")
            
            # SKU Analysis Job - Daily at 4:15 AM
            logger.info("Scheduling SKU analysis job to run daily at 4:15 AM")
            
            self.scheduler.add_job(
                func=self._run_sku_analysis,
                trigger=CronTrigger(hour=4, minute=15),  # Daily at 4:15 AM
                id='sku_analysis_job', 
                name='SKU Analysis Job (Daily at 4:15 AM)',
                replace_existing=True,
                max_instances=1,
                next_run_time=None  # Let scheduler determine next run
            )
            logger.info("SKU analysis job scheduled successfully")
            
            # Analytics Refresh Job - Daily at 4:30 AM
            logger.info("Scheduling analytics refresh job to run daily at 4:30 AM")
            
            self.scheduler.add_job(
                func=self._run_analytics_refresh,
                trigger=CronTrigger(hour=4, minute=30),  # Daily at 4:30 AM
                id='analytics_refresh_job',
                name='Analytics Refresh Job (Daily at 4:30 AM)', 
                replace_existing=True,
                max_instances=1,
                next_run_time=None  # Let scheduler determine next run
            )
            logger.info("Analytics refresh job scheduled successfully")
            
            # Start the scheduler
            logger.info("Starting APScheduler...")
            self.scheduler.start()
            logger.info("APScheduler started successfully!")
            
            # Log all scheduled jobs
            jobs = self.scheduler.get_jobs()
            logger.info(f"Total scheduled jobs: {len(jobs)}")
            for job in jobs:
                logger.info(f"Job: {job.name} | Next run: {job.next_run_time}")
            
            logger.info("INTERNAL SCHEDULER FULLY OPERATIONAL!")
            logger.info("API Sync: Daily at 4:00 AM")
            logger.info("SKU Analysis: Daily at 4:15 AM")
            logger.info("Analytics Refresh: Daily at 4:30 AM")
            logger.info("All jobs will run automatically - NO EXTERNAL CRON NEEDED!")
            
        except Exception as e:
            logger.error(f"CRITICAL ERROR: Failed to start scheduler: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Internal scheduler stopped")
            
    def get_jobs_status(self):
        """Get detailed status of scheduled jobs"""
        try:
            if not self.scheduler:
                return {"status": "not_initialized", "error": "Scheduler not found", "jobs": []}
                
            if not self.scheduler.running:
                return {"status": "stopped", "jobs": [], "message": "Scheduler is not running"}
            
            jobs = self.scheduler.get_jobs()
            job_info = []
            for job in jobs:
                job_info.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                    "max_instances": getattr(job, 'max_instances', 'unknown'),
                    "func_name": job.func.__name__ if hasattr(job, 'func') else 'unknown'
                })
            
            return {
                "status": "running",
                "scheduler_state": str(self.scheduler.state),
                "jobs": job_info,
                "total_jobs": len(jobs),
                "process_id": os.getpid(),
                "message": f"Scheduler running with {len(jobs)} jobs"
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                "status": "error", 
                "error": str(e),
                "jobs": [],
                "message": "Failed to get scheduler status"
            }
    

    
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
            
            # Create and run the SKU analysis cron job
            sku_cron = sku_analysis_cron.SKUAnalysisCronJob()
            results = await sku_cron.run_full_analysis()
            
            logger.info(f"SKU Analysis results: {results}")
            logger.info("SKU Analysis completed")
            
        except Exception as e:
            logger.error(f"SKU Analysis job failed: {str(e)}")
    
    async def _run_analytics_refresh(self):
        """Wrapper to run analytics refresh job"""
        try:
            logger.info("STARTING SCHEDULED ANALYTICS REFRESH JOB...")
            
            # Create and run the analytics refresh cron job
            analytics_cron = analytics_refresh_cron.AnalyticsRefreshCronJob()
            results = await analytics_cron.run_full_analytics_refresh()
            
            logger.info(f"Analytics Refresh results: {results}")
            
            logger.info("Analytics Refresh completed")
            
        except Exception as e:
            logger.error(f"Analytics Refresh job failed: {str(e)}")

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
