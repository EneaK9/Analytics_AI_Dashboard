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
            logger.info("ATTEMPTING TO START INTERNAL SCHEDULER...")
            logger.info(f"Current process ID: {os.getpid()}")
            logger.info(f"Current working directory: {os.getcwd()}")
            
            # API Sync Job - Every 2 hours
            next_api_sync = datetime.now()
            logger.info(f"Scheduling API sync job to run at: {next_api_sync}")
            
            self.scheduler.add_job(
                func=self._run_api_sync,
                trigger=IntervalTrigger(hours=2),
                id='api_sync_job',
                name='API Sync Job (Every 2 hours)',
                replace_existing=True,
                max_instances=1,  # Only one instance at a time
                next_run_time=next_api_sync  # Start immediately
            )
            logger.info("API sync job scheduled successfully")
            
            # SKU Analysis Job - Every 2 hours (offset by 30 minutes)  
            next_sku_analysis = datetime.now().replace(minute=30, second=0, microsecond=0)
            logger.info(f"Scheduling SKU analysis job to run at: {next_sku_analysis}")
            
            self.scheduler.add_job(
                func=self._run_sku_analysis,
                trigger=IntervalTrigger(hours=2, minutes=30),  # Offset by 30 minutes
                id='sku_analysis_job', 
                name='SKU Analysis Job (Every 2 hours + 30min offset)',
                replace_existing=True,
                max_instances=1,
                next_run_time=next_sku_analysis
            )
            logger.info("SKU analysis job scheduled successfully")
            
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
            logger.info("API Sync: Every 2 hours (starting now)")
            logger.info("SKU Analysis: Every 2 hours (starting in 30 minutes)")  
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
