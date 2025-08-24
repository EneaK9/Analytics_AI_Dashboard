#!/usr/bin/env python3
"""
Analytics Refresh Cron Job - AUTOMATED ENDPOINT TRIGGER
Automatically calls the inventory-analytics endpoint with force_refresh=true
The endpoint handles all cache removal and storage internally
Runs every 5 minutes to keep dashboard data fresh - FOR TESTING ONLY
"""

import asyncio
import logging
import sys
import os
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
# Optional dotenv import for local development
try:
    from dotenv import load_dotenv
    load_dotenv_available = True
except ImportError:
    load_dotenv_available = False

# Setup comprehensive logging with safe file handling
handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler, but don't fail if logs directory doesn't exist
try:
    os.makedirs('logs', exist_ok=True)
    handlers.append(logging.FileHandler('logs/analytics_refresh_cron.log', mode='a'))
except (OSError, PermissionError) as e:
    # Fall back to stdout-only logging in deployment environments
    print(f"Warning: Could not create analytics log file, using stdout only: {e}")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Load environment variables (optional for local development)
if load_dotenv_available:
    load_dotenv()

class AnalyticsRefreshCronJob:
    """Automated analytics refresh cron job - keeps dashboard data fresh"""
    
    def __init__(self):
        self.platforms = ["shopify", "amazon", "all"]
        self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = 300  # 5 minutes timeout
        logger.info("📊 Analytics Refresh Cron Job initialized - TESTING MODE (5 minutes)")
    
    def _get_admin_client(self):
        """Get Supabase admin client"""
        try:
            from database import get_admin_client
            return get_admin_client()
        except Exception as e:
            logger.error(f"Failed to get admin client: {e}")
            return None
    
    async def get_active_clients(self) -> List[str]:
        """Get all active clients that have API integrations"""
        try:
            db_client = self._get_admin_client()
            if not db_client:
                logger.error("❌ No database connection")
                return []
            
            # Get all clients with connected API credentials
            response = db_client.table("client_api_credentials").select(
                "client_id"
            ).eq("status", "connected").execute()
            
            if not response.data:
                logger.warning("⚠️ No active clients found")
                return []
            
            # Get unique client IDs
            client_ids = list(set([row['client_id'] for row in response.data]))
            logger.info(f"📋 Found {len(client_ids)} active clients for analytics refresh")
            
            return client_ids
            
        except Exception as e:
            logger.error(f"Failed to get active clients: {e}")
            return []
    
    async def generate_client_token(self, client_id: str) -> Optional[str]:
        """Generate a temporary token for API calls"""
        try:
            # Use the same token generation as the system
            from api_key_auth import create_token_for_client
            
            token_data = create_token_for_client(client_id)
            if token_data and token_data.get("access_token"):
                return token_data["access_token"]
            else:
                logger.error(f"Failed to generate token for client {client_id}")
                return None
                
        except Exception as e:
            logger.error(f"Token generation failed for {client_id}: {e}")
            return None
    
    async def refresh_analytics_for_client(self, client_id: str, platform: str) -> Dict[str, Any]:
        """Refresh analytics for a specific client and platform"""
        try:
            logger.info(f"🔄 Refreshing analytics for client {client_id} (platform: {platform})")
            
            # Generate token for this client
            token = await self.generate_client_token(client_id)
            if not token:
                return {"success": False, "error": "Failed to generate client token"}
            
            # Call the inventory-analytics endpoint with force_refresh
            url = f"{self.base_url}/api/dashboard/inventory-analytics"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {
                "platform": platform,
                "force_refresh": "true",  # Force fresh calculation
                "fast_mode": "true"       # Use optimized processing
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                logger.info(f"📡 Calling {url} for {client_id} ({platform})")
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify we got valid analytics data
                    if data.get("success") and data.get("inventory_analytics"):
                        analytics_data = data["inventory_analytics"]
                        
                        # NO ADDITIONAL CACHING - endpoint already handles cache removal and storage
                        
                        # Extract key metrics for logging
                        platforms_count = len(analytics_data.get("platforms", {}))
                        total_skus = len(analytics_data.get("sku_inventory", {}).get("skus", []))
                        
                        logger.info(f"✅ SUCCESS - {client_id} ({platform}): {platforms_count} platforms, {total_skus} SKUs - Endpoint handled caching")
                        
                        return {
                            "success": True,
                            "client_id": client_id,
                            "platform": platform,
                            "platforms_analyzed": platforms_count,
                            "skus_found": total_skus,
                            "endpoint_cached": True,  # Indicate endpoint did the caching
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        error_msg = data.get("error", "No analytics data returned")
                        logger.error(f"❌ Invalid response for {client_id} ({platform}): {error_msg}")
                        return {"success": False, "error": error_msg}
                
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"❌ API call failed for {client_id} ({platform}): {error_msg}")
                    return {"success": False, "error": error_msg}
                    
        except Exception as e:
            logger.error(f"❌ Error refreshing analytics for {client_id} ({platform}): {e}")
            return {"success": False, "error": str(e)}
    
    # REMOVED: cache_analytics_response() method - endpoint handles all caching
    
    async def run_full_analytics_refresh(self) -> Dict[str, Any]:
        """Run full analytics refresh for all active clients and platforms"""
        start_time = datetime.now()
        logger.info("🚀 Starting analytics refresh cron job - TESTING MODE (5 minutes)")
        
        results = {
            "success": True,
            "timestamp": start_time.isoformat(),
            "total_jobs": 0,
            "successful_refreshes": 0,
            "failed_refreshes": 0,
            "client_results": {},
            "duration_seconds": 0
        }
        
        try:
            # Get all active clients
            active_clients = await self.get_active_clients()
            
            if not active_clients:
                logger.info("ℹ️ No active clients found for analytics refresh")
                results["total_jobs"] = 0
                results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
                return results
            
            # Calculate total jobs (clients × platforms)
            results["total_jobs"] = len(active_clients) * len(self.platforms)
            logger.info(f"📋 Processing {len(active_clients)} clients × {len(self.platforms)} platforms = {results['total_jobs']} refresh jobs")
            
            # Process each client and platform combination
            for client_id in active_clients:
                client_results = {}
                
                for platform in self.platforms:
                    try:
                        result = await self.refresh_analytics_for_client(client_id, platform)
                        client_results[platform] = result
                        
                        if result.get("success"):
                            results["successful_refreshes"] += 1
                        else:
                            results["failed_refreshes"] += 1
                            logger.warning(f"⚠️ FAILED - {client_id} ({platform}): {result.get('error')}")
                            
                    except Exception as e:
                        logger.error(f"❌ Exception processing {client_id} ({platform}): {e}")
                        client_results[platform] = {"success": False, "error": str(e)}
                        results["failed_refreshes"] += 1
                
                results["client_results"][client_id] = client_results
            
            # Calculate final results
            duration = (datetime.now() - start_time).total_seconds()
            results["duration_seconds"] = duration
            
            logger.info(f"🏁 Analytics refresh cron job completed in {duration:.2f} seconds")
            logger.info(f"✅ Results: {results['successful_refreshes']} successful, {results['failed_refreshes']} failed out of {results['total_jobs']} total jobs")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Fatal error in analytics refresh cron job: {e}")
            results["success"] = False
            results["error"] = str(e)
            results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            return results

# Global instance
analytics_refresh_cron = AnalyticsRefreshCronJob()

if __name__ == "__main__":
    async def main():
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        logger.info("=" * 80)
        logger.info("STARTING ANALYTICS REFRESH CRON JOB - TESTING MODE (5 minutes)")
        logger.info("=" * 80)
        
        results = await analytics_refresh_cron.run_full_analytics_refresh()
        
        logger.info("=" * 80)
        logger.info("FINAL RESULTS:")
        logger.info(f"Successful refreshes: {results.get('successful_refreshes', 0)}")
        logger.info(f"Failed refreshes: {results.get('failed_refreshes', 0)}")
        logger.info(f"Duration: {results.get('duration_seconds', 0):.2f} seconds")
        logger.info("=" * 80)
    
    asyncio.run(main())
