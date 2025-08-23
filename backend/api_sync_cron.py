#!/usr/bin/env python3
"""
API Sync Cron Job - PERFECT VERSION
Automatically syncs new data from Shopify and Amazon APIs every 24 hours
Checks client_api_credentials table and syncs based on next_sync_at timestamps
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Setup comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/api_sync_cron.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class APISyncCronJob:
    """Perfect cron job that syncs new data from APIs every 24 hours"""
    
    def __init__(self):
        self.supported_platforms = ["shopify", "amazon", "woocommerce"]
        logger.info("API Sync Cron Job initialized - PERFECT VERSION")
    
    def _get_admin_client(self):
        """Get Supabase admin client"""
        try:
            from database import get_admin_client
            return get_admin_client()
        except Exception as e:
            logger.error(f"Failed to get admin client: {e}")
            return None
    
    async def get_clients_due_for_sync(self) -> List[Dict[str, Any]]:
        """Get all clients that are due for API sync"""
        try:
            db_client = self._get_admin_client()
            if not db_client:
                logger.error("❌ No database connection")
                return []
            
            current_time = datetime.now()
            current_time_iso = current_time.isoformat()
            
            logger.info(f"Checking for clients due for sync at {current_time_iso}")
            
            # Get all connected API credentials where next_sync_at <= current_time
            response = db_client.table("client_api_credentials").select(
                "credential_id, client_id, platform_type, connection_name, credentials, "
                "sync_frequency_hours, last_sync_at, next_sync_at, status"
            ).eq("status", "connected").lte("next_sync_at", current_time_iso).execute()
            
            clients_due = response.data if response.data else []
            
            logger.info(f"Found {len(clients_due)} API integrations due for sync:")
            for client in clients_due:
                logger.info(f"  - Client {client['client_id']} ({client['platform_type']}) - Last: {client.get('last_sync_at', 'Never')}")
            
            return clients_due
            
        except Exception as e:
            logger.error(f"Failed to get clients due for sync: {e}")
            return []
    
    async def sync_client_api_data(self, api_integration: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data for a single client API integration"""
        start_time = datetime.now()
        client_id = api_integration["client_id"]
        credential_id = api_integration["credential_id"]
        platform_type = api_integration["platform_type"]
        connection_name = api_integration["connection_name"]
        sync_frequency_hours = api_integration["sync_frequency_hours"]
        
        logger.info(f"Starting API sync for Client {client_id} ({platform_type} - {connection_name})")
        
        try:
            # Get credentials
            credentials = api_integration["credentials"]
            if isinstance(credentials, str):
                credentials = json.loads(credentials)
            
            logger.info(f"Connecting to {platform_type} API...")
            
            # Import API data fetcher
            from api_connectors import api_data_fetcher
            
            # Test connection first
            success, message = await api_data_fetcher.test_connection(platform_type, credentials)
            if not success:
                logger.error(f"API connection failed for {platform_type}: {message}")
                await self._update_sync_error(credential_id, f"Connection failed: {message}")
                return {"success": False, "error": message}
            
            logger.info(f"API connection successful for {platform_type}")
            
            # Fetch all data from API
            logger.info(f"Fetching new data from {platform_type} API...")
            all_data = await api_data_fetcher.fetch_all_data(platform_type, credentials)
            
            total_records = 0
            data_summary = {}
            
            # Process and store data
            for data_type, records in all_data.items():
                if not records:
                    logger.info(f"  - {data_type}: 0 records")
                    data_summary[data_type] = 0
                    continue
                
                logger.info(f"  - {data_type}: {len(records)} records fetched")
                
                # Prepare records for storage
                processed_records = []
                for record in records:
                    processed_record = {
                        "client_id": client_id,
                        "data": json.dumps(record) if isinstance(record, dict) else str(record),
                        "data_type": data_type,
                        "platform": platform_type,
                        "connection_name": connection_name,
                        "table_name": f"client_{client_id.replace('-', '_')}_data",
                        "created_at": datetime.now().isoformat()
                    }
                    processed_records.append(processed_record)
                
                # Store data with deduplication (same table names as always)
                if processed_records:
                    from database import get_db_manager
                    manager = get_db_manager()
                    
                    inserted_count = await manager.dedup_and_batch_insert_client_data(
                        f"client_{client_id.replace('-', '_')}_data",
                        processed_records,
                        client_id,
                        dedup_scope="day"
                    )
                    
                    total_records += inserted_count
                    data_summary[data_type] = inserted_count
                    
                    logger.info(f"Stored {inserted_count} new {data_type} records (after deduplication)")
            
            # Calculate next sync time
            next_sync = datetime.now() + timedelta(hours=sync_frequency_hours)
            
            # Update sync status
            db_client = self._get_admin_client()
            db_client.table("client_api_credentials").update({
                "status": "connected",
                "last_sync_at": datetime.now().isoformat(),
                "next_sync_at": next_sync.isoformat(),
                "error_message": None
            }).eq("credential_id", credential_id).execute()
            
            # Calculate sync duration
            sync_duration = (datetime.now() - start_time).total_seconds()
            
            # Try to log sync result (but don't fail the entire sync if logging fails)
            try:
                db_client.table("client_api_sync_results").insert({
                    "client_id": client_id,
                    "credential_id": credential_id,
                    "platform_type": platform_type,
                    "connection_name": connection_name,
                    "records_fetched": sum(len(records) for records in all_data.values()),
                    "records_processed": total_records,
                    "records_stored": total_records,
                    "sync_duration_seconds": sync_duration,
                    "success": True,
                    "data_types_synced": list(all_data.keys())
                }).execute()
            except Exception as log_error:
                logger.warning(f"Failed to log sync result (but data sync was successful): {log_error}")
            
            logger.info(f"API sync completed for Client {client_id} ({platform_type})")
            logger.info(f"Summary: {total_records} new records stored in {sync_duration:.2f}s")
            logger.info(f"Next sync scheduled for: {next_sync.isoformat()}")
            
            # Trigger dashboard recalculations if new data was synced
            if total_records > 0:
                logger.info(f"New data synced - triggering dashboard recalculations for client {client_id}")
                try:
                    # Trigger SKU cache refresh for this client and platform
                    from sku_analysis_cron import SKUAnalysisCronJob
                    sku_job = SKUAnalysisCronJob()
                    
                    # Refresh SKU cache for this specific client and platform
                    sku_result = await sku_job.refresh_client_sku_analysis(client_id, platform_type)
                    if sku_result.get("success"):
                        logger.info(f"SKU analysis updated after sync: {sku_result.get('skus_cached', 0)} SKUs cached")
                    else:
                        logger.warning(f"SKU analysis failed after sync: {sku_result.get('error')}")
                        
                    # Clear LLM cache to force dashboard regeneration
                    from llm_cache_manager import LLMCacheManager
                    cache_manager = LLMCacheManager()
                    await cache_manager.invalidate_cache(client_id)
                    logger.info(f"LLM cache invalidated - dashboard will regenerate with new data")
                    
                except Exception as calc_error:
                    logger.warning(f"Dashboard recalculation failed (but sync was successful): {calc_error}")
            else:
                logger.info(f"No new data synced - skipping dashboard recalculations")
            
            # Return success=True because data was stored successfully (logging errors don't matter)
            return {
                "success": True,
                "client_id": client_id,
                "platform_type": platform_type,
                "total_records_stored": total_records,
                "data_summary": data_summary,
                "sync_duration_seconds": sync_duration,
                "next_sync_at": next_sync.isoformat(),
                "data_stored_successfully": True,
                "dashboard_updated": total_records > 0
            }
            
        except Exception as e:
            logger.error(f"API sync failed for Client {client_id} ({platform_type}): {e}")
            await self._update_sync_error(credential_id, str(e))
            return {"success": False, "error": str(e), "client_id": client_id, "platform_type": platform_type}
    
    async def _update_sync_error(self, credential_id: str, error_message: str):
        """Update credential status to error"""
        try:
            db_client = self._get_admin_client()
            if db_client:
                # Schedule retry in 1 hour
                next_sync = datetime.now() + timedelta(hours=1)
                
                db_client.table("client_api_credentials").update({
                    "status": "error",
                    "error_message": error_message,
                    "next_sync_at": next_sync.isoformat()
                }).eq("credential_id", credential_id).execute()
                
                logger.info(f"Scheduled retry in 1 hour for credential {credential_id}")
        except Exception as e:
            logger.error(f"Failed to update sync error: {e}")
    
    async def run_full_sync(self) -> Dict[str, Any]:
        """Run full API sync for all clients due for sync"""
        start_time = datetime.now()
        logger.info("Starting full API sync cron job - PERFECT VERSION")
        
        results = {
            "success": True,
            "timestamp": start_time.isoformat(),
            "total_integrations": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "total_records_synced": 0,
            "client_results": {},
            "duration_seconds": 0
        }
        
        try:
            # Get all clients due for sync
            clients_due = await self.get_clients_due_for_sync()
            
            if not clients_due:
                logger.info("No API integrations due for sync at this time")
                results["total_integrations"] = 0
                results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
                return results
            
            results["total_integrations"] = len(clients_due)
            logger.info(f"Processing {len(clients_due)} API integrations...")
            
            # Process each client API integration
            for api_integration in clients_due:
                try:
                    sync_result = await self.sync_client_api_data(api_integration)
                    
                    client_id = api_integration["client_id"]
                    platform_type = api_integration["platform_type"]
                    key = f"{client_id}_{platform_type}"
                    
                    results["client_results"][key] = sync_result
                    
                    if sync_result.get("success"):
                        results["successful_syncs"] += 1
                        results["total_records_synced"] += sync_result.get("total_records_stored", 0)
                        logger.info(f"SUCCESS - {key}: {sync_result.get('total_records_stored', 0)} records")
                    else:
                        results["failed_syncs"] += 1
                        logger.error(f"FAILED - {key}: {sync_result.get('error')}")
                        
                except Exception as e:
                    results["failed_syncs"] += 1
                    client_key = f"{api_integration['client_id']}_{api_integration['platform_type']}"
                    results["client_results"][client_key] = {"success": False, "error": str(e)}
                    logger.error(f"Exception processing {client_key}: {e}")
            
            # Calculate final results
            duration = (datetime.now() - start_time).total_seconds()
            results["duration_seconds"] = duration
            
            logger.info(f"API sync cron job completed in {duration:.2f} seconds")
            logger.info(f"Results: {results['successful_syncs']} successful, {results['failed_syncs']} failed")
            logger.info(f"Total new records synced: {results['total_records_synced']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Fatal error in API sync cron job: {e}")
            results["success"] = False
            results["error"] = str(e)
            results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            return results

# Global instance
api_sync_cron = APISyncCronJob()

if __name__ == "__main__":
    async def main():
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        logger.info("=" * 80)
        logger.info("STARTING API SYNC CRON JOB - PERFECT VERSION")
        logger.info("=" * 80)
        
        results = await api_sync_cron.run_full_sync()
        
        logger.info("=" * 80)
        logger.info("FINAL RESULTS:")
        logger.info(f"Successful syncs: {results.get('successful_syncs', 0)}")
        logger.info(f"Failed syncs: {results.get('failed_syncs', 0)}")
        logger.info(f"Total records synced: {results.get('total_records_synced', 0)}")
        logger.info(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        logger.info("=" * 80)
    
    asyncio.run(main())
